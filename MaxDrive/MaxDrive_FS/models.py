from django.db import models
from treebeard.mp_tree import MP_Node
from MaxDrive_User.models import MaxDrive_User

#############################################################
## SourceList: Name and abbreviated name of source account ##
#############################################################
class Source_List(models.Model):
	name  = models.TextField(default='')
	short = models.TextField()

##############################################################
## MaxDrivePiece: the source, path and related MaxDriveData ##
##############################################################
class MaxDrive_Piece(models.Model):
	source  = models.ForeignKey(Source_List)
	order   = models.IntegerField()
	path    = models.TextField(default='1')
	md_data = models.ForeignKey('MaxDrive_Data')

	class Meta:
		ordering = ['order']

###############################################
## MaxDriveData: MaxDrive specific node data ##
###############################################
class MaxDrive_Data(models.Model):
	_hash  = models.TextField(default='1')

###############################################
## DropboxData: MaxDrive specific node data ###
###############################################
class Dropbox_Data(models.Model):
	icon       = models.TextField(default='')
	mime_type  = models.TextField(default='')

#########################################
## DriveData: Drive specific node data ##
#########################################
class Drive_Data(models.Model):
	webContentLink = models.URLField(null=True, blank=True)
	webViewLink    = models.URLField(null=True, blank=True)
	alternateLink  = models.URLField(null=True, blank=True)
	iconLink       = models.URLField(null=True, blank=True)
	thumbnailLink  = models.URLField(null=True, blank=True)
	file_id        = models.CharField(null=False, max_length=30)

##################################################################
## Node: Basic information about an item, inherits from MP_Node ##
##################################################################
class Node(MP_Node):
	user          = models.ForeignKey(MaxDrive_User)
	path_name     = models.TextField()
	source        = models.ForeignKey(Source_List, null=False)
	accessed      = models.BooleanField(default=False)
	#Generic node fields
	title         = models.TextField()
	st_size  	  = models.CharField(max_length=30)
	st_mtime 	  = models.DateTimeField(null=True)
	st_uid   	  = models.CharField(max_length=30)
	is_dir     	  = models.BooleanField(default=0)
	#Source specific fields
	drive_file    = models.ForeignKey(Drive_Data, null=True, blank=True)
	dropbox_file  = models.ForeignKey(Dropbox_Data, null=True, blank=True)
	maxdrive_file = models.ForeignKey(MaxDrive_Data, null=True, blank=True)

	class Meta:
		unique_together = (('user', 'path_name'),)

	def __unicode__(self):
	    return 'Node: %s' % self.path_name