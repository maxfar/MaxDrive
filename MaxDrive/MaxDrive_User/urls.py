from MaxDrive_User import views
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', views.LoginRequest),
    url(r'^Register', views.RegistrationRequestStageOne),
    url(r'^Logout', views.LogoutRequest),
    url(r'^User/', include('MaxDrive_FS.urls'))
)