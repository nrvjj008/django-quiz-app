"""
Django settings for QuizPortal project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*j-70hb4aetufb_2wn89hn^aqjwueuoju&i1i$a9+@+11q+tjl'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Digital Ocean Spaces settings
AWS_ACCESS_KEY_ID = 'DO00JGNCWUJGGM4VH2VR'
AWS_SECRET_ACCESS_KEY = 'v5YX9uBxCxg5UZ0Q2Qcp62BPaivYZUVWManFgY7j/w4'
AWS_STORAGE_BUCKET_NAME = 'nirav-test'
AWS_S3_ENDPOINT_URL = 'https://nirav-test.nyc3.digitaloceanspaces.com'

#
# AWS_ACCESS_KEY_ID = 'DO00GT4NWXYK9QE44VNY'
# AWS_SECRET_ACCESS_KEY = '5oEq4GhteWrLgGqlR/i+ad8JfAwlR9ejKf8ejz7BbpY'
# AWS_STORAGE_BUCKET_NAME = 'nasaqstor1'
# AWS_S3_ENDPOINT_URL = 'https://nasaqstor1.ams3.digitaloceanspaces.com'
# Override Django's default file storage to use Spaces
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'info@nasaqlibrary.org'

EMAIL_HOST_PASSWORD = 'awxk jyzx pimf kpkz'
DEFAULT_FROM_EMAIL = 'info@nasaqlibrary.org'
# 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


# AWS_ACCESS_KEY_ID = 'minio-access-key'  # Replace with your MinIO access key
# AWS_SECRET_ACCESS_KEY = 'minio-secret-key'  # Replace with your MinIO secret key
# AWS_STORAGE_BUCKET_NAME = 'my-bucket'  # Replace with your bucket name
# AWS_S3_CUSTOM_DOMAIN = 'localhost:9000'
# AWS_S3_ENDPOINT_URL = 'http://localhost:9000'
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }
# AWS_DEFAULT_ACL = 'public-read'
# AWS_QUERYSTRING_AUTH = False
# AWS_S3_REGION_NAME = 'us-east-1'  # Region is not really important for MinIO

# # Use S3 as the default storage backend
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication',
    'ebooks',
    'storages',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',


]

ALLOWED_HOSTS = ['159.223.235.130', 'localhost', '127.0.0.1','nasaqlibrary.org']

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True  # This is for testing purposes.


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
# settings.py
# settings.py

# Existing settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
STATIC_URL = '/static/'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'

# New or modified settings
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # NEW LINE
STATICFILES_DIRS = [BASE_DIR / "static"]  # Make sure this directory exists in your project folder


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'QuizPortal.wsgi.application'
ROOT_URLCONF = 'QuizPortal.urls'

SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
