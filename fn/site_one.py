import utils
import os


class SiteOne:
    def __init__(self):
        self.site = "site1"
        self.genre = ""
        self.slider_count = 0
        self.sel_obj = None
        
        
    def get_items_in_channels(self, category, slider_test=False):
        site1_master_list = []
        slider = 0
        self.sel_obj = utils.create_scraper_object(
            self.site, category, "loader_inner")
        slider_count = self.sel_obj.webdriver.find_elements_by_xpath(
            "//*[contains(@id, 'ruler_channels_')]")
        while True:
            if slider_test and slider > 1:
                break
            slider += 1
            channel_list = []
            try:
                self.sel_obj.wait_element_appear("slider_{}".format(
                    slider), by_id=True, to_be_visible=True)
                print("Scraping channel/slider {}".format(slider))
                self.sel_obj.find_by_id = True
                print("Finding elements for slider {}".format(slider))
                element_items = self.sel_obj.webdriver.find_elements_by_xpath(
                    "//*[contains(@id, 'slider_{}_item')]".format(slider))
                now_or_upcoming_count = 0
                for item in element_items:
                    text = item.get_attribute('textContent')
                    now_or_upcoming_count += 1
                    channel_list.append(text)
                print(
                    "Collected {} items for channel/slider {}".format(now_or_upcoming_count, slider))
                site1_master_list.append(channel_list)
            except:
                if slider < len(slider_count)-1:
                    print(f"-------> Slider empty or missing data for {slider}")
                else:
                    print("No more sliders")
                    break
        return site1_master_list

    def get_current_page(self, sel_obj_arg=None, category=None):
        if sel_obj_arg is None:
            if self.sel_obj is None:
                self.sel_obj = utils.create_scraper_object(self.site, category)
            sel_obj = self.sel_obj
        else:
            sel_obj = sel_obj_arg
        sel_obj.find_by_class = True
        sel_obj.element_to_find = "category_item_selected"
        element = next(sel_obj.list_elements_on_page())
        try:
            if type(element) is list and len(element) != 0:
                text = element[0].text
            else:
                text = element.text
        except:
            print("Could not find element on page")
        sel_obj.find_by_class = False
        return text

    # When getting the logos, originally channels_<digit> was used as the xpath.
    # Since it was xpath contains, it would find channels_1 and channels 10, 11, 12 etc
    # To solve this, it would find all imgs based on the xpath and sort them based on y location
    # using the insert sort (since its less than 64 elements).
    def get_logos(self, category):
        logo_links = []
        self.sel_obj = utils.create_scraper_object(
            self.site, category, "loader_inner")
        try:
            elements = self.sel_obj.webdriver.find_elements_by_xpath(
                "//*[contains(@id, 'channels_')]/div/div/div/div[@class='centered']/a/img")
            sorted_elements = utils.sort_img_elements(elements)
            for img in sorted_elements:
                if img.location["y"] > 0 and img.location["x"] > 0:
                    logo_url = img.get_attribute("src")
                    logo_links.append(logo_url)
        except:
            print("Could not find element(s) with that xpath ")
        return logo_links
