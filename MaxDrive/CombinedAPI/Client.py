import os
import sys
import httplib2
import pickle
import base64
import mimetypes
import hashlib
import tempfile
from django.utils.timezone import utc
from django.core.management import setup_environ
from MaxDrive import settings
setup_environ(settings)
from hurry.filesize import size, si
from datetime import datetime
from apiclient import errors
from apiclient.http import MediaIoBaseUpload
from apiclient.discovery import build
from dropbox import client, rest, session
from oauth2client.django_orm import Storage
from oauth2client.client import OAuth2WebServerFlow
from MaxDrive_User.models import DriveCredentials
from MaxDrive_FS.models import Node, Drive_Data, Source_List, MaxDrive_Data, MaxDrive_Piece
from MaxDrive_FS import tasks
from MaxDrive_FS.tasks import dropbox_upload_async, maxdrive_uploader

class CombinedClient(object):
	def __init__(self, init, user=None):
		self.md_user = user

		if init in ['login', 'testing']:
			self.db_client    = self.get_dropbox_client()
			self.gd_client    = self.get_drive_client()
			self.drive_root   = self.get_drive_root()
			self.drive_shared = self.get_drive_share()
		elif init in ['register']:
			self.register_service_roots()

	###########################################################################
	## On pickling to session need to remove Drive client                    ##
	###########################################################################
	def __getstate__(self):
		obdict = self.__dict__.copy()
		del obdict['gd_client']
		return obdict

	###########################################################################
	## One unpicling need to rebuild Drive client                            ##
	###########################################################################
	def __setstate__(self, dict):
		self.__dict__ = dict
		self.gd_client = self.get_drive_client()

	###########################################################################
	## Reauthorize the Dropbox client                                        ##
	###########################################################################
	def get_dropbox_client(self):
		sess = session.DropboxSession(self.md_user.dropbox_creds.api_key,
		                              self.md_user.dropbox_creds.api_secret,
		                              self.md_user.dropbox_creds.api_access)
		sess.set_token(self.md_user.dropbox_creds.token_key, 
			           self.md_user.dropbox_creds.token_secret)

		return client.DropboxClient(sess)

	###########################################################################
	## Reauthorize the Drive client from the Django DB                       ##
	###########################################################################
	def get_drive_client(self):
		credentials = Storage(DriveCredentials, 'id', self.md_user, 'credential').get()
		http        = credentials.authorize(http=httplib2.Http())
		
		return build('drive', 'v2', http=http)

	###########################################################################
	## Get the 'MaxDrive' sub folder ID in a users Drive account             ##
	###########################################################################
	def get_drive_root(self):
		for root_file in self.gd_client.children().list(folderId='root').execute()['items']:
			f = self.gd_client.files().get(fileId=root_file['id']).execute()
			if f['title'] == 'Apps':
				for app in self.gd_client.children().list(folderId=f['id']).execute()['items']:
					f = self.gd_client.files().get(fileId=app['id']).execute()
					if f['title'] == 'MaxDrive':
						return f['id']
					else:
						continue
			else:
				continue

	###########################################################################
	## Get the ID of the sub folder for split files in Drive                 ##
	###########################################################################
	def get_drive_share(self):
		for f in self.list_drive(self.drive_root):
			if f['title'] == '.sharedDrive':
				return f['file_id']
			else:
				continue

	###########################################################################
	## Setup Drive and Dropbox folders if a new user                         ##
	###########################################################################
	def register_service_roots(self):
		response = {}

		apps = False
		for root_file in self.list_drive('root'):
			if root_file['title'] == 'Apps':
				apps = True
		if not apps:
			body = {'title'    : 'Apps',
				    'parents'  : [{'id':'root'}],
				    'mimeType' : 'application/vnd.google-apps.folder'}

			data = self.gd_client.files().insert(body=body).execute()

			body = {'title'    : 'MaxDrive',
				    'parents'  : [{'id':data['id']}],
				    'mimeType' : 'application/vnd.google-apps.folder'}

			self.drive_root = self.gd_client.files().insert(body=body).execute()['id']

			body = {'title'    : '.shared',
				    'parents'  : [{'id':self.drive_root}],
				    'mimeType' : 'application/vnd.google-apps.folder'}

			self.gd_client.files().insert(body=body).execute()
		
		drive_root   = self.drive_to_maxdrive(self.gd_client.files().get(fileId=self.drive_root).execute())
		dropbox_root = self.db_client.metadata('/', list=False)
		dropbox_root.pop('path')
		dropbox_root[u'path']='/Apps/MaxDrive'
		dropbox_root = self.dropbox_to_maxdrive(dropbox_root)

		response['status'] = 200
		response['roots']  = [drive_root, dropbox_root]

		return response

	###########################################################################
	## Stat_FS like call, list disk space etc.                               ##
	###########################################################################
	def about(self):
		db_data = self.db_client.account_info()
		gd_data = self.gd_client.about().get().execute()

		md_quota     = long(db_data['quota_info']['quota'])  + long(gd_data['quotaBytesTotal'])
		md_quotaUsed = long(db_data['quota_info']['normal']) + long(gd_data['quotaBytesUsed'])
		md_quotaFree = md_quota - md_quotaUsed

		db_quota     = db_data['quota_info']['quota']
		db_quotaUsed = db_data['quota_info']['normal']
		db_quotaFree = db_quota - db_quotaUsed

		gd_quota     = long(gd_data['quotaBytesTotal'])
		gd_quotaUsed = long(gd_data['quotaBytesUsed'])
		gd_quotaFree = gd_quota - gd_quotaUsed


		md_about = {'md_quota'     : size(md_quota, system=si),
		            'md_quotaUsed' : size(md_quotaUsed, system=si),
		            'md_quotaFree' : size(md_quotaFree, system=si),
		            'db_quota'     : size(db_quota, system=si),
		            'db_quotaUsed' : size(db_quotaUsed, system=si),
		            'db_quotaFree' : size(db_quotaFree, system=si),
		            'gd_quota'     : size(gd_quota, system=si),
		            'gd_quotaUsed' : size(gd_quotaUsed, system=si),
		            'gd_quotaFree' : size(gd_quotaFree, system=si),}

		return md_about

	###########################################################################
	## ls like call, list dir contents. Delegated to funcs: list_drive and   ##
	## list_dropbox                                                          ##
	###########################################################################
	def metadata(self, node):
		if node == '/':
			return self.list_dropbox('/') + self.list_drive(self.drive_root)
		elif node.source.short == 'drive':
			return self.list_drive(node)
		elif node.source.short == 'dropbox':
			return self.list_dropbox(node)

	def list_drive(self, node):
		contents = []

		if isinstance(node, str) or isinstance(node, unicode):
			pass
		else:
			node = node.drive_file.file_id

		drive_items = self.gd_client.children().list(folderId=node).execute()['items']
		for item in drive_items:
			_file = self.gd_client.files().get(fileId=item['id']).execute()
			if 'explicitlyTrashed' in _file and _file['explicitlyTrashed'] == True:
				continue
			else:
				gd_file = {}

				head, tail = os.path.split(self.google_id_to_path(item['id']))
				if head == '/':
					pass
				else:
					head = head + '/'

				#Generic node attributes
				gd_file['title']    = tail
				gd_file['parent']   = head
				gd_file['source']   = 'drive'
				gd_file['is_dir']   = (lambda x: True if x['mimeType'] == 'application/vnd.google-apps.folder' and 'fileExtension' not in x else False)(_file)
				gd_file['st_size']  = (lambda x: 0 if x == True else _file['fileSize'])(gd_file['is_dir'])
				gd_file['st_mtime'] = (lambda x: None if x is None else datetime_normalization(x, 'drive'))(_file['modifiedDate'])

				#Drive specific attributes
				gd_file['file_id']        = _file['id']
				gd_file['webContentLink'] = (lambda x: None if 'webContentLink' not in x else x['webContentLink'])(_file)
				gd_file['webViewLink']    = (lambda x: None if 'webViewLink' not in x else x['webViewLink'])(_file)
				gd_file['alternateLink']  = (lambda x: None if 'alternateLink' not in x else x['alternateLink'])(_file)
				gd_file['iconLink']       = (lambda x: None if 'iconLink' not in x else x['iconLink'])(_file)
				gd_file['thumbnailLink']  = (lambda x: None if 'thumbnailLink' not in x else x['thumbnailLink'])(_file)

				contents.append(gd_file)

		return contents

	def list_dropbox(self, node):
		contents = []

		if node == '/':
			pass
		else:
			node = node.path_name

		dropbox_items = self.db_client.metadata(node)['contents']
		for item in dropbox_items:
			db_file = {}

			head, tail = os.path.split(item['path'])
			if head == '/':
				pass
			else:
				head = head + '/'

			db_file['title']    = tail
			db_file['parent']   = head
			db_file['st_size']  = item['bytes']
			db_file['st_mtime'] = (lambda x: None if 'modified' not in x else datetime_normalization(x['modified'], 'dropbox'))(item)
			db_file['is_dir']   = item['is_dir']
			db_file['source']   = 'dropbox'

			contents.append(db_file)

		return contents

	###########################################################################
	## Make a new dir given the parent node, a title and a destination       ##
	###########################################################################
	def mkdir(self, node, title, dest):
		response = {}

		if dest == 'dropbox':
			try:
				data             = self.db_client.file_create_folder('/'+title)
				response['data'] = self.dropbox_to_maxdrive(data)
			except rest.ErrorResponse as e:
				response['status']  = e.status
				response['message'] = e.reason

				return response

		elif dest == 'drive':
			try:
				body = {'title'    : title,
				        'parents'  : [{'id':(lambda x: self.drive_root if x=='/' else node.drive_file.file_id)(node.path_name)}],
				        'mimeType' : 'application/vnd.google-apps.folder'}
				data = self.gd_client.files().insert(body=body).execute()
				response['data'] = self.drive_to_maxdrive(data)
			except errors.HttpError as e:
					response['status']  = e.uri
					response['message'] = e._get_reason()

					return response

		response['status']  = 200
		response['message'] = title + ' created'

		return response

		"""
		if dest:
			if dest == 'dropbox':
				try:
					data             = self.db_client.file_create_folder('/'+title)
					response['data'] = self.dropbox_to_maxdrive(data)
				except rest.ErrorResponse as e:
					response['status']  = e.status
					response['message'] = e.reason

					return response

			elif dest == 'drive':
				try:
					body = {'title'    : title,
					        'parents'  : [{'id':self.drive_root}],
					        'mimeType' : 'application/vnd.google-apps.folder'}

					data = self.gd_client.files().insert(body=body).execute()
					response['data'] = self.drive_to_maxdrive(data)
				except errors.HttpError as e:
					response['status']  = e.uri
					response['message'] = e._get_reason()

					return response

			elif dest == 'maxdrive':
				data = {}
				data['title']    = title
				data['parent']   = node.path_name
				data['st_size']  = 0
				data['st_mtime'] = datetime.utcnow().replace(tzinfo=utc)
				data['is_dir']   = 1
				data['source']   = 'maxdrive'

				response['data'] = data
			
			response['status']  = 200

			return response

		else:
			if node.source.short == 'dropbox':
				try:
					data             = self.db_client.file_create_folder(node.path_name+title)
					response['data'] = self.dropbox_to_maxdrive(node.path_name+title)
				except rest.ErrorResponse as e:
					response['status']  = e.status
					response['message'] = e.reason

					return response

			elif node.source.short == 'drive':
				try:
					body = {'title'    : title,
					        'parents'  : [{'id':node.drive_file.file_id}],
					        'mimeType' : 'application/vnd.google-apps.folder'}

					data = self.gd_client.files().insert(body=body).execute()
					response['data'] = self.drive_to_maxdrive(data)
				except errors.HttpError as e:
					response['status']  = e.uri
					response['message'] = e._get_reason() 
					
					return response

			elif node.source.short == 'maxdrive':
				


				
				response['status']  = 200
				response['data']    = title

				return response

			response['status']  = 200
			response['message'] = 'Success! '+title+' created.'

			return response
		"""

	###########################################################################
	## Delete files related to node (Django node deleted in view)            ##
	###########################################################################
	def delete(self, node):
		response = {}

		if node.source.short == 'dropbox':
			try:
				self.db_client.file_delete(node.path_name)
			except rest.ErrorResponse as e:
				response['status']  = e.status
				response['message'] = e.reason

				return response

		elif node.source.short == 'drive':
			try:
				self.gd_client.files().delete(fileId=node.drive_file.file_id).execute()
				node.drive_file.delete()
			except errors.HttpError as e:
				response['status']  = e.uri
				response['message'] = e._get_reason() 
				
				return response

		#In the case of a MaxDrive node, iterate over pieces in shared folder deleting.
		elif node.source.short == 'maxdrive':
			for piece in MaxDrive_Piece.objects.filter(md_data=node.maxdrive_file):
				if piece.source.short == 'dropbox':
					self.db_client.file_delete(piece.path)
				elif piece.source.short == 'drive':
					self.gd_client.files().delete(fileId=piece.path).execute()

			MaxDrive_Piece.objects.filter(md_data=node.maxdrive_file).delete()
			node.maxdrive_file.delete()

		response['status']  = 200
		response['message'] = node.title+' deleted.'

		return response

	###########################################################################
	## Given a node, determine destination and return link or rebuild file   ##
	###########################################################################
	def download_link(self, node, md_user):
		response = {}

		if node.source.short == 'dropbox':
			try:
				media = self.db_client.media(node.path_name)
			except rest.ErrorResponse as e:
				response['status']  = e.status
				response['message'] = e.reason

				return response

			response['status']  = 200
			response['message'] = 'Success! '+node.title+' link got.'
			response['url']     = media['url']
			response['data']    = 'Expires: '+media['expires']

		elif node.source.short == 'drive':
			try:
				media = self.gd_client.files().get(fileId=node.drive_file.file_id).execute()
			except errors.HttpError as e:
				response['status']  = e.uri
				response['message'] = e._get_reason() 

				return response
				
			response['status']  = 200
			response['message'] = 'Success! '+node.title+' link got.'
			response['url']     = media.get('downloadUrl')
			response['data']    = 'View in Drive: ', media.get('webContentLink')

		elif node.source.short == 'maxdrive':
			pieces = MaxDrive_Piece.objects.filter(md_data=node.maxdrive_file)

			file_string = ''
			for piece in MaxDrive_Piece.objects.filter(md_data=node.maxdrive_file):
				if piece.source.short == 'dropbox':
					f = self.db_client.get_file_and_metadata(piece.path)[0]
					file_string += f.read()
				elif piece.source.short == 'drive':
					g_file = self.gd_client.files().get(fileId=piece.path).execute()
					content = self.gd_client._http.request(g_file['downloadUrl'])[1]
					file_string += content

			user_media_path = settings.MEDIA_ROOT+'/'+md_user.user.username

			if not os.path.exists(user_media_path):
				os.mkdir(user_media_path)

			with open(user_media_path+'/'+node.title, 'w') as _file:
				_file.write(pickle.loads(base64.decodestring(file_string)))

			hashIn  = node.maxdrive_file._hash
			hashOut = hashlib.sha224(open(_file.name, 'r').read()).hexdigest()

			if hashIn == hashOut:
				response['status']  = 201
				response['message'] = 'Success! '+node.title+' link got.'
				response['url']     = md_user.user.username+'/'+node.title
				response['data']    = 'Hash Out: '+hashOut

			else:
				response['status']  = 400
				response['message'] = 'Incorrect hashes'

		return response

	###########################################################################
	## Get the revision history of a file                                    ##
	###########################################################################
	def revisions(self, node):
		response = {}

		if node.source.short == 'dropbox':
			try:
				revisions = self.db_client.revisions(node.path_name)
			except rest.ErrorResponse as e:
				response['status']  = e.status
				response['message'] = e.reason

				return response

			response['status']    = 200
			response['message']   = 'Success! '+node.title+' revisions got.'
			response['revisions'] = revisions

			return response

		elif node.source.short == 'drive':
			try:
				revisions = self.gd_client.revisions().list(fileId=node.drive_file.file_id).execute()
			except errors.HttpError as e:
				print e
				response['status']  = e.uri
				response['message'] = e._get_reason() 

				return response
				
			response['status']    = 200
			response['message']   = 'Success! '+node.title+' revisions got.'
			response['revisions'] = revisions['items']

			return response

	###########################################################################
	## Determine destination of file and delegate to maxdrive, dropbox or    ##
	## drive funcs                                                           ##
	###########################################################################
	def upload(self, node, UploadedFile, md_user, destination):
		response = {}

		if destination == 'dropbox':
			try:
				data = self.dropbox_uploader(node, UploadedFile)
				response['accessed'] = data['accessed']
				response['data']     = self.dropbox_to_maxdrive(data['data'])
			except rest.ErrorResponse as e:
				response['status']  = e.status
				response['message'] = e.reason

				return response

		elif destination == 'drive':
			try:
				data = self.drive_uploader(node, UploadedFile)
				response['accessed'] = data['accessed']
				response['data']     = self.drive_to_maxdrive(data['data'])
			except errors.HttpError as e:
				response['status']  = e.uri
				response['message'] = e._get_reason() 

				return response

		elif destination == 'maxdrive':
			response = self.maxdrive_uploader(node, UploadedFile, md_user)

			return response

		response['status']  = 200
		response['message'] = UploadedFile.name + ' created!'

		return response
	
	def drive_uploader(self, node, f):
		response   = {}
		media_body = MediaIoBaseUpload(f.file, mimetypes.guess_type(f.name)[0])
		body       = {'title': f.name, 
		              'parents': [{'id':(lambda x: self.drive_root if x=='/' else node.drive_file.file_id)(node.path_name)}],}

		response['data']     = self.gd_client.files().insert(body=body , media_body=media_body).execute()
		response['accessed'] = True

		return response

	#Convert to string, split and upload immediately or pass to Celery
	def maxdrive_uploader(self, node, f, md_user):
		response = {}

		standard       = ''
		for chunk in f.chunks():
			standard += chunk

		item             = {}
		item['pieces']   = []
		item['hash']     = hashlib.sha224(standard).hexdigest()
		item['st_size']  = f.size
		item['title']    = f.name
		item['parent']   = node.path_name
		item['source']   = 'maxdrive'
		item['st_mtime'] = datetime.utcnow().replace(tzinfo=utc)
		item['is_dir']   = False
		file_string      = base64.encodestring(pickle.dumps(standard, -1))
		file_chunks      = list(file_string)
		chunks           = [file_chunks[x:x+524288] for x in xrange(0, len(file_chunks), 524288)]
		no_chunks        = len(chunks)
		item['len']      = no_chunks

		if no_chunks == 1:
			db_title    = tasks.check_db_title(node.path_name, item['title'])
			data        = ''.join(chunks[0])

			self.db_client.put_file(db_title+'0', data)

			item['pieces']       = [{'order': 0, 'path': db_title+'0', 'source': 'dropbox'}]
			response['status']   = 200
			response['message']  = item['title'] + ' created!'
			response['data']     = item
			response['accessed'] = False

			return response

		else:
			maxdrive_uploader.delay(self.db_client, self.drive_shared, chunks, no_chunks, item, node, md_user)

			response['status']   = 201
			response['message']  = 'Celeried - not yet accessible'
			response['data']     = item
			response['accessed'] = True

			return response

		return item
	
	def dropbox_uploader(self, node, f):
		response = {}
		if f.multiple_chunks():
			dropbox_upload_async_test.delay(self.db_client, node.path_name, f.temporary_file_path(), f.size, f.name)

			item             = {}
			item['st_size']  = f.size
			item['title']    = f.name
			item['parent']   = node.path_name
			item['source']   = 'dropbox'
			item['st_mtime'] = datetime.utcnow().replace(tzinfo=utc)
			item['is_dir']   = False

			response['status']   = 201
			response['message']  = 'Celeried - not yet accessible'
			response['data']     = item
			response['accessed'] = False

		else:
			response['data']     = self.db_client.put_file(node.path_name+'/'+f.name, f.read())
			response['status']   = 200
			response['message']  = f.name + ' created!'
			response['accessed'] = True

		return response

	###########################################################################
	## Convert source file metadata to MaxDrive format                       ##
	###########################################################################
	def dropbox_to_maxdrive(self, item):
		db_file = {}

		head, tail = os.path.split(item['path'])
		if head == '/':
			pass
		else:
			head = head + '/'

		db_file['title']    = tail
		db_file['parent']   = head
		db_file['st_size']  = item['bytes']
		db_file['st_mtime'] = (lambda x: None if 'modified' not in x else datetime_normalization(x['modified'], 'dropbox'))(item)
		db_file['is_dir']   = item['is_dir']
		db_file['source']   = 'dropbox'

		return db_file

	def drive_to_maxdrive(self, item):
		gd_file = {}

		head, tail = os.path.split(self.google_id_to_path(item['id']))
		if head == '/':
			pass
		else:
			head = head + '/'

		#Generic node attributes
		gd_file['title']    = tail
		gd_file['parent']   = head
		gd_file['source']   = 'drive'
		gd_file['is_dir']   = (lambda x: True if x['mimeType'] == 'application/vnd.google-apps.folder' and 'fileExtension' not in x else False)(item)
		gd_file['st_size']  = (lambda x: 0 if x == True else item['fileSize'])(gd_file['is_dir'])
		gd_file['st_mtime'] = (lambda x: None if x is None else datetime_normalization(x, 'drive'))(item['modifiedDate'])

		#Drive specific attributes
		gd_file['file_id']        = item['id']
		gd_file['webContentLink'] = (lambda x: None if 'webContentLink' not in x else x['webContentLink'])(item)
		gd_file['webViewLink']    = (lambda x: None if 'webViewLink' not in x else x['webViewLink'])(item)
		gd_file['alternateLink']  = (lambda x: None if 'alternateLink' not in x else x['alternateLink'])(item)
		gd_file['iconLink']       = (lambda x: None if 'iconLink' not in x else x['iconLink'])(item)
		gd_file['thumbnailLink']  = (lambda x: None if 'thumbnailLink' not in x else x['thumbnailLink'])(item)

		return gd_file

	###########################################################################
	## Return a standard file path (rooted at MaxDrive) from a drive ID      ##
	###########################################################################
	def google_id_to_path(self, drive_id):
		parts = []

		is_root = False
		while is_root == False:
			_file = self.gd_client.files().get(fileId=drive_id).execute()
			if len(_file['parents']) == 0 or _file['parents'][0]['id'] == self.drive_root:
				parts.append(_file['title'])
				is_root = True
			else:
				parts.append(_file['title'])
				drive_id = _file['parents'][0]['id']
		parts.reverse()

		path = '/'
		for part in parts:
			path = path + part + '/'

		return path[:-1] 

