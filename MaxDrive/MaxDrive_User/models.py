from django.db import models
from django.contrib.auth.models import User
from oauth2client.django_orm import CredentialsField

###########################################################################
## Dropbox specific data, token stored as strings to be rebuilt          ##
###########################################################################
class DropboxCredentials(models.Model):
    api_key      = models.CharField(max_length=200)
    api_secret   = models.CharField(max_length=200)
    api_access   = models.CharField(max_length=200)
    #Dropox API Token
    token_key    = models.CharField(max_length=200)
    token_secret = models.CharField(max_length=200)

###########################################################################
## Drive specific data, token stored via a custom Google/Django item     ##
###########################################################################
class DriveCredentials(models.Model):
    id           = models.OneToOneField('MaxDrive_User', primary_key=True)
    api_id       = models.CharField(max_length=200)
    api_secret_2 = models.CharField(max_length=200)
    api_scope    = models.CharField(max_length=200)
    api_uri      = models.CharField(max_length=200)
    #Google API Credentials
    credential = CredentialsField()

###########################################################################
## Extension of normal Django user                                       ##
###########################################################################
class MaxDrive_User(models.Model):
    user           = models.OneToOneField(User)
    drive_creds    = models.OneToOneField(DriveCredentials, null=True)
    dropbox_creds  = models.OneToOneField(DropboxCredentials)

    def __unicode__(self):
        return 'MaxDriveUser: %s' % self.user