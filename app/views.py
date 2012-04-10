from Music.app.models import Track, QueueItem, Setting
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def index(request):
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

    return render_to_response('profile.html', {'user_profile': user_profile},
                              context_instance=RequestContext(request))
