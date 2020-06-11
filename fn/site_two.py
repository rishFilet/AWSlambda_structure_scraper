import utils as ut
from selenium.common.exceptions import WebDriverException, ElementNotVisibleException, TimeoutException
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import copy


class SiteTwo:
    def __init__(self):
        self.site = "site2"
        self.source = None
        self.scrape_action = 0
        self.duplicate_check_list = self.current_list = self.previous_list = []
        self.all_show_boxes = None
        self.sel_obj = ut.create_scraper_object(
            "site2")
        self.end_scrape = False

    def get_items_in_channels(self, test=False):
        self.load_all_shows()
        shows_list = []
        skipped_eleemnts = []
        skipped_elements = 0
        if test:
            ten_percent_of_list = round(0.01*len(self.all_show_boxes))
            self.all_show_boxes = self.all_show_boxes[:ten_percent_of_list]
        # clicking on each box to get the information after retrieving a filtered list if displayed
        for show_box in self.all_show_boxes:
            try:
                try:
                    show_box.click()
                except (ElementNotVisibleException, WebDriverException):
                    ActionChains(self.sel_obj.webdriver).move_to_element(
                        show_box).click().perform()
                    # TODO : Add logging here
                self.sel_obj.wait.until(EC.presence_of_element_located(
                    (By.CLASS_NAME, "tv-show-popup-detailes")))
                popup_result = self.sel_obj.webdriver.find_element_by_class_name(
                    "modal-body")
                # This wait for xpath needs to be here to allow the text on the popup to appear. Without it, then it will show the dict as having empty strings
                self.sel_obj.wait.until(EC.text_to_be_present_in_element(
                    (By.XPATH, "//div[@class='tv-show-popup-detailes']/div/span"), "Genre:"))
                title = popup_result.find_element_by_xpath(
                    "//div[@class='tv-popup-h2']").text
                details = popup_result.find_elements_by_xpath(
                    "//div[@class='tv-show-popup-detailes']/div/span")
                channel_logos = popup_result.find_elements_by_xpath(
                    "//div[@class='modal-body']/div/div/img")
                channel_logo = channel_logos[0].get_attribute("src")
                genre = details[1].text
                startTime = details[3].text
                duration = details[5].text
                info_dict = {"title": title, "genre": genre,
                             "start_time": startTime, "duration": duration, "channel_logo": channel_logo}
                shows_list.append(info_dict)
                self.current_list.append(info_dict)
                # This two line combination of finding by css selector and executing javascript works for clicking hidden elements
                close = self.sel_obj.webdriver.find_elements_by_css_selector(
                    ".close")
                self.sel_obj.webdriver.execute_script(
                    "$(arguments[0]).click();", close)
                self.sel_obj.wait.until(EC.invisibility_of_element(
                    (By.CLASS_NAME, "tv-popup-h2")))
                self.source = show_box
            except WebDriverException as e:
                skipped_elements += 1
                skipped_eleemnts.append(show_box)
                # TODO : Add logging here
        set_shows = self.remove_dupe_dicts(shows_list)
        print("Skipped {} shows that could not be clicked out of {} shows".format(
            skipped_elements, len(self.all_show_boxes)))
        return set_shows

    def load_all_shows(self):
        before_load_list_len = len(self.get_all_show_boxes_on_screen())
        while True:
            try:
                self.sel_obj.wait_element_appear(
                    "loadMoreBtn", by_id=True, to_click=True)
                print("Loading more shows......")
                self.sel_obj.webdriver.find_element_by_id(
                    "loadMoreBtn").click()
                time.sleep(2)
                after_load_list = self.get_all_show_boxes_on_screen()
            except TimeoutException:
                print("Could not find load more button, trying again..")
                pass
            if before_load_list_len == len(after_load_list):
                break
            else:
                before_load_list_len = len(after_load_list)
        print("Finished loading all shows")
        self.all_show_boxes = after_load_list

    def get_all_show_boxes_on_screen(self):
        retry = 0
        while retry < 5:
            try:
                self.sel_obj.wait.until(EC.visibility_of_element_located(
                    (By.CLASS_NAME, "all-shows-time-area")))
                break
            except TimeoutException as e:
                print(e + " Trying again on retry {}".format(retry))
                retry += 1
        return self.sel_obj.webdriver.find_elements_by_class_name("tv-show-title-ch-1")

    def remove_dupe_dicts(self, list_to_check):
        list_of_strings = [json.dumps(d, sort_keys=True)
                           for d in list_to_check]

        list_of_strings = set(list_of_strings)
        return [json.loads(s) for s in list_of_strings]
# NOTE: i don't need to resinstatniate the find elements, all boxes will be moved when using the actions and will be updated. Try to remove doing the webdriver find elements again and just seeing if allboxes updates after doing the swipe.
