from MaxDrive_User.models import MaxDrive_User, DropboxCredentials, DriveCredentials
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field

###########################################################################
## Login with crispy extras                                              ##
###########################################################################
class LoginForm(forms.Form):
	def __init__(self, *args, **kwargs):
		super(LoginForm, self).__init__(*args, **kwargs)
		self.helper             = FormHelper()
		self.helper.form_method = 'post'
		self.helper.layout      = Layout(
			Field('username', placeholder="User Name"),
			Field('password', placeholder="Password"),)

		self.helper.add_input(Submit('submit', 'Submit'))

	username  = forms.CharField(label=(u'User Name'))
	password  = forms.CharField(label=(u'Password'), 
		                        required=True,
                                widget=forms.PasswordInput(render_value=False))

###########################################################################
## Dropbox input for registration minus token stuff                      ##
###########################################################################
class DropboxForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(DropboxForm, self).__init__(*args, **kwargs)
		self.helper             = FormHelper()
		self.helper.form_tag    = False

	class Meta:
		model   = DropboxCredentials
		exclude = ('token_key', 'token_secret')

###########################################################################
## Drive input for registration minus token stuff                        ##
###########################################################################
class DriveForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(DriveForm, self).__init__(*args, **kwargs)
		self.helper             = FormHelper()
		self.helper.form_tag    = False

	class Meta:
		model   = DriveCredentials
		exclude = ('id', 'credential')


###########################################################################
## Overall registration form for normal user stuff                       ##
###########################################################################
class RegistrationForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(RegistrationForm, self).__init__(*args, **kwargs)
		self.helper             = FormHelper()
		self.helper.form_tag    = False
	
	username        = forms.CharField(label=(u'User Name'))
	password        = forms.CharField(label=(u'Password'), widget=forms.PasswordInput(render_value=False))
	password1       = forms.CharField(label=(u'Verify Password'), widget=forms.PasswordInput(render_value=False))

	class Meta:
		model = MaxDrive_User
		exclude = ('user', 'drive_creds', 'dropbox_creds')

	def clean_username(self):
		username = self.cleaned_data['username']
		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			return username
		raise forms.ValidationError("That username is already taken, please select another.")

	def clean(self):
		if self.cleaned_data['password'] != self.cleaned_data['password1']:
			raise forms.ValidationError("The passwords did not match.  Please try again.")
		return self.cleaned_data
		