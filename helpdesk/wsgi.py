import os
import sys

path = "/home/dcasgroup2810/helpdesk"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "helpdesk.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()