from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Setting(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

class Track(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255)
    albumartist = models.CharField(max_length=255)

class QueueItem(models.Model):
    user = models.ForeignKey(User)
    track = models.ForeignKey(Track)

