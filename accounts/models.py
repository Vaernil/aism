from django.contrib.auth.models import AbstractUser

from django.db import models


class CustomUser(AbstractUser):
    karma = models.IntegerField(default=1)
    about = models.TextField(default='')
