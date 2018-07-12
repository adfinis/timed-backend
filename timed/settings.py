import datetime
import os
import re

import environ
from pkg_resources import resource_filename

env = environ.Env()

django_root = environ.Path(__file__) - 2

ENV_FILE = env.str('DJANGO_ENV_FILE', default=django_root('.env'))
if os.path.exists(ENV_FILE):
    environ.Env.read_env(ENV_FILE)

# per default production is enabled for security reasons
# for development create .env file with ENV=dev
ENV = env.str('ENV', 'prod')


def default(default_dev=env.NOTSET, default_prod=env.NOTSET):
    """Environment aware default."""
    return default_prod if ENV == 'prod' else default_dev


# Database definition

DATABASES = {
    'default': {
        'ENGINE': env.str(
            'DJANGO_DATABASE_ENGINE',
            default='django.db.backends.postgresql_psycopg2'
        ),
        'NAME': env.str('DJANGO_DATABASE_NAME', default='timed'),
        'USER': env.str('DJANGO_DATABASE_USER', default='timed'),
        'PASSWORD': env.str(
            'DJANGO_DATABASE_PASSWORD', default=default('timed')
        ),
        'HOST': env.str('DJANGO_DATABASE_HOST', default='localhost'),
        'PORT': env.str('DJANGO_DATABASE_PORT', default='')
    }
}


# Application definition

DEBUG = env.bool('DJANGO_DEBUG', default=default(True, False))
SECRET_KEY = env.str('DJANGO_SECRET_KEY', default=default('uuuuuuuuuu'))
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=default(['*']))
HOST_PROTOCOL = env.str('DJANGO_HOST_PROTOCOL', default=default('http'))
HOST_DOMAIN = env.str('DJANGO_HOST_DOMAIN', default=default('localhost:4200'))


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.humanize',
    'multiselectfield',
    'django.forms',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'timed.employment',
    'timed.projects',
    'timed.tracking',
    'timed.reports',
    'timed.redmine',
    'timed.subscription',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'timed.urls'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [django_root('timed', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    # template backend for plain text (no escaping)
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [django_root('timed', 'templates')],
        'NAME': 'text',
        'APP_DIRS': True,
        'OPTIONS': {
            'autoescape': False,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'timed.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LOCALE_PATHS = [
    django_root('timed', 'locale')
]

LANGUAGE_CODE = 'en-US'

TIME_ZONE = env.str('DJANGO_TIME_ZONE', 'Europe/Zurich')

USE_I18N = True
USE_L10N = True

DATETIME_FORMAT = env.str('DJANGO_DATETIME_FORMAT', 'd.m.Y H:i:s')
DATE_FORMAT = env.str('DJANGO_DATE_FORMAT', 'd.m.Y')
TIME_FORMAT = env.str('DJANGO_TIME_FORMAT', 'H:i:s')

DECIMAL_SEPARATOR = env.str('DECIMAL_SEPARATOR', '.')

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = env.str('STATIC_URL', '/static/')
STATIC_ROOT = env.str('STATIC_ROOT', None)

# Rest framework definition

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_json_api.parsers.JSONParser',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_METADATA_CLASS':
        'rest_framework_json_api.metadata.JSONAPIMetadata',
    'EXCEPTION_HANDLER':
        'rest_framework_json_api.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework_json_api.pagination.PageNumberPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_json_api.renderers.JSONRenderer',
    ),
}

JSON_API_FORMAT_KEYS = 'dasherize'
JSON_API_FORMAT_TYPES = 'dasherize'
JSON_API_PLURALIZE_TYPES = True

APPEND_SLASH = False

# Authentication definition

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_LDAP_ENABLED = env.bool('DJANGO_AUTH_LDAP_ENABLED', default=False)
if AUTH_LDAP_ENABLED:
    AUTH_LDAP_USER_ATTR_MAP = env.dict(
        'DJANGO_AUTH_LDAP_USER_ATTR_MAP',
        default={
            'first_name': 'givenName',
            'last_name':  'sn',
            'email':      'mail'
        }
    )

    AUTH_LDAP_SERVER_URI = env.str('DJANGO_AUTH_LDAP_SERVER_URI')
    AUTH_LDAP_BIND_DN = env.str('DJANGO_AUTH_LDAP_BIND_DN', default='')
    AUTH_LDAP_BIND_PASSWORD = env.str(
        'DJANGO_AUTH_LDAP_BIND_PASSWORD', default=''
    )
    AUTH_LDAP_USER_DN_TEMPLATE = env.str('DJANGO_AUTH_LDAP_USER_DN_TEMPLATE')
    AUTHENTICATION_BACKENDS.insert(0, 'django_auth_ldap.backend.LDAPBackend')

AUTH_USER_MODEL = 'employment.User'

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=2),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # noqa
    },
]

# Email definition

EMAIL_CONFIG = env.email_url(
    'EMAIL_URL',
    default='smtp://localhost:25'
)
vars().update(EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = env.str(
    'DJANGO_DEFAULT_FROM_EMAIL',
    default('webmaster@localhost')
)

SERVER_EMAIL = env.str(
    'DJANGO_SERVER_EMAIL',
    default('root@localhost')
)


def parse_admins(admins):
    """
    Parse env admins to django admins.

    Example of DJANGO_ADMINS environment variable:
    Test Example <test@example.com>,Test2 <test2@example.com>
    """
    result = []
    for admin in admins:
        match = re.search('(.+) \<(.+@.+)\>', admin)
        if not match:
            raise environ.ImproperlyConfigured(
                'In DJANGO_ADMINS admin "{0}" is not in correct '
                '"Firstname Lastname <email@example.com>"'.format(admin))
        result.append((match.group(1), match.group(2)))
    return result


ADMINS = parse_admins(env.list('DJANGO_ADMINS', default=[]))


# Redmine definition (optional)

REDMINE_URL = env.str('DJANGO_REDMINE_URL', default='')
REDMINE_APIKEY = env.str('DJANGO_REDMINE_APIKEY', default='')
REDMINE_HTACCESS_USER = env.str('DJANGO_REDMINE_HTACCESS_USER', default='')
REDMINE_HTACCESS_PASSWORD = env.str(
    'DJANGO_REDMINE_HTACCESS_PASSWORD', default='')
REDMINE_SPENTHOURS_FIELD = env.int(
    'DJANGO_REDMINE_SPENTHOURS_FIELD', default=0)


# Work report definition

WORK_REPORT_PATH = env.str(
    'DJANGO_WORK_REPORT_PATH',
    default=resource_filename('timed.reports', 'workreport.ots')
)
