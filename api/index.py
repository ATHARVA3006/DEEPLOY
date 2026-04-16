import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'codeshare'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeshare.settings')

import django
django.setup()

# Auto-migrate on cold start
try:
    from django.core.management import call_command
    call_command('migrate', verbosity=0, interactive=False)
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
