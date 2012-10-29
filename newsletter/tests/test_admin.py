from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait


class SeleniumAdminTests(LiveServerTestCase):

    fixtures = ['default_templates']

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(SeleniumAdminTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumAdminTests, cls).tearDownClass()

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
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))

        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()

        self.assertEqual("Site administration | Django site admin",
            self.selenium.title)
