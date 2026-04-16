import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'codeshare'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeshare.settings')

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
