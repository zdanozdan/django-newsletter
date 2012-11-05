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
        cls.wd = WebDriver(wait=10)
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
        """ Test whether login succeeded. """

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

    def test_addnewsletter(self):
        """ Test adding a newsletter. """

        # Make sure we're logged in first
        self.test_login()

        # Go to newsletters view
        self.wd.find(link_text='Newsletters').click()
        self.assertEquals(self.wd.title,
            "Select newsletter to change | Django site admin")

        self.wd.find(link_text='Add newsletter').click()
        self.assertEquals(self.wd.title,
            "Add newsletter | Django site admin")

        # Fill in the newsletter form
        form = self.wd.find(tag_name='form')
        form.find(name='title').send_keys('Test newsletter')
        form.find(name='email').send_keys('test@test.com')
        form.find(name='sender').send_keys('Test sender')

        # Submit the form
        form.submit()

        # Confirm save result
        self.assertTrue(self.wd.find(text_contains='added successfully'))
        self.assertTrue(self.wd.find(link_text='Test newsletter'))

    def test_addsubscription(self):
        """ Test adding a subscription to a newsletter. """

        # Make sure a newsletter is created
        self.test_addnewsletter()

        # Go back to main admin page
        self.wd.get('%s%s' % (self.live_server_url, '/admin/'))

        # Open add subscription form
        self.wd.find(link_text='Subscriptions').click()
        self.wd.find(link_text='Add subscription').click()

        self.assertEquals(self.wd.title,
            "Add subscription | Django site admin")

        # Fill in form
        form = self.wd.find(tag_name='form')
        form.find(name='name_field').send_keys('Test subscriber')
        form.find(name='email_field').send_keys('test_subscriber@test.com')

        form.find(name='newsletter').find(text='Test newsletter').click()
        form.find(name='subscribed').click()

        # Submit the form
        form.submit()

        # Confirm save results
        self.assertTrue(self.wd.find(text_contains='added successfully'))
        self.assertTrue(self.wd.find(link_text='Test subscriber'))

    def test_addmessage(self):
        """ Test adding a message to a newsletter. """

        # Make sure a newsletter is created
        self.test_addnewsletter()

        # Go back to main admin page
        self.wd.get('%s%s' % (self.live_server_url, '/admin/'))

        # Open add form
        self.wd.find(link_text='Messages').click()
        self.wd.find(link_text='Add message').click()

        self.assertEquals(self.wd.title,
            "Add message | Django site admin")

        # Fill in form
        form = self.wd.find(tag_name='form')
        form.find(name='title').send_keys('Test message')
        form.find(name='newsletter').find(text='Test newsletter').click()

        # Setup the first article
        form.find(name='articles-0-title').click().send_keys(
            'Test article title 1')
        form.find(name='articles-0-text').click().send_keys(
            'Test text 1')

        # Open hidden link tab and fill in URL
        form.find(id='fieldsetcollapser0').click()
        form.find(name='articles-0-url').click().send_keys(
            'http://www.google.com')

        # Setup the second article
        form.find(name='articles-1-title').click().send_keys(
            'Test article title 2')
        form.find(name='articles-1-text').click().send_keys(
            'Test text 2')

        # Submit the form
        form.submit()

        # Confirm save results
        self.assertTrue(self.wd.find(text_contains='added successfully'))
        self.assertTrue(self.wd.find(link_text='Test message'))
