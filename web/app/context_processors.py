from django.conf import settings

def root_url(context):
    return { 'ROOT_URL': settings.ROOT_URL }
