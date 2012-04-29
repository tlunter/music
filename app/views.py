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

def index_view(request):
    queue_items = QueueItem.objects.filter(played = False, deleted = False).order_by('pk')[0:10]
    
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
    
    queue_tracks = QueueItem.objects.filter(user = user_profile).exclude(deleted = True).order_by('-time_added')[:10]
    
    return render_to_response('profile.html',
            {'user_profile': user_profile,
             'gravatar_email': gravatar_email,
             'queue_tracks': queue_tracks},
            context_instance=RequestContext(request))

@login_required
def search_view(request):
    if request.method == "POST":
        search_terms = request.POST['search_term']
        
        search_data = instant_search_fn(search_terms) 
        
        return render_to_response('search.html',
                {'search_terms': search_terms,
                 'search_data': search_data},
                context_instance=RequestContext(request))
    
    return render_to_response('search.html',
            context_instance=RequestContext(request))


@login_required
@csrf_exempt
def instant_search_view(request):
    if request.method == 'POST' and len(request.POST['search_term']) > 1:
        search_terms = request.POST['search_term']
        
        query = instant_search_fn(search_terms)
        
        return HttpResponse(serializers.serialize('json',
            query,
            fields = ('title','album','artist')))
    
    raise Http404

def instant_search_fn(search_term):
    raw_search_terms = search_term.split()
    search_terms = filter(None, raw_search_terms)

    title_map       = map(lambda term: '(`title` LIKE %s) * {0}'.format(len(term) * 3), search_terms)
    album_map       = map(lambda term: '(`album` LIKE %s) * {0}'.format(len(term)), search_terms)
    artist_map      = map(lambda term: '(`artist` LIKE %s) * {0}'.format(len(term) * 2), search_terms)
    albumartist_map = map(lambda term: '(`albumartist` LIKE %s) * {0}'.format(len(term) * 2), search_terms)

    changed_terms = map(lambda term: '%{0}%'.format(term), search_terms)
    
    query = Track.objects.extra(
        select = {
            'count': ' + '.join(title_map + album_map + artist_map + albumartist_map)
        },
        select_params = changed_terms * 4,
        where = [' OR '.join(title_map + album_map + artist_map + albumartist_map)],
        params = changed_terms * 4,
        order_by = ['-count', 'artist'])
    
    return query

@login_required
@csrf_exempt
def queue_track_view(request):
    if request.method == 'POST':
        if 'track-pk' in request.POST:
            track_pk = request.POST['track-pk']
            track = Track.objects.get(pk = track_pk)
            
            confirmation = True if 'confirm' in request.POST else False
            
            check_last_queue = QueueItem.objects.exclude(played = True, deleted = True).order_by('-pk')[0:2]
            
            queued = False
            for queue_item in check_last_queue:
                if queue_item.track.pk == track.pk:
                    queued = True
            
            if queued and confirmation is False:
                return HttpResponse('confirm')
            
            QueueItem.objects.create(user = request.user, track = track, played = False, deleted = False)
            
            return HttpResponse('success')
        
        raise Http404

@login_required
@csrf_exempt
def delete_queue_item_view(request):
    if request.method == 'POST':
        queue_item_pk = request.POST['queue-item-pk']
        queue_item = QueueItem.objects.get(pk = queue_item_pk)

        if request.user == queue_item.user:
            queue_item.deleted = True
            queue_item.save()
            return HttpResponse('success')

    return Http404

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
        
        all_tracks = Track.objects.all()

        for track in all_tracks:
            if not os.path.exists(track.file_path.strip('"').strip("'")):
                track.delete()
        
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

