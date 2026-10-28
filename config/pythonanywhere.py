"""Production settings for the PythonAnywhere web app; local settings stay intact."""
import json
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from .settings import *  # noqa: F403

_path = Path(os.environ.get('ATLAS_CONFIG_PATH', Path.home() / '.config/ai-atlas/production.json'))
try:
    _private = json.loads(_path.read_text(encoding='utf-8'))
    SECRET_KEY = _private['secret_key']
    _host = _private['host']
except (OSError, ValueError, KeyError) as error:
    raise ImproperlyConfigured('Execute python deploy/setup_pythonanywhere.py antes de iniciar o site.') from error
if not isinstance(SECRET_KEY, str) or len(SECRET_KEY) < 50 or not isinstance(_host, str) or not _host:
    raise ImproperlyConfigured('Configuracao de producao incompleta.')

DEBUG = False
ALLOWED_HOSTS = [_host]
CSRF_TRUSTED_ORIGINS = [f'https://{_host}']
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# Enable "Force HTTPS" in the PythonAnywhere Web tab (at the reverse proxy).
# Avoid trusting a forwarded header without verifying the platform configuration.
SECURE_SSL_REDIRECT = False
