import os
import time
import tempfile
import httplib2
import mimetypes
from django.core.files.uploadedfile import UploadedFile
from django.utils.timezone import utc
from django.http import HttpResponse
from MaxDrive_User.models import MaxDrive_User, DriveCredentials
from MaxDrive_FS.models import Node, MaxDrive_Piece, Source_List
from MaxDrive_FS.views import node_create
from apiclient.http import MediaIoBaseUpload
from apiclient import errors
from datetime import datetime
from apiclient.discovery import build
from oauth2client.django_orm import Storage
from celery import task
from dropbox import rest

###########################################################################
## Functions that hand over to a Celery worker                           ##
###########################################################################

#Dropbox uploader: upload chunks and mark as accessed
@task()
def dropbox_upload_async(db_client, path, temp_path, size, name):
	f = open(temp_path)
	
	uploader = db_client.get_chunked_uploader(f, size)
	while uploader.offset < size:
		try:
			upload = uploader.upload_chunked()
		except rest.ErrorResponse, e:
			return {'message' : 'error'}

	uploader.finish(path+'/'+name)

	node = Node.objects.get(user=md_user, path_name=(lambda x: x['parent']+x['title'] if x['parent'] == '/' else x['parent']+'/'+x['title'])(item))
	node.accessed = True
	node.save()

#Upload first half of chunks to Dropbox and second to Drive, create MaxDrive pieces and mark as accessed
@task()
def maxdrive_uploader(db_client, gd_share, chunks, no_chunks, item, node, md_user):
	index       = 0
	gd_client   = google_get_client(md_user) 
	db_title    = check_db_title(node.path_name, item['title'])
	gd_title    = check_gd_title(node.path_name, item['title'])

	#Upload first half of chunks to dropbox
	for chunk in chunks[:no_chunks/2]:
		data = ''.join(chunk)
		db_client.put_file(db_title+str(index), data)

		item['pieces'].append({'order': index, 'path': db_title+str(index), 'source': 'dropbox'})

		index+=1

	#Upload second half of chunks to drive
	for chunk in chunks[no_chunks/2:]:
		data       = ''.join(chunk)
		temp       = tempfile.NamedTemporaryFile()
		temp.write(data)
		media_body = MediaIoBaseUpload(temp, mimetypes.guess_type(item['title'])[0])
		body       = {'title'  : gd_title+str(index), 
                      'parents': [{'id':gd_share}],}

		try:
			upload = gd_client.files().insert(body=body , media_body=media_body).execute()
		except errors.HttpError as e:

		item['pieces'].append({'order': index, 'path': upload['id'], 'source': 'drive'})

		index+=1

	node = Node.objects.get(user=md_user, path_name=(lambda x: x['parent']+x['title'] if x['parent'] == '/' else x['parent']+'/'+x['title'])(item))
	for piece in item['pieces']:
		mp = MaxDrive_Piece(order=piece['order'], 
			                path=piece['path'],
			                source=Source_List.objects.get(short=piece['source']),
			                md_data=node.maxdrive_file)		
		mp.save()
	node.accessed = True
	node.save()

#Create nodes of both root folders
@task()
def register_root(items_to_add):
	try:
		reserved = ['.shared']
		for item in items_to_add:
			if item['title'] in reserved:
				continue

			node = Node.objects.get(user=md_user, path_name=item['parent'])

			if item['source'] == 'drive':
				gd = Drive_Data(file_id=item['file_id'],
			           webContentLink=item['webContentLink'],
			           webViewLink=item['webViewLink'],
			           alternateLink=item['alternateLink'],
			           iconLink=item['iconLink'],
			           thumbnailLink=item['thumbnailLink'])
				gd.save()

				node.add_child(user=md_user,
					           path_name=item['parent']+item['title'],
					           source=source_check(item['source']),
					           accessed=False,
					           title=item['title'],
					           st_mtime=item['st_mtime'],
					           st_size=item['st_size'],
					           st_uid=md_user.user.username,
					           is_dir=item['is_dir'],
					           drive_file=gd)
			else:
				node.add_child(user=md_user,
					           path_name=item['parent']+item['title'],
					           source=source_check(item['source']),
					           accessed=False,
					           title=item['title'],
					           st_mtime=item['st_mtime'],
					           st_size=item['st_size'],
					           st_uid=md_user.user.username,
					           is_dir=item['is_dir'],)
	except Exception as e:
		response['status']  = 400
		response['message'] = e

		return response

################################
#Non Dajax Registered Functions#
################################
def google_get_client(md_user):
	credentials = Storage(DriveCredentials, 'id', md_user, 'credential').get()
	http        = credentials.authorize(http=httplib2.Http())
	
	return build('drive', 'v2', http=http)

def check_db_title(path, title):
	if path == '/':
		return '/.shared'+path+title
	else:
		return '/.shared'+path+'/'+title

def check_gd_title(path, title):
	if path == '/':
		return path+title
	else:
		return path+'/'+title



