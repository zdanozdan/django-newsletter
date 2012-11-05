from django.contrib.auth.models import User

# On Django 1.3 use the backported LiveServerTestCase from django-live-server
import django
if django.VERSION[0] == 1 and django.VERSION[1] == 3:
    from liveserver.test.testcases import LiveServerTestCase
else:
    from django.test import LiveServerTestCase

from webdriverplus import WebDriver


class SeleniumAdminTests(LiveServerTestCase):
    """ Selenium-based tests for the newsletter admin. """

    # Make sure we have our default templates available for testing
    fixtures = ['default_templates']

    # Generic timeout to avoid concurrency issues
    timeout = 5

    @classmethod
    def setUpClass(cls):
        cls.wd = WebDriver()
        super(SeleniumAdminTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.wd.quit()
        super(SeleniumAdminTests, cls).tearDownClass()

    def setUp(self):
        """ Make sure we've got a superuser available. """

        self.admin = \
            User.objects.create_user('test', 'test@testers.com', 'test')
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()

    def test_login(self):
        """ Attempt admin login. """

        self.wd.get('%s%s' % (self.live_server_url, '/admin/'))

        self.assertEqual("Log in | Django site admin",
            self.wd.title)

        username_input = self.wd.find(name="username")
        username_input.send_keys('test')
        password_input = self.wd.find(name="password")
        password_input.send_keys('test')

        self.wd.find(xpath='//input[@value="Log in"]').click()

        self.assertEqual("Site administration | Django site admin",
            self.wd.title)

    def test_modules(self):
        """ Test for presence of admin modules. """

        # Make sure we're logged in first
        self.test_login()

        self.wd.find(link_text='Newsletter')

        self.assertTrue(self.wd.find(link_text='Newsletter'))
        self.assertTrue(self.wd.find(link_text='E-mail templates'))
        self.assertTrue(self.wd.find(link_text='Messages'))
        self.assertTrue(self.wd.find(link_text='Newsletters'))
        self.assertTrue(self.wd.find(link_text='Submissions'))
        self.assertTrue(self.wd.find(link_text='Subscriptions'))
