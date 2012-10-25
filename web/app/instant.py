import simplejson
import pp
import thread
from itertools import izip
import time

def add(x,y):
    return x + y

def rating(term_piece, track_string):
    return len(term_piece) if term_piece in track_string else 0

class TrackAccumulator:
    def __init__(self):
        self._lock = thread.allocate_lock()
        self._tracks = []
    
    def append(self, track):
        self._lock.acquire()
        self._tracks += track
        self._lock.release()

    def tracks(self):
        return self._tracks

def track_map(track_data, search_term):
    accumulation = []
    for track in track_data:
        track_string = u'{0} {1} {2} {3}'.format(track['title'].lower(), track['album'].lower(), track['artist'].lower(), track['albumartist'].lower())
        split_track_rating = map(lambda x: rating(x, track_string), search_term)
        track_rating = reduce(add, split_track_rating, 0)
        track['rating'] = track_rating
        accumulation.append(track)
    return accumulation
    

def instant_search_method(search_term, track_listing):
    new_track_listing = TrackAccumulator()

    job_server = pp.Server()

    thread_count = 1 
    track_count = len(track_listing)
    offset_count = track_count/thread_count
    
    for i in range(thread_count):
        start = i*offset_count
        end = min(track_count, start+offset_count)
        thread = job_server.submit(track_map, (track_listing[start:end], search_term), (rating, add), callback=new_track_listing.append)

    job_server.wait()

    mapped_track_listing = new_track_listing.tracks()

    filtered_track_listing = filter(lambda track: True if track['rating'] > 0 else False, mapped_track_listing)
    sorted_track_listing = sorted(filtered_track_listing, key=lambda track: track['rating'], reverse=True)
    return sorted_track_listing

def instant_search_method_older(search_term, track_listing):
    new_track_listing = []

    for track in track_listing:
        new_track = track
        track_string = u'{0} {1} {2} {3}'.format(track['title'].lower(), track['album'].lower(), track['artist'].lower(), track['albumartist'].lower())
        split_track_rating = map(lambda x: rating(x, track_string), search_term)
        track_rating = reduce(add, split_track_rating, 0)
        new_track['rating'] = track_rating
        new_track_listing.append(new_track)

    mapped_track_listing = new_track_listing

    filtered_track_listing = filter(lambda track: True if track['rating'] > 0 else False, mapped_track_listing)
    sorted_track_listing = sorted(filtered_track_listing, key=lambda track: track['rating'], reverse=True)
    return sorted_track_listing

if __name__ == '__main__':
    tracks = open('/home/tlunter/Projects/Music/tracks.txt', 'r+')
    track_listing = simplejson.load(tracks)

    SIZE = 1
    times = [0] * SIZE 

    start = time.time()

    print "pp.map"
    for i in range(SIZE):
        instant_search_method(['radiohead'], track_listing)
        times[i] = time.time() - start
        start = time.time()

    sorted_times = sorted(times)
    print sorted_times[SIZE/2]
    start = time.time()

    print "map"
    for i in range(SIZE):
        instant_search_method_older(['radiohead'], track_listing)
        times[i] = time.time() - start
        start = time.time()

    sorted_times = sorted(times)
    print sorted_times[SIZE/2]
    start = time.time()
