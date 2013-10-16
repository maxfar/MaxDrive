from django.db import models
from django.contrib.auth.models import User
from oauth2client.django_orm import CredentialsField

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^"])
