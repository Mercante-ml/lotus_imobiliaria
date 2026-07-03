"""
Django settings for lotus_imobiliaria project.
"""

from pathlib import Path
import environ
import os

env = environ.Env()

# --- CONFIGURAÇÃO DO ENVIRON ---
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=True)


# --- CHAVES DO .ENV ---
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'
ALLOWED_HOSTS = ['*']

# --- CONFIGURAÇÃO CLOUDFLARE (PROXY) ---
CSRF_TRUSTED_ORIGINS = [
    f'https://{os.environ.get("ROOT_DOMAIN", "dsprime.org")}', 
    f'https://*.{os.environ.get("ROOT_DOMAIN", "dsprime.org")}'
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- APPS MULTI-TENANT ---
SHARED_APPS = [
    'django_tenants',  # obrigatório ser o primeiro
    'clientes',        # app que vai gerenciar os tenants
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Allauth deve estar no schema publico para login centralizado
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
]

TENANT_APPS = [
    # Apps específicos de cada imobiliária
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'django.contrib.humanize',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "clientes.Client"
TENANT_DOMAIN_MODEL = "clientes.Domain"

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'lotus_imobiliaria.urls'
PUBLIC_SCHEMA_URLCONF = 'lotus_imobiliaria.urls_public'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- BACKENDS DE AUTENTICAÇÃO ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

WSGI_APPLICATION = 'lotus_imobiliaria.wsgi.application'


# --- DATABASE ---
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# --- VALIDAÇÃO DE SENHA ---
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# --- INTERNACIONALIZAÇÃO ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- STATIC & MEDIA ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Celery Configuration
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Redis Cache for Tracking Progress
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/2"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- EMAIL ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' 
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='contato@dsprime.net')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False


# --- ALLAUTH CONFIG ---
# SITE_ID = 1

# Login apenas com email + senha
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'   # 🔑 confirmação de email obrigatória

# Desabilita a proteção contra enumeração no signup para mostrar erro na tela
ACCOUNT_PREVENT_ENUMERATION = False

# Desativa login por código (passwordless)
ACCOUNT_LOGIN_BY_CODE_ENABLED = False
ACCOUNT_LOGIN_BY_CODE_REQUIRED = False

# Customizações
ACCOUNT_FORMS = {
    'signup': 'core.forms.CustomSignupForm',
}

ACCOUNT_SESSION_REMEMBER = True
LOGIN_URL = '/contas/login/'
LOGIN_REDIRECT_URL = '/login-redirect/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Lotus Imobiliária] '
SOCIALACCOUNT_LOGIN_ON_GET = True

# Compartilhar Sessão de Login entre todos os subdomínios (SSO)
ROOT_DOMAIN = os.environ.get('ROOT_DOMAIN', '.dsprime.org')
if not ROOT_DOMAIN.startswith('.'):
    ROOT_DOMAIN = f'.{ROOT_DOMAIN}'
SESSION_COOKIE_DOMAIN = ROOT_DOMAIN
CSRF_COOKIE_DOMAIN = ROOT_DOMAIN

# --- STRIPE CONFIG ---
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_PRICE_BOUTIQUE = env('STRIPE_PRICE_BOUTIQUE', default='')
STRIPE_PRICE_CORPORATE = env('STRIPE_PRICE_CORPORATE', default='')
STRIPE_PRICE_10GB = env('STRIPE_PRICE_10GB', default='')
STRIPE_PRICE_50GB = env('STRIPE_PRICE_50GB', default='')
