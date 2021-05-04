import os
import re

import environ
import sentry_sdk
from pkg_resources import resource_filename
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env()

django_root = environ.Path(__file__) - 2

ENV_FILE = env.str("DJANGO_ENV_FILE", default=django_root(".env"))
if os.path.exists(ENV_FILE):  # pragma: no cover
    environ.Env.read_env(ENV_FILE)

# per default production is enabled for security reasons
# for development create .env file with ENV=dev
ENV = env.str("ENV", "prod")


def default(default_dev=env.NOTSET, default_prod=env.NOTSET):
    """Environment aware default."""
    return default_prod if ENV == "prod" else default_dev


# Database definition

DATABASES = {
    "default": {
        "ENGINE": env.str(
            "DJANGO_DATABASE_ENGINE", default="django_prometheus.db.backends.postgresql"
        ),
        "NAME": env.str("DJANGO_DATABASE_NAME", default="timed"),
        "USER": env.str("DJANGO_DATABASE_USER", default="timed"),
        "PASSWORD": env.str("DJANGO_DATABASE_PASSWORD", default=default("timed")),
        "HOST": env.str("DJANGO_DATABASE_HOST", default="localhost"),
        "PORT": env.str("DJANGO_DATABASE_PORT", default=""),
    }
}


# Application definition

DEBUG = env.bool("DJANGO_DEBUG", default=default(True, False))
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default=default("uuuuuuuuuu"))
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=default(["*"]))
HOST_PROTOCOL = env.str("DJANGO_HOST_PROTOCOL", default=default("http"))
HOST_DOMAIN = env.str("DJANGO_HOST_DOMAIN", default=default("localhost:4200"))


INSTALLED_APPS = [
    "timed.apps.TimedAdminConfig",
    "django.contrib.humanize",
    "multiselectfield",
    "django.forms",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "djmoney",
    "mozilla_django_oidc",
    "django_prometheus",
    "timed.employment",
    "timed.projects",
    "timed.tracking",
    "timed.reports",
    "timed.redmine",
    "timed.subscription",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "timed.urls"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
TEMPLATES = [
    # default: needed for django-admin
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [django_root("timed", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
    # template backend for plain text (no escaping)
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "NAME": "text",
        "APP_DIRS": True,
        "OPTIONS": {
            "autoescape": False,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "timed.wsgi.application"


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LOCALE_PATHS = [django_root("timed", "locale")]

LANGUAGE_CODE = "en-US"

TIME_ZONE = env.str("DJANGO_TIME_ZONE", "Europe/Zurich")

USE_I18N = True
USE_L10N = True

DATETIME_FORMAT = env.str("DJANGO_DATETIME_FORMAT", "d.m.Y H:i:s")
DATE_FORMAT = env.str("DJANGO_DATE_FORMAT", "d.m.Y")
TIME_FORMAT = env.str("DJANGO_TIME_FORMAT", "H:i:s")

DECIMAL_SEPARATOR = env.str("DECIMAL_SEPARATOR", ".")

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = env.str("STATIC_URL", "/static/")
STATIC_ROOT = env.str("STATIC_ROOT", "/app/static")

# Cache

CACHES = {
    "default": {
        "BACKEND": env.str(
            "CACHE_BACKEND",
            default="django_prometheus.cache.backends.locmem.LocMemCache",
        ),
        "LOCATION": env.str("CACHE_LOCATION", ""),
    }
}

# Rest framework definition

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PARSER_CLASSES": ("rest_framework_json_api.parsers.JSONParser",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication",
    ),
    "DEFAULT_METADATA_CLASS": "rest_framework_json_api.metadata.JSONAPIMetadata",
    "EXCEPTION_HANDLER": "rest_framework_json_api.exceptions.exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework_json_api.pagination.JsonApiPageNumberPagination",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework_json_api.renderers.JSONRenderer",),
    "TEST_REQUEST_RENDERER_CLASSES": (
        "rest_framework_json_api.renderers.JSONRenderer",
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.MultiPartRenderer",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "vnd.api+json",
}

JSON_API_FORMAT_FIELD_NAMES = "dasherize"
JSON_API_FORMAT_TYPES = "dasherize"
JSON_API_PLURALIZE_TYPES = True

APPEND_SLASH = False

# Authentication

AUTH_USER_MODEL = "employment.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "timed.authentication.TimedOIDCAuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},  # noqa
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},  # noqa
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"  # noqa
    },
]

# OIDC

OIDC_DEFAULT_BASE_URL = env.str(
    "DJANGO_OIDC_DEFAULT_BASE_URL",
    default="http://timed.local/auth/realms/timed/protocol/openid-connect",
)
OIDC_OP_AUTHORIZATION_ENDPOINT = env.str(
    "DJANGO_OIDC_OP_AUTHORIZATION_ENDPOINT", default=f"{OIDC_DEFAULT_BASE_URL}/auth"
)

OIDC_OP_TOKEN_ENDPOINT = env.str(
    "DJANGO_OIDC_OP_TOKEN_ENDPOINT", default=f"{OIDC_DEFAULT_BASE_URL}/token"
)
OIDC_OP_USER_ENDPOINT = env.str(
    "DJANGO_OIDC_OP_USER_ENDPOINT", default=f"{OIDC_DEFAULT_BASE_URL}/userinfo"
)
OIDC_OP_JWKS_ENDPOINT = env.str(
    "DJANGO_OIDC_OP_JWKS_ENDPOINT", default=f"{OIDC_DEFAULT_BASE_URL}/certs"
)

OIDC_RP_CLIENT_ID = env.str("DJANGO_OIDC_RP_CLIENT_ID", default="timed-public")
OIDC_RP_CLIENT_SECRET = env.str("DJANGO_OIDC_RP_CLIENT_SECRET", default=None)

