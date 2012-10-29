from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

class Addsubscription(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8000/"
        self.verificationErrors = []
    
    def test_addsubscription(self):
        driver = self.driver
        driver.get(self.base_url + "/admin/")
        driver.find_element_by_link_text("Subscriptions").click()
        self.assertEqual("Select subscription to change | Django site admin", driver.title)
        self.assertFalse(self.is_element_present(By.LINK_TEXT, "Test subscription"))
        driver.find_element_by_link_text("Add subscription").click()
        self.assertEqual("Add subscription | Django site admin", driver.title)
        # ERROR: Caught exception [Error: locator strategy either id or name must be specified explicitly.]
        # ERROR: Caught exception [Error: locator strategy either id or name must be specified explicitly.]
        # ERROR: Caught exception [Error: locator strategy either id or name must be specified explicitly.]
        # ERROR: Caught exception [Error: locator strategy either id or name must be specified explicitly.]
        # ERROR: Caught exception [Error: locator strategy either id or name must be specified explicitly.]
        self.assertEqual("Select subscription to change | Django site admin", driver.title)
        # ERROR: Caught exception [ERROR: Unsupported command [isTextPresent]]
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
