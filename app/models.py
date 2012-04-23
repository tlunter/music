from django.db import models
from django.contrib.auth.models import User
from Music.settings import SCAN_STATES

# Create your models here.
class Setting(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

class Track(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255)
    albumartist = models.CharField(max_length=255)
    length = models.IntegerField()
    file_path = models.CharField(max_length=255)

    class Meta:
        unique_together = ('title', 'artist', 'album', 'file_path')
        permissions = (('can_poll_for_tracks', 'Can analyze for new tracks in the Music folder'),)

    def __unicode(self):
        return u'{0} {1} {2} {3} {4}'.format(self.pk, self.title, self.artist, self.album, self.albumartist)

class QueueItem(models.Model):
    user = models.ForeignKey(User)
    track = models.ForeignKey(Track)
    played = models.BooleanField()
    deleted = models.BooleanField()
    time_added = models.DateTimeField(auto_now_add = True)

class ScanCount(models.Model):
    user = models.ForeignKey(User)
    curr_count = models.IntegerField()
    total_count = models.IntegerField()
    state = models.CharField(max_length=2, choices=SCAN_STATES)
