from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from MaxDrive_User.models import MaxDrive_User
from MaxDrive_FS.models import Node
from CombinedAPI.Client import datetime_normalization
import os

###########################################################################
## All function return json responses from the request regardless of     ##
## positive or negative outcome.                                         ##
###########################################################################

###########################################################################
## Get the revisions of a file from the client                           ##
###########################################################################
@dajaxice_register
def revisions(request, source, path):
	path    = root_check(path)
	md_user = MaxDrive_User.objects.get(user=request.user)

	try:
		node = Node.objects.get(user=md_user, path_name=path)
	except Node.DoesNotExist as e:
		return HttpResponse(e)

	response = request.session.get('client').revisions(node)

	if response['status'] == 200:
		for revision in response['revisions']:
			revision['path']     = os.path.split(revision['path'])[1]
			revision['modified'] = datetime_normalization(revision['modified'], 'dropbox')

		return simplejson.dumps({'status':response['status'], 'response':response['message'], 'revisions':response['revisions']})
	
	return simplejson.dumps({'status':400, 'response' :response['message']})

###########################################################################
## Return status and message for a download request                      ##
###########################################################################
@dajaxice_register
def download(request, source, path):
	path    = root_check(path)
	md_user = MaxDrive_User.objects.get(user=request.user)

	try:
		node = Node.objects.get(user=md_user, path_name=path)
	except Node.DoesNotExist as e:
		return HttpResponse(e)

	response = request.session.get('client').download_link(node, md_user)

	if response['status'] == 200:
		return simplejson.dumps({'status':200, 'url':response['url'], 'data':response['data']})
	elif response['status'] == 201:
		return simplejson.dumps({'status':201, 'url':response['url'], 'data':response['data']})

	return simplejson.dumps({'status':response['status'], 'message':response['message']})

def root_check(path):
	if not path:
		return '/'
	else:
		return path