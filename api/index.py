import sys
import os

# Add codeshare to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'codeshare'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeshare.settings')

import django
django.setup()

# Run migrations automatically on cold start
try:
    from django.core.management import call_command
    call_command('migrate', '--run-syncdb', verbosity=0, interactive=False)
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
