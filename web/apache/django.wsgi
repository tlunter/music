import os, sys, site

site.addsitedir('/home/tlunter/Envs/Music/lib/python2.7/site-packages/')

APACHE_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.abspath(os.path.dirname(APACHE_PATH))
PROJECTS_PATH = os.path.abspath(os.path.dirname(ROOT_PATH))

sys.path.append(APACHE_PATH)
sys.path.append(ROOT_PATH)
sys.path.append(PROJECTS_PATH)

print sys.path

os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
