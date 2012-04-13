from Music.app.models import Track, QueueItem, Setting, ScanCount
from Music.settings import MUSIC_FOLDER
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.db.models import F, Q

from mutagen.easyid3 import EasyID3
import subprocess
import threading
import hashlib
import os

def index(request):
    queue_list = None
    #if request.user.is_authenticated():
    #    queue_list = 

    return render_to_response('index.html',
                              context_instance=RequestContext(request))

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index-page'))

@login_required
def profile_view(request, username = None):
    username = username if username else request.user.username

    user_profile = get_object_or_404(User, username__exact = username)
    m = hashlib.md5()
    m.update(user_profile.email.lower())
    gravatar_email = m.hexdigest()

    return render_to_response('profile.html', {'user_profile': user_profile,
                                               'gravatar_email': gravatar_email,},
                              context_instance=RequestContext(request))

@permission_required('app.can_poll_for_tracks')
def load_tracks_view(request):
    scans = request.user.scancount_set

    current_scans = scans.exclude(state = 'VE').order_by('-pk')

    if current_scans.count() > 0:

        latest_scan = current_scans[0]

        if latest_scan.state is 'FI' and latest_scan.curr_count is latest_scan.total_count:
            
            latest_scan.state = 'VE'
            latest_scan.save()
            return render_to_response('load_tracks_finished.html',
                    {'scan':latest_scan},
                    context_instance=RequestContext(request))

        percentage = float(latest_scan.curr_count)/float(latest_scan.total_count)*100
        return render_to_response('load_tracks_failure.html',
                {'scan':latest_scan, 'percentage':percentage},
                context_instance=RequestContext(request))

    start_track_update(request)
    
    latest_scan = current_scans[0]

    return render_to_response('load_tracks_success.html',
            {'scan':latest_scan},
            context_instance=RequestContext(request))
        


def start_track_update(request):

    tracks = subprocess.Popen(['find', MUSIC_FOLDER, '-type', 'f'], stdout=subprocess.PIPE)
    track_count = len(tracks.stdout.readlines())

    scanner = ScanCount(user = request.user,
                        curr_count = 0,
                        total_count = track_count,
                        state = 'ST')

    scanner.save()

    def start_scan(scan_id): 

        ScanCount.objects.filter(pk = scan_id).update(state = 'SC')

        # Walk through the whole folder for just the files
        for root, dirs, files in os.walk(MUSIC_FOLDER):

            music = []

            # Go through the files in the current folder
            for mp3 in files:
            
                # Only get the ID3 tags of mp3 files
                if os.path.splitext(mp3)[1] == ".mp3":
                    audio = EasyID3(os.path.join(root,mp3))
                    try:
                        raw_artist = (audio['artist'][0]).encode('utf-8')
                        artist = unicode(raw_artist, 'utf-8')
                    except KeyError:
                        artist = u''
                    
                    try:
                        raw_album = (audio['album'][0]).encode('utf-8')
                        album = unicode(raw_album, 'utf-8')
                    except KeyError:
                        album = u''
                    
                    try:
                        raw_title = (audio['title'][0]).encode('utf-8')
                        title = unicode(raw_title, 'utf-8')
                    except KeyError:
                        title = u''

                    try:
                        raw_albumartist = (audio['performer'][0]).encode('utf-8')
                        albumartist = unicode(raw_albumartist, 'utf-8')
                    except KeyError:
                        albumartist = u''

                    raw_file_path = repr(os.path.join(root,mp3)).encode('utf-8')
                    file_path = unicode(raw_file_path, 'utf-8')

                    music.append({'artist':artist, 'album':album,
                                  'title':title, 'albumartist':albumartist,
                                  'file_path':file_path})
                    
            for track in music:
                
                ScanCount.objects.filter(pk = scan_id).update(curr_count = F('curr_count') + 1)

                Track.objects.get_or_create(title = track['title'],
                                            artist = track['artist'],
                                            album = track['album'],
                                            albumartist = track['albumartist'],
                                            file_path = track['file_path'])

        ScanCount.objects.filter(pk = scan_id).update(state = 'FI')

    print scanner.pk

    threading.Thread(target=start_scan, args=(scanner.pk,)).start()
    return True

