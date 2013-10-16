from django.conf.urls import patterns, include, url
from dajaxice.core import dajaxice_autodiscover
from django.conf import settings
from MaxDrive_FS import views

dajaxice_autodiscover()

urlpatterns = patterns('',
	#Dajaxice
	(r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
	#CRUD like operations
	url(r'^(?P<username>\w+)/rebuild', views.rebuild),
	url(r'^(?P<username>\w+)(?P<path>(.*))/(?P<op>upload)', views.upload),
	url(r'^(?P<username>\w+)(?P<path>(.*))/(?P<op>mkdir)', views.mkdir),
	url(r'^(?P<username>\w+)(?P<path>(.*))/(?P<op>delete)', views.delete),
	url(r'^(?P<username>\w+)(?P<path>(.*))/(?P<op>download)', views.download),
	url(r'^(?P<username>\w+)(?P<path>(.*))/(?P<op>revisions)', views.revisions),
    url(r'^(?P<username>\w+)(?P<path>(.*))', views.node),
)
