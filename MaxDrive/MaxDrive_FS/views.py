from MaxDrive_FS.models import Node, Source_List, Drive_Data, Dropbox_Data, MaxDrive_Data, MaxDrive_Piece
from MaxDrive_FS.forms import MkdirForm, UploadForm
from MaxDrive_User.models import MaxDrive_User
import os
import urllib
from hurry.filesize import size, si
from dropbox.rest import ErrorResponse
from datetime import datetime
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.utils.timezone import utc

######################################################
## Node: return a folder view of the requested path ##
######################################################
def node(request, username, path):
	md_user = MaxDrive_User.objects.get(user=request.user)
	path    = root_check(path)
	node    = node_check(md_user, path)

	if not node.accessed:
		node = node_populate(request, path, md_user, source=node.source)

	context = {'nodes'    : node_children(node),
	           'dir'      : node.title,
	           'parent'   : node.path_name,
	           'forms'    : {'upload' : UploadForm(node.source.short), 'new_dir' : MkdirForm(node.source.short, path)},
	           'split'    : (lambda x: '' if x == '/' else '/')(path),
	           'stat_fs'  : request.session.get('client').about(),
	           'crumbs'   : get_breadcrumbs(node.path_name),
	           'response' : request.session.get('response')}
	request.session.pop('response', None)

	return render_to_response('MaxDrive_FS/node.html',
			                  context,
			                  context_instance=RequestContext(request))

def node_populate(request, path, md_user, source=None):
	node  = Node.objects.get(user=md_user, path_name=path)
	#Get list of items for node
	items = request.session.get('client').metadata(node)

	#Create items
	for item in items:
		node_create(item, md_user, node)

	node.accessed = True
	node.save()

	return node

#Pass upload request to client and return status
def upload(request, username, path, op):
	path    = root_check(path)
	md_user = MaxDrive_User.objects.get(user=request.user)
	node    = node_check(md_user, path)

	if request.method == "POST":
		new_file    = request.FILES['file']
		destination = request.POST['options']
		response    = request.session.get('client').upload(node, new_file, md_user, destination)

		if response['status'] in [200, 201] :
			node_create(response['data'], md_user, node, accessed=response['accessed'])

		request.session['response'] = response

		return HttpResponseRedirect(crud_redirect_builder(md_user, node))

	else:
		context = {'node'   : node,
		           'client' : request.session.get('client'),
		           'form'   : UploadForm,
		           'parent' : node.path_name,}

		return render_to_response('MaxDrive_FS/upload.html',
			                      context,
			                      context_instance=RequestContext(request))

#MkDir: Create a new directory as child of current node
def mkdir(request, username, path, op):
	path    = root_check(path)
	md_user = MaxDrive_User.objects.get(user=request.user)
	node    = node_check(md_user, path)

	if request.method == 'POST':
		form     = MkdirForm(request.POST, path)

		title    = request.POST['title']
		dest     = (lambda x: x['options'] if 'options' in x else None)(request.POST)
		response = request.session.get('client').mkdir(node, title, dest)

		if response['status'] == 200:
			node_create(response['data'], md_user, node)

		request.session['response'] = response

		return HttpResponseRedirect(crud_redirect_builder(md_user, node))

	else:
		context = {'form'   : MkdirForm,
	               'parent' : node.path_name,}

		return render_to_response('MaxDrive_FS/crud.html',
			                      context,
			                      context_instance=RequestContext(request))

#Delete: Delete a file or folder. Attempt cloud delete first, if successeful
#        delete the node.
def delete(request, username, path, op):
	md_user = MaxDrive_User.objects.get(user=request.user)
	path    = root_check(path)
	node    = node_check(md_user, path)

	if request.method == "POST":
		response = request.session.get('client').delete(node)

		if response['status'] == 200:
			node.delete()

			path = os.path.split(node.path_name)[0]
			node = Node.objects.get(user=md_user, path_name=path)

		request.session['response'] = response

		return HttpResponseRedirect(crud_redirect_builder(md_user, node))

	else:
		context = {'node' : node}

		return render_to_response('MaxDrive_FS/delete.html',
			                      context,
			                      context_instance=RequestContext(request))

#Pass download request to client and return link or error
def download(request, username, path, op):
	path    = root_check(path)
	md_user = MaxDrive_User.objects.get(user=request.user)
	node    = node_check(md_user, path)

	response = request.session.get('client').download_link(node, md_user)

	if response['status'] == 200:

		context = {'node'   : node,
		           'client' : request.session.get('client'),
		           'media'  : response} 

		return render_to_response('MaxDrive_FS/download.html',
			                      context,
			                      context_instance=RequestContext(request))
	
	return HttpResponse(str(response['status'])+' '+response['message'])

#Revisions: Get the available revsions of a node to be listed
def revisions(request, username, path, op):
	path    = root_check(path)
	md_user = MaxDrive_User.objects.get(user=request.user)

	try:
		node = Node.objects.get(user=md_user, path_name=path)
	except Node.DoesNotExist as e:
		return HttpResponse(e)

	response = request.session.get('client').revisions(node)

	if response['status'] == 200:

		context = {'node'       : node,
		           'client'     : request.session.get('client'),
		           'revisions'  : response['revisions']} 

		return render_to_response('MaxDrive_FS/revisions.html',
			                      context,
			                      context_instance=RequestContext(request))
	
	return HttpResponse(str(response['status'])+' '+response['message'])

