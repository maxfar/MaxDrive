from django import forms
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, ButtonHolder
from crispy_forms.bootstrap import InlineRadios

###########################################################################
## Standard forms. Both only offer destination options to MaxDrive and   ##
## parent node source.                                                   ##
###########################################################################

class MkdirForm(forms.Form):
	title        = forms.CharField(label=(u'Folder Name'))
	options      = forms.CharField(widget=forms.Select(choices=[]))

	def __init__(self, source, path, *args, **kwargs):
		self.helper             = FormHelper()
		self.helper.form_tag    = False
		super(MkdirForm, self).__init__(*args, **kwargs)

		self.destinations = [("dropbox", 'Dropbox'), 
		                     ('drive', 'Google'),]
		self.source       = source
		self.path         = path

		if path == '/':
			pass
		elif self.source == 'dropbox':
			self.destinations.remove(('drive', 'Google'))
		elif self.source == 'drive':
			self.destinations.remove(("dropbox", 'Dropbox'))

		self.fields['options'].widget.choices = self.destinations

class UploadForm(forms.Form):
	file    = forms.FileField()
	options = forms.CharField(widget=forms.Select(choices=[]))
	
	def __init__(self, source, *args, **kwargs):
		self.helper             = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_tag    = False
		self.helper.add_input(Submit('submit', 'Upload'))
		super(UploadForm, self).__init__(*args, **kwargs)

		self.destinations = [("dropbox", 'Dropbox'), 
		                     ('drive', 'Google'), 
		                     ('maxdrive', 'MaxDrive')]
		self.source       = source

		if self.source == 'maxdrive':
			pass
		elif self.source == 'dropbox':
			self.destinations.remove(('drive', 'Google'))
		elif self.source == 'drive':
			self.destinations.remove(("dropbox", 'Dropbox'))

		self.fields['options'].widget.choices = self.destinations