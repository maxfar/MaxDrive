# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DropboxCredentials'
        db.create_table(u'MaxDrive_User_dropboxcredentials', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('api_secret', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('api_access', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('token_key', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('token_secret', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'MaxDrive_User', ['DropboxCredentials'])

        # Adding model 'DriveCredentials'
        db.create_table(u'MaxDrive_User_drivecredentials', (
            ('id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['MaxDrive_User.MaxDrive_User'], unique=True, primary_key=True)),
            ('api_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('api_secret_2', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('api_scope', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('api_uri', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('credential', self.gf('oauth2client.django_orm.CredentialsField')(null=True)),
        ))
        db.send_create_signal(u'MaxDrive_User', ['DriveCredentials'])

        # Adding model 'MaxDrive_User'
        db.create_table(u'MaxDrive_User_maxdrive_user', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('drive_creds', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['MaxDrive_User.DriveCredentials'], unique=True, null=True)),
            ('dropbox_creds', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['MaxDrive_User.DropboxCredentials'], unique=True)),
        ))
        db.send_create_signal(u'MaxDrive_User', ['MaxDrive_User'])


    def backwards(self, orm):
        # Deleting model 'DropboxCredentials'
        db.delete_table(u'MaxDrive_User_dropboxcredentials')

        # Deleting model 'DriveCredentials'
        db.delete_table(u'MaxDrive_User_drivecredentials')

        # Deleting model 'MaxDrive_User'
        db.delete_table(u'MaxDrive_User_maxdrive_user')


    models = {
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

    complete_apps = ['MaxDrive_User']