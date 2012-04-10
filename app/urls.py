from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('Music.app.views',
    url(r'^my-profile/$', 'profile_view', name='my-profile-page'),
    url(r'^profile/(?P<username>.*)/$', 'profile_view', name='profile-page'),
    url(r'^logout/$', 'logout_view', name='logout-page'),
    url(r'^$', 'index', name='index-page'),
)
