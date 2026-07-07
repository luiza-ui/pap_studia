"""
Configurações de produção (Railway).
Todas as variáveis sensíveis vêm de variáveis de ambiente.
"""

import os
import dj_database_url
from .base import *

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# WhiteNoise serve os ficheiros estáticos directamente
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Base de dados PostgreSQL via DATABASE_URL (Railway injeta automaticamente)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ['DATABASE_URL'],
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email via Resend (API HTTPS - o Railway bloqueia SMTP nos planos Free/Hobby)
EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
ANYMAIL = {
    'RESEND_API_KEY': os.environ.get('RESEND_API_KEY', ''),
}
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'onboarding@resend.dev')

# Moderação por IA (stubs activos enquanto variáveis não estiverem definidas)
GOOGLE_CLOUD_CREDENTIALS = os.environ.get('GOOGLE_CLOUD_CREDENTIALS', '')
PERSPECTIVE_API_KEY      = os.environ.get('PERSPECTIVE_API_KEY', '')

# Segurança HTTPS
SECURE_PROXY_SSL_HEADER     = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT         = False
SESSION_COOKIE_SECURE       = True
CSRF_COOKIE_SECURE          = True
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD omitido intencionalmente: o preload é irreversível e
# exige submissão à lista HSTS Preload. Activar só depois do domínio estar estável.
