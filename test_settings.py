DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_extensions',
    'newsletter',
)

ROOT_URLCONF = 'test_urls'

STATIC_URL = '/static/'

SITE_ID = 1

TEMPLATE_DIRS = ('test_templates', )

