from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common import exceptions as e
import time
import os


class SeleniumScraper:
    def __init__(self, url, search_query=None, search_id=None, wait_for_element=None, element_to_find=None, find_by_class=False, find_by_id=False):
        self.url = url
        self.search_query = search_query
        self.search_id = search_id
        self.wait_for_element = wait_for_element
        self.element_to_find = element_to_find
        self.find_by_class = find_by_class
        self.find_by_id = find_by_id
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--window-size=1280x1696')
        self.chrome_options.add_argument('--user-data-dir=/tmp/user-data')
        self.chrome_options.add_argument('--hide-scrollbars')
        self.chrome_options.add_argument('--enable-logging')
        self.chrome_options.add_argument('--log-level=0')
        self.chrome_options.add_argument('--v=99')
        self.chrome_options.add_argument('--single-process')
        self.chrome_options.add_argument('--data-path=/tmp/data-path')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--homedir=/tmp')
        self.chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
        self.chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        self.chrome_options.binary_location = "/opt/chrome/headless-chromium"
        self.webdriver = webdriver.Chrome(executable_path="/opt/chrome/chromedriver", chrome_options=self.chrome_options)
        # retrive url in headless browser
        self.webdriver.get(self.url)
        self.wait = WebDriverWait(self.webdriver, 10)

    def list_elements_on_page(self):
        # find search box
        if self.search_query is not None and self.search_query != "":
            search = self.webdriver.find_element_by_id(self.search_id)
            search.send_keys(self.search_query + Keys.RETURN)

        self.wait_element_appear(self.wait_for_element)

        if self.find_by_class:
            # element_to_find variable here is the class name or ID or xpath that is seen in the html inspection
            yield self.webdriver.find_elements_by_class_name(
                self.element_to_find)
        elif self.find_by_id:
            yield self.webdriver.find_elements_by_id(
                self.element_to_find)
        else:
            raise Exception("Specify if to find element by class or Id")

    def list_elements_by_tag(self, page_data=None):
        if page_data is None:
            self.wait_element_appear(self.wait_for_element)
            images = self.webdriver.find_elements_by_tag_name("img")
        else:
            images = page_data[0].find_elements_by_tag_name("img")

        yield images

    def wait_for_element_presence(self):
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.ID, self.wait_for_element)))
        except e.TimeoutException:
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CLASS_NAME, self.wait_for_element)))
            except e.TimeoutException:
                print("Could not locate element using presence by id nor class")

    def wait_element_appear(self, element, by_id=False, by_class=False, to_click=False, to_be_visible=False):
        if by_id or self.find_by_id:
            locator = By.ID
        elif by_class or self.find_by_class:
            locator = By.CLASS_NAME
        if to_click:
            self.wait.until(EC.element_to_be_clickable(
                (locator, element)))
        elif to_be_visible:
            self.wait.until(EC.visibility_of_element_located(
                (locator, element)))
        else:
            self.wait_for_element_presence()

    def wait_element_disappear(self, element, by_id=False, by_class=False):
        if by_id:
            locator = By.ID
        elif by_class:
            locator = By.CLASS_NAME
        self.wait.until(EC.invisibility_of_element_located(
            (locator, element)))

    def click_element_on_page(self, element_to_click, element_to_wait_on, by_id=False, by_class=False):
        if by_id:
            self.find_by_id = by_id
        elif by_class:
            self.find_by_class = by_class
        if self.find_by_id:
            self.wait_element_appear(
                element_to_click, by_id=True, to_click=True)
            self.webdriver.find_element_by_id(element_to_click).click()
        elif self.find_by_class:
            self.wait_element_appear(
                element_to_click, by_class=True, to_click=True)
            self.webdriver.find_element_by_class_name(element_to_click).click()
        else:
            raise Exception("Specify if to find element by class name or id")
        try:
            self.wait_element_appear(
                element_to_wait_on, by_id=True, to_be_visible=True)
        except e.TimeoutException:
            print("Could not find element: {}".format(element_to_wait_on))
        self.wait_element_disappear(element_to_wait_on, by_id=True)

    def stop_driver(self):
        self.webdriver.quit()
