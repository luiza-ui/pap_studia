"""
Configurações de desenvolvimento local.
Usa SQLite, imprime emails no terminal, DEBUG activo.
"""

from .base import *

DEBUG = True

SECRET_KEY = 'django-insecure-n4rnloeo7mc4moy^x9mwyj__5n$b@mn-2)y-xi8o@#qqoz3c4g'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Emails impressos no terminal — sem envio real
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
