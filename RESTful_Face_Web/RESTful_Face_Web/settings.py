"""
Django settings for RESTful_Face_Web project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os, datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'jm%z1b74z0b4x&jwwx3@nr4oe_8wuxp0+u-7=%o%%19wb00rq*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Admin User
ADMIN_NAME = 'admin'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'company',
    'rest_framework.authtoken',
    'expiring_token',
    'rest_framework_swagger',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'RESTful_Face_Web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
]

WSGI_APPLICATION = 'RESTful_Face_Web.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

MYSQL_USER = 'RESTful_Face_API'
MYSQL_PASSWORD = 'jt1330'
MYSQL_HOST = 'localhost'
DB_SETTINGS_BASE_DIR = os.path.join(BASE_DIR, 'RESTful_Face_Web/runtime_db/database_settings')
DATABASES = {
    #'default': {
    #    'ENGINE': 'django.db.backends.mysql',
    #    'USER': 'RESTful_Face_API',
    #    'PASSWORD': 'jt1330',
    #     'NAME': 'Admin',
    #    'HOST': 'localhost',
    #    'PORT': '3306',
    #},
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }

}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/" + datetime.datetime.now().strftime("%y%m%d"),
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'company': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}

# default authentication class
REST_FRAMEWORK = {
   'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework.authentication.BasicAuthentication',
       'expiring_token.authentication.ExpiringTokenAuthentication',
   ),
}
# The default expiring time of tokens
EXPIRING_TOKEN_LIFESPAN = datetime.timedelta(days=1)

# swagger doc settings
SWAGGER_SETTINGS = {
    "exclude_namespace": [],
    "api_version": '0.1',
    'api_path': "/",
    "enabled_methods": [
        'get',
        'post',
        'put',
        'delete',
    ],
    "api_key": '',
    "is_authentication": False,
    "is_superuser": False,
}


from .runtime_db import load_database
#from .runtime_db.runtime_database import MySQLManager
#myDBManager = MySQLManager()
from .runtime_db.runtime_database import SQLiteManager
myDBManager = SQLiteManager()
