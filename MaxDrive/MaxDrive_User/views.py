from MaxDrive_User.forms import LoginForm, RegistrationForm, DropboxForm, DriveForm
from MaxDrive_User.models import MaxDrive_User, DriveCredentials, DropboxCredentials
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.django_orm import Storage
from dropbox import client, rest, session
from CombinedAPI import Client


###########################################################################
## Standard login. If success client is built and added to session       ##
###########################################################################
def LoginRequest(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect('User/'+str(request.user))
	
	if request.method == 'POST':
		form = LoginForm(request.POST)

		if form.is_valid():
			u    = form.cleaned_data['username']
			p    = form.cleaned_data['password']
			user = authenticate(username=u, password=p)

			if user is not None:
				md_user = MaxDrive_User.objects.get(user=user)
				client  = Client.CombinedClient('login', md_user)
				request.session['client'] = client
				
				login(request, user)

				return HttpResponseRedirect('User/'+str(request.user))
			else:
				context = {'form' : form}
				return render_to_response('MaxDrive_User/landing.html',
			                               context,
			                               context_instance=RequestContext(request))

	else:
		form    = LoginForm
		context = {'form' : form}

		return render_to_response('MaxDrive_User/landing.html',
			                      context,
			                      context_instance=RequestContext(request))

###########################################################################
## If there has been a successful creation of Drive and Dropbox tokens   ##
## create a MaxDrive user and redirect                                   ##
###########################################################################
def RegistrationRequestStageOne(request):
	if request.user.is_authenticated():
		return HttpResponse('authenicated')

	if request.method == 'POST':
		form = RegistrationForm(request.POST)

		if form.is_valid():
			#Attempt authorization of Dropbox
			dropbox_secret = request.POST['api_secret']
			dropbox_key    = request.POST['api_key']
			dropbox_access = request.POST['api_access']
			
			sess           = session.DropboxSession(dropbox_key, dropbox_secret, dropbox_access)
			request_token  = sess.obtain_request_token()
			print sess.build_authorize_url(request_token)
			raw_input()
			access_token   = sess.obtain_access_token(request_token)

			#Attempt authorization of Drive
			c_id        = request.POST['api_id']
			c_secret    = request.POST['api_secret_2']
			o_scope     = request.POST['api_scope']
			r_URI       = request.POST['api_uri']

			flow        = OAuth2WebServerFlow(c_id, c_secret, o_scope, r_URI)
			print flow.step1_get_authorize_url()
			code        = raw_input('Enter verification code: ').strip()
			credentials = flow.step2_exchange(code)

			d = DropboxCredentials(api_key=dropbox_key,
  		                       	   api_secret=dropbox_secret,
  		                           api_access=dropbox_access,
  		                           token_key=access_token.key,
  		                           token_secret=access_token.secret)
			d.save()

			u = User.objects.get(username='maxwell')
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

			p    = form.cleaned_data['password']
			user = authenticate(username='maxwell', password=p)
			login(request, user)

			client  = Client.CombinedClient('login', m)
			request.session['client'] = client

			return HttpResponseRedirect('http://localhost:8000/MaxDrive/User/'+u.username+'/rebuild')
		else:
			print form.errors
			return HttpResponse('cock')

	else:
		context = {'forms' : {'user':RegistrationForm,
		                      'dropbox':DropboxForm(initial={'api_key':'dwbwzy1tfi5e97b',
		                      	                             'api_secret':'kdnjvjp62bkb1f2',
		                      	                             'api_access':'app_folder'
		                      	                             }
		                      	                    ),
		                      'drive':DriveForm(initial={'api_id':'67639165534-iat1fois0eu3u0uq7cfn3fano7nemetq.apps.googleusercontent.com',
		                      	                         'api_secret_2':'fCI3SAnwZS8NuJA78uQWDY0k',
		                      	                         'api_scope':'https://www.googleapis.com/auth/drive',
		                      	                         'api_uri':'urn:ietf:wg:oauth:2.0:oob'
		                      	                         }
		                      	               )
		                      }
		           }

		return render_to_response('MaxDrive_User/registration.html',
			                      context,
			                      context_instance=RequestContext(request))

###########################################################################
## Standard logout request                                               ##
###########################################################################
def LogoutRequest(request):
        logout(request)
        return HttpResponseRedirect('http://localhost:8000/MaxDrive')