#Rebuild: Delete all nodes relating to a user and mock register
def rebuild(request, username):
	md_user = MaxDrive_User.objects.get(user=request.user.id)
	Node.objects.filter(user=md_user).delete()

	root = Node.add_root(user=md_user,
		                 path_name='/',
		                 st_size=0,
		                 source=Source_List.objects.get(name='MaxDrive'),
		                 accessed=True,
		                 title='/',
		                 st_mtime=datetime.utcnow().replace(tzinfo=utc),
		                 st_uid=md_user.user.username,
		                 is_dir=True)

	service_roots = request.session.get('client').register_service_roots()

	for service in service_roots['roots']:
		node_create(service, md_user, root, rebuild=True)

	roots_contents = request.session.get('client').metadata('/')

	node = Node.objects.get(user=md_user, 
		                    source=Source_List.objects.get(short='maxdrive'), 
		                    path_name='/')
	for root_file in roots_contents:
		node_create(root_file, md_user, node)

	request.session['response'] = {'status':200, 'message':'rebuilt'}

	return HttpResponseRedirect(crud_redirect_builder(md_user, root))

##############################
#Non HTTP Returning Functions#
##############################
def root_check(path):
	if not path:
		return '/'
	else:
		return path

#Ensure node exists else 404
def node_check(md_user, path):
	try:
		node = Node.objects.get(user=md_user, path_name=path)
	except Node.MultipleObjectsReturned as e:
		print e

	return node

#Convert data to be appropriately displayed to user
def node_children(node):
	children = node.get_children().exclude(title__in=['.sharedDrive', '.sharedDropbox', '.shared'])

	for child in children:
		if child.is_dir:
			child.st_size = '--'
		else:
			child.st_size = size(int(child.st_size), system=si)

	return children

#Helper function to add node given a MaxDrive item
def node_create(item, md_user, node, accessed=False, rebuild=False):
	if rebuild:
		if item['source'] == 'drive':
			gd = Drive_Data(file_id=item['file_id'],
			                webContentLink=item['webContentLink'],
			                webViewLink=item['webViewLink'],
			                alternateLink=item['alternateLink'],
			                iconLink=item['iconLink'],
			                thumbnailLink=item['thumbnailLink']
			               )
			gd.save()

			node.add_sibling(user=md_user,
			                 path_name=item['parent']+item['title'],
			                 source=Source_List.objects.get(short=item['source']),
			                 accessed=False,
			                 title=item['title'],
			                 st_mtime=item['st_mtime'],
			                 st_size=item['st_size'],
			                 st_uid=md_user.user.username,
			                 is_dir=item['is_dir'],
			                 drive_file=gd)
		elif item['source'] == 'dropbox':
			node.add_sibling(user=md_user,
			                 path_name=item['parent']+item['title'],
			                 source=Source_List.objects.get(short=item['source']),
			                 accessed=False,
			                 title=item['title'],
				             st_mtime=item['st_mtime'],
				             st_size=item['st_size'],
				             st_uid=md_user.user.username,
				             is_dir=item['is_dir'],)
		return
	elif item['source'] == 'maxdrive':
		md = MaxDrive_Data(_hash=item['hash'])
		md.save()
		if item['len'] == 1:
			mp = MaxDrive_Piece(order=item['pieces'][0]['order'], 
				                path=item['pieces'][0]['path'],
				                source=Source_List.objects.get(short=item['pieces'][0]['source']),
				                md_data=md)
			mp.save()

		node.add_child(user=md_user,
			           path_name=(lambda x: x['parent']+x['title'] if x['parent'] == '/' else x['parent']+'/'+x['title'])(item),
			           source=Source_List.objects.get(short=item['source']),
			           accessed=accessed,
			           title=item['title'],
			           st_mtime=item['st_mtime'],
			           st_size=item['st_size'],
			           st_uid=md_user.user.username,
			           is_dir=item['is_dir'],
			           maxdrive_file=md)

	elif item['source'] == 'drive':
		gd = Drive_Data(file_id=item['file_id'],
			           webContentLink=item['webContentLink'],
			           webViewLink=item['webViewLink'],
			           alternateLink=item['alternateLink'],
			           iconLink=item['iconLink'],
			           thumbnailLink=item['thumbnailLink']
			           )
		gd.save()

		node.add_child(user=md_user,
			           path_name=item['parent']+item['title'],
			           source=Source_List.objects.get(short=item['source']),
			           accessed=accessed,
			           title=item['title'],
			           st_mtime=item['st_mtime'],
			           st_size=item['st_size'],
			           st_uid=md_user.user.username,
			           is_dir=item['is_dir'],
			           drive_file=gd)
	elif item['source'] == 'dropbox':
		node.add_child(user=md_user,
			           path_name=item['parent']+item['title'],
			           source=Source_List.objects.get(short=item['source']),
			           accessed=accessed,
			           title=item['title'],
			           st_mtime=item['st_mtime'],
			           st_size=item['st_size'],
			           st_uid=md_user.user.username,
			           is_dir=item['is_dir'],)

#After a CRUD change, return to given URL
def crud_redirect_builder(md_user, node):
	base = 'http://localhost:8000/MaxDrive/User/'
	user = md_user.user.username
	path = node.path_name

	return base+user+path

#Given a path, split into constitents with name and href
def get_breadcrumbs(path):
	crumbs = []

	while 1:
		crumb = {}
		path,folder=os.path.split(path)

		if path=="/" and folder == "":
			break
		elif path=="/" and folder!="":
			crumb['name'] = folder
			crumb['href'] = path+folder
			crumbs.append(crumb)
		elif folder!="":
			crumb['name'] = folder
			crumb['href'] = path+'/'+folder
			crumbs.append(crumb)
		elif path!="":
			crumb['name'] = path
			crumb['href'] = path+'/'+folder
			crumbs.append(crumb)
			break

	crumbs.reverse()

	return crumbs