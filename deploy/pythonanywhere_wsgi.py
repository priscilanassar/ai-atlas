"""Copy into the WSGI configuration file linked from PythonAnywhere's Web tab."""
import os
import sys
from pathlib import Path

project = Path.home() / 'ai-atlas'
if str(project) not in sys.path:
    sys.path.insert(0, str(project))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.pythonanywhere'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
