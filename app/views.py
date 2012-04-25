from Music.app.models import Track, QueueItem, Setting, ScanCount
from Music.settings import MUSIC_FOLDER
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.db.models import F, Q
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import subprocess
import threading
import hashlib
import os
import simplejson
import time
import multiprocessing
pool = multiprocessing.Pool()

def index(request):
    queue_items = QueueItem.objects.exclude(played = True, deleted = True).order_by('pk')

    return render_to_response('index.html',
            {'queue_items': queue_items},
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

    queue_tracks = QueueItem.objects.filter(user = request.user).exclude(deleted = True).order_by('-time_added')[:10]

    return render_to_response('profile.html',
            {'user_profile': user_profile,
             'gravatar_email': gravatar_email,
             'queue_tracks': queue_tracks},
            context_instance=RequestContext(request))

@login_required
def search_view(request):

    search_query = ''
    if request.method == "POST":
        search_query = request.POST['search_term']

        search_data = instant_search_view(request).content

        search_data = simplejson.loads(search_data)
        
        return render_to_response('search.html',
                {'search_query': search_query,
                 'search_data': search_data},
                context_instance=RequestContext(request))

    return render_to_response('search.html',
            context_instance=RequestContext(request))


@login_required
@csrf_exempt
def instant_search_view(request):
    if request.method == 'POST' and len(request.POST['search_term']) > 1:
        raw_search_terms = request.POST['search_term'].split()
        search_terms = filter(None, raw_search_terms)
        start = time.time()
        
        title_map       = map(lambda term: "(`title` LIKE '%%{0}%%') * {1}".format(term, len(term) * 3), search_terms)
        album_map       = map(lambda term: "(`album` LIKE '%%{0}%%') * {1}".format(term, len(term)), search_terms)
        artist_map      = map(lambda term: "(`artist` LIKE '%%{0}%%') * {1}".format(term, len(term) * 2), search_terms)
        albumartist_map = map(lambda term: "(`albumartist` LIKE '%%{0}%%') * {1}".format(term, len(term) * 2), search_terms)

        start = time.time()
        query = Track.objects.extra(
            select = {
                'count': ' + '.join(title_map + album_map + artist_map + albumartist_map)
            },
            where = [' OR '.join(title_map + album_map + artist_map + albumartist_map)],
            order_by = ['-count', 'artist'])

        print "Query: ", query.query

        query = list(query)
        print "Processing: ", time.time() - start

        return HttpResponse(serializers.serialize('json', query, fields = ('title','album','artist'))) #simplejson.dumps(tracks))

    raise Http404

def queue_tracks_view(request):
    if request.method == 'POST':
        if 'song' in request.POST:
            return render_to_response('queue_tracks.html',
                    {'song': request.POST['song']},
                    context_instance=RequestContext(request))
    raise Http404

def load_tracks_view(request):

    if not request.user.has_perm('app.can_poll_for_tracks'):
        return render_to_response('load_tracks/permissions.html',
                context_instance=RequestContext(request))

    scans = request.user.scancount_set
    current_scans = scans.exclude(state = 'VE').order_by('-pk')

    if current_scans.count() > 0:
        latest_scan = current_scans[0]

        if latest_scan.state == 'FI':
            latest_scan.state = 'VE'
            latest_scan.save()
            return render_to_response('load_tracks/finished.html',
                    {'scan': latest_scan},
                    context_instance=RequestContext(request))

        percentage = float(latest_scan.curr_count)/float(latest_scan.total_count)*100
        return render_to_response('load_tracks/running.html',
                {'scan':latest_scan, 'percentage':percentage},
                context_instance=RequestContext(request))

    successful = start_track_update(request)

    if not successful:
        return render_to_response('load_tracks/error.html',
                {'error': 'no tracks'},
                context_instance=RequestContext(request))

    latest_scan = current_scans[0]
    return render_to_response('load_tracks/success.html',
            {'scan':latest_scan},
            context_instance=RequestContext(request))

def start_track_update(request):

    tracks = subprocess.Popen(['find', MUSIC_FOLDER, '-iname', '*.mp3'], stdout=subprocess.PIPE)
    track_count = len(tracks.stdout.readlines())

    if not track_count:
        return False

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
                
                    ScanCount.objects.filter(pk = scan_id).update(curr_count = F('curr_count') + 1)
                    audio = MP3(os.path.join(root,mp3), ID3=EasyID3)

                    length = int(audio.info.length)

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
                                  'file_path':file_path, 'length':length})
                    
            for track in music:
                Track.objects.get_or_create(title = track['title'],
                                            artist = track['artist'],
                                            album = track['album'],
                                            albumartist = track['albumartist'],
                                            file_path = track['file_path'],
                                            length = track['length'])

        ScanCount.objects.filter(pk = scan_id).update(state = 'FI')

    threading.Thread(target=start_scan, args=(scanner.pk,)).start()
    return True

