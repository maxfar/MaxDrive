# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Source_List'
        db.create_table(u'MaxDrive_FS_source_list', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')(default='')),
            ('short', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'MaxDrive_FS', ['Source_List'])

        # Adding model 'MaxDrive_Piece'
        db.create_table(u'MaxDrive_FS_maxdrive_piece', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_FS.Source_List'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('path', self.gf('django.db.models.fields.TextField')(default='1')),
            ('md_data', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_FS.MaxDrive_Data'])),
        ))
        db.send_create_signal(u'MaxDrive_FS', ['MaxDrive_Piece'])

        # Adding model 'MaxDrive_Data'
        db.create_table(u'MaxDrive_FS_maxdrive_data', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_hash', self.gf('django.db.models.fields.TextField')(default='1')),
        ))
        db.send_create_signal(u'MaxDrive_FS', ['MaxDrive_Data'])

        # Adding model 'Dropbox_Data'
        db.create_table(u'MaxDrive_FS_dropbox_data', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('icon', self.gf('django.db.models.fields.TextField')(default='')),
            ('mime_type', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal(u'MaxDrive_FS', ['Dropbox_Data'])

        # Adding model 'Drive_Data'
        db.create_table(u'MaxDrive_FS_drive_data', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('webContentLink', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('webViewLink', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('alternateLink', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('iconLink', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('thumbnailLink', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('file_id', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'MaxDrive_FS', ['Drive_Data'])

        # Adding model 'Node'
        db.create_table(u'MaxDrive_FS_node', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('depth', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('numchild', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_User.MaxDrive_User'])),
            ('path_name', self.gf('django.db.models.fields.TextField')(default='1')),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_FS.Source_List'])),
            ('accessed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.TextField')(default='1')),
            ('st_size', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('st_mtime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('st_uid', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('is_dir', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('drive_file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_FS.Drive_Data'], null=True, blank=True)),
            ('dropbox_file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_FS.Dropbox_Data'], null=True, blank=True)),
            ('maxdrive_file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['MaxDrive_FS.MaxDrive_Data'], null=True, blank=True)),
        ))
        db.send_create_signal(u'MaxDrive_FS', ['Node'])

        # Adding unique constraint on 'Node', fields ['user', 'path_name']
        db.create_unique(u'MaxDrive_FS_node', ['user_id', 'path_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Node', fields ['user', 'path_name']
        db.delete_unique(u'MaxDrive_FS_node', ['user_id', 'path_name'])

        # Deleting model 'Source_List'
        db.delete_table(u'MaxDrive_FS_source_list')

        # Deleting model 'MaxDrive_Piece'
        db.delete_table(u'MaxDrive_FS_maxdrive_piece')

        # Deleting model 'MaxDrive_Data'
        db.delete_table(u'MaxDrive_FS_maxdrive_data')

        # Deleting model 'Dropbox_Data'
        db.delete_table(u'MaxDrive_FS_dropbox_data')

        # Deleting model 'Drive_Data'
        db.delete_table(u'MaxDrive_FS_drive_data')

        # Deleting model 'Node'
        db.delete_table(u'MaxDrive_FS_node')


    models = {
        u'MaxDrive_FS.drive_data': {
            'Meta': {'object_name': 'Drive_Data'},
            'alternateLink': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'file_id': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'iconLink': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thumbnailLink': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'webContentLink': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'webViewLink': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'MaxDrive_FS.dropbox_data': {
            'Meta': {'object_name': 'Dropbox_Data'},
            'icon': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mime_type': ('django.db.models.fields.TextField', [], {'default': "''"})
        },
        u'MaxDrive_FS.maxdrive_data': {
            'Meta': {'object_name': 'MaxDrive_Data'},
            '_hash': ('django.db.models.fields.TextField', [], {'default': "'1'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'MaxDrive_FS.maxdrive_piece': {
            'Meta': {'ordering': "['order']", 'object_name': 'MaxDrive_Piece'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md_data': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_FS.MaxDrive_Data']"}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'path': ('django.db.models.fields.TextField', [], {'default': "'1'"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_FS.Source_List']"})
        },
        u'MaxDrive_FS.node': {
            'Meta': {'unique_together': "(('user', 'path_name'),)", 'object_name': 'Node'},
            'accessed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'drive_file': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_FS.Drive_Data']", 'null': 'True', 'blank': 'True'}),
            'dropbox_file': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_FS.Dropbox_Data']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dir': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'maxdrive_file': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_FS.MaxDrive_Data']", 'null': 'True', 'blank': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'path_name': ('django.db.models.fields.TextField', [], {'default': "'1'"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_FS.Source_List']"}),
            'st_mtime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'st_size': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'st_uid': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'title': ('django.db.models.fields.TextField', [], {'default': "'1'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['MaxDrive_User.MaxDrive_User']"})
        },
        u'MaxDrive_FS.source_list': {
            'Meta': {'object_name': 'Source_List'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'short': ('django.db.models.fields.TextField', [], {})
        },
        u'MaxDrive_User.drivecredentials': {
            'Meta': {'object_name': 'DriveCredentials'},
            'api_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'api_scope': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'api_secret_2': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'api_uri': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'credential': ('oauth2client.django_orm.CredentialsField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['MaxDrive_User.MaxDrive_User']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'MaxDrive_User.dropboxcredentials': {
            'Meta': {'object_name': 'DropboxCredentials'},
            'api_access': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'api_secret': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token_key': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'token_secret': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'MaxDrive_User.maxdrive_user': {
            'Meta': {'object_name': 'MaxDrive_User'},
            'drive_creds': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['MaxDrive_User.DriveCredentials']", 'unique': 'True', 'null': 'True'}),
            'dropbox_creds': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['MaxDrive_User.DropboxCredentials']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['MaxDrive_FS']