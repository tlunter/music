from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('Music.app.views',
    url(r'^track-music-files/$', 'load_tracks_view', name='load-tracks-page'),
    url(r'^delete-queue-item/$', 'delete_queue_item_view', name='delete-queue-item-page'),
    url(r'^queue-track/$', 'queue_track_view', name='queue-track-page'),
    url(r'^instant-search/$', 'instant_search_view', name='instant-search-page'),
    url(r'^search/$', 'search_view', name='search-page'),
    url(r'^profile/$', 'profile_view', name='my-profile-page'),
    url(r'^profile/(?P<username>.*)/$', 'profile_view', name='profile-page'),
    url(r'^logout/$', 'logout_view', name='logout-page'),
    url(r'^$', 'index_view', name='index-page'),
)
