import os, sys

APACHE_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.abspath(os.path.dirname(APACHE_PATH))
PROJECTS_PATH = os.path.abspath(os.path.dirname(ROOT_PATH))

sys.path.append(APACHE_PATH)
sys.path.append(ROOT_PATH)
sys.path.append(PROJECTS_PATH)

os.environ['DJANGO_SETTINGS_MODULE'] = 'Music.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