OIDC_VERIFY_SSL = env.bool("DJANGO_OIDC_VERIFY_SSL", default=default(False, True))
OIDC_RP_SIGN_ALGO = env.str("DJANGO_OIDC_RP_SIGN_ALGO", default="RS256")

OIDC_CREATE_USER = env.bool("DJANGO_OIDC_CREATE_USER", default=True)
OIDC_USERNAME_CLAIM = env.str(
    "DJANGO_OIDC_USERNAME_CLAIM", default=default("preferred_username", "sub")
)
OIDC_EMAIL_CLAIM = env.str("DJANGO_OIDC_EMAIL_CLAIM", default="email")
OIDC_FIRSTNAME_CLAIM = env.str("DJANGO_OIDC_FIRSTNAME_CLAIM", default="given_name")
OIDC_LASTNAME_CLAIM = env.str("DJANGO_OIDC_LASTNAME_CLAIM", default="family_name")
# time in seconds
OIDC_BEARER_TOKEN_REVALIDATION_TIME = env.int(
    "DJANGO_OIDC_BEARER_TOKEN_REVALIDATION_TIME", default=60
)

# introspection endpoint for checking confidential client authentication
OIDC_CHECK_INTROSPECT = env.bool("DJANGO_OIDC_CHECK_INTROSPECT", default=True)
OIDC_OP_INTROSPECT_ENDPOINT = env.str(
    "DJANGO_OIDC_OP_INTROSPECT_ENDPOINT",
    default=f"{OIDC_DEFAULT_BASE_URL}/token/introspect",
)
OIDC_RP_INTROSPECT_CLIENT_ID = env.str(
    "DJANGO_OIDC_RP_INTROSPECT_CLIENT_ID", default="timed-confidential"
)
OIDC_RP_INTROSPECT_CLIENT_SECRET = env.str(
    "DJANGO_OIDC_RP_INTROSPECT_CLIENT_SECRET", default=None
)

# admin page after completing server-side authentication flow
LOGIN_REDIRECT_URL = env.str(
    "DJANGO_OIDC_ADMIN_LOGIN_REDIRECT_URL", default=default("http://timed.local/admin/")
)

# allow / disallow login with local user / password
ALLOW_LOCAL_LOGIN = env.bool("DJANGO_ALLOW_LOCAL_LOGIN", default=True)

if not ALLOW_LOCAL_LOGIN:  # pragma: no cover
    APPLICATION_BACKENDS = ["timed.authentication.TimedOIDCAuthenticationBackend"]

# Email definition

EMAIL_CONFIG = env.email_url("EMAIL_URL", default="smtp://localhost:25")
vars().update(EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = env.str(
    "DJANGO_DEFAULT_FROM_EMAIL", default("webmaster@localhost")
)

SERVER_EMAIL = env.str("DJANGO_SERVER_EMAIL", default("root@localhost"))
EMAIL_EXTRA_HEADERS = {"Auto-Submitted": "auto-generated"}


def parse_admins(admins):
    """
    Parse env admins to django admins.

    Example of DJANGO_ADMINS environment variable:
    Test Example <test@example.com>,Test2 <test2@example.com>
    """
    result = []
    for admin in admins:
        match = re.search(r"(.+) \<(.+@.+)\>", admin)
        if not match:
            raise environ.ImproperlyConfigured(
                'In DJANGO_ADMINS admin "{0}" is not in correct '
                '"Firstname Lastname <email@example.com>"'.format(admin)
            )
        result.append((match.group(1), match.group(2)))
    return result


ADMINS = parse_admins(env.list("DJANGO_ADMINS", default=[]))


# Redmine definition (optional)

REDMINE_URL = env.str("DJANGO_REDMINE_URL", default="")
REDMINE_APIKEY = env.str("DJANGO_REDMINE_APIKEY", default="")
REDMINE_HTACCESS_USER = env.str("DJANGO_REDMINE_HTACCESS_USER", default="")
REDMINE_HTACCESS_PASSWORD = env.str("DJANGO_REDMINE_HTACCESS_PASSWORD", default="")
REDMINE_SPENTHOURS_FIELD = env.int("DJANGO_REDMINE_SPENTHOURS_FIELD", default=0)


# Work report definition

WORK_REPORT_PATH = env.str(
    "DJANGO_WORK_REPORT_PATH",
    default=resource_filename("timed.reports", "templates/workreport.ots"),
)

WORK_REPORTS_EXPORT_MAX_COUNT = env.int(
    "DJANGO_WORK_REPORTS_EXPORT_MAX_COUNT", default=0
)

REPORTS_EXPORT_MAX_COUNT = env.int("DJANGO_REPORTS_EXPORT_MAX_COUNT", default=0)

# Tracking: Report fields which should be included in email (when report was
# changed during verification)
TRACKING_REPORT_VERIFIED_CHANGES = env.list(
    "DJANGO_TRACKING_REPORT_VERIFIED_CHANGES",
    default=["task", "comment", "not_billable"],
)

# Sentry error tracking
if env.str("DJANGO_SENTRY_DSN", default=""):  # pragma: no cover
    sentry_sdk.init(
        dsn=env.str("DJANGO_SENTRY_DSN", default=""),
        integrations=[DjangoIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=env.float("DJANGO_SENTRY_TRACES_SAMPLE_RATE", default=1.0),
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=env.bool("DJANGO_SENTRY_SEND_DEFAULT_PII", default=True),
        # By default the SDK will try to use the SENTRY_RELEASE
        # environment variable, or infer a git commit
        # SHA as release, however you may want to set
        # something more human-readable.
        # release="myapp@1.0.0",
    )
