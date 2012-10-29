from django.contrib.auth.models import User

from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait


class SeleniumAdminTests(LiveServerTestCase):
    """ Selenium-based tests for the newsletter admin. """

    # Make sure we have our default templates available for testing
    fixtures = ['default_templates']

    # Generic timeout to avoid concurrency issues
    timeout = 5

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(SeleniumAdminTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumAdminTests, cls).tearDownClass()

    def setUp(self):
        """ Make sure we've got a superuser available. """
        admin = User.objects.create_user('test', 'test@testers.com', 'test')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

    def test_login(self):
        """ Attempt admin login. """

        self.selenium.get('%s%s' % (self.live_server_url, '/admin/'))

        self.assertEqual("Log in | Django site admin",
            self.selenium.title)

        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('test')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('test')

        # Wait until the response is received
        WebDriverWait(self.selenium, self.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))

        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()

        self.assertEqual("Site administration | Django site admin",
            self.selenium.title)
