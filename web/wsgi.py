import os, sys, site
 
site.addsitedir('/home/tlunter/Envs/Music/lib/python2.7/site-packages')

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_NAME = os.path.basename(PROJECT_PATH)
ROOT_PATH = os.path.abspath(os.path.dirname(PROJECT_PATH))

sys.path.append(PROJECT_PATH)
sys.path.append(ROOT_PATH)

print sys.path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
