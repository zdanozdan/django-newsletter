DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}

# On Django 1.3, use on-disk database for testing as sharing the database
# with test thread is not supported there
import django
if django.VERSION[0] == 1 and django.VERSION[1] == 3:
    DATABASES['default']['TEST_NAME'] = 'database.sqlite'

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