###########################################################################
## Change Dropbox and Drive metadata to a Postgres form, not cool        ##
###########################################################################
def datetime_normalization(input_time, source):
	if not input_time:
		return None
	else:
		if source == 'drive':
			format = '%Y-%m-%dT%H:%M:%S.%fZ'
		elif source == 'dropbox':
			format = '%a, %d %b %Y %H:%M:%S +%f'

		return datetime.strptime(input_time, format).strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
	from django.core.management import setup_environ
	from MaxDrive import settings
	setup_environ(settings)
	from MaxDrive_User.models import MaxDrive_User, DropboxCredentials, DriveCredentials
	from MaxDrive_FS.models import Node, Drive_Data, Dropbox_Data, Source_List
	from django.contrib.auth.models import User
	from oauth2client.django_orm import Storage

	if len(MaxDrive_User.objects.all()) is 0:
		#Authorize google client
		c_id     = '67639165534-iat1fois0eu3u0uq7cfn3fano7nemetq.apps.googleusercontent.com'
		c_secret = 'fCI3SAnwZS8NuJA78uQWDY0k'
		o_scope  = 'https://www.googleapis.com/auth/drive'
		r_URI    = 'urn:ietf:wg:oauth:2.0:oob'

		flow = OAuth2WebServerFlow(c_id, c_secret, o_scope, r_URI)
		print flow.step1_get_authorize_url()
		code = raw_input('Enter verification code: ').strip()
		credentials = flow.step2_exchange(code)

		http = httplib2.Http()
		http = credentials.authorize(http)
  		#Authorize dropbox client
		key    = 'dwbwzy1tfi5e97b'
		secret = 'kdnjvjp62bkb1f2'
		access = 'app_folder'

		sess          = session.DropboxSession(key, secret, access)
		request_token = sess.obtain_request_token()

		print sess.build_authorize_url(request_token)
		raw_input()
		access_token = sess.obtain_access_token(request_token)

		#Save client with api input and dropbox k, s
		u = User.objects.get(username='maxwell')

		d = DropboxCredentials(api_key=key,
  		                       api_secret=secret,
  		                       api_access=access,
  		                       token_key=access_token.key,
  		                       token_secret=access_token.secret)
		d.save()

		m = MaxDrive_User(user=u,
			              dropbox_creds=d)
		m.save()

		s = Storage(DriveCredentials, 'id', m, 'credential')
  		s.put(credentials)	

  		g = DriveCredentials.objects.get(id=m)
  		g.api_id = c_id
  		g.api_secret = c_secret
  		g.api_scope = o_scope
		g.api_uri = r_URI
		g.save()

		m.drive_creds = g
		m.save()

	elif len(Node.objects.all()) is 0:
		m = MaxDrive_User.objects.get(user=User.objects.get(username='maxwell'))
		try:
			r = Node.add_root(user=m,
				              path_name='/',
				              st_size=0,
				              source=Source_List.objects.get(name='MaxDrive'),
				              accessed=True,
				              title='/',
				              st_mtime=datetime.utcnow().replace(tzinfo=utc),
				              st_uid=m.user.username,
				              is_dir=True)
			r.save()

			c = Client('rebuild_login', m)
			c.register_populate_root(r)

		except Exception as e:
			print e



