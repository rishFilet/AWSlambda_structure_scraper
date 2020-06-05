import utils


class SiteOne:
    def __init__(self):
        self.site = "site1"
        self.genre = ""
        self.slider_count = 0
        self.sel_obj = None

    # Here sliders are the channels
    def get_number_of_sliders(self, category):
        self.sel_obj = utils.create_scraper_object(
            self.site, category, "loader-inner")
        self.sel_obj.element_to_find = "slider"
        self.sel_obj.find_by_class = True
        slider_count = len(next(self.sel_obj.list_elements_on_page()))
        self.slider_count = slider_count
        self.sel_obj.find_by_class = False
        return slider_count

    def get_items_in_channels(self, category, slider_test=False):
        if slider_test:
            self.slider_count = sliders = 1
            item_count = 1
        else:
            sliders = self.get_number_of_sliders(category)
            item_count = 1
        site1_master_list = []
        channel_list = []
        for slider in range(sliders):
            slider += 1
            print("Scraping channel/slider {}".format(slider))
            items = item_count
            while True:
                if self.sel_obj is None:
                    self.sel_obj = utils.create_scraper_object(
                        self.site, category, "loader-inner",)
                self.sel_obj.find_by_id = True
                #self.genre = self.get_genre(self.sel_obj)
                try:
                    self.sel_obj.element_to_find = "slider_{0}_item{1}".format(
                        slider, items)
                    print("Finding elements {}".format(self.sel_obj.element_to_find))
                    element = next(self.sel_obj.list_elements_on_page())
                    text = element[0].get_attribute('textContent')
                    items += 1
                    channel_list.append(text)
                except:
                    print("Could not find any more slider item elements, found {} items for slider {}".format(items, slider))
                    break
            site1_master_list.append(channel_list)
        return site1_master_list        
        
    def get_genre(self, sel_obj_arg=None):
        if sel_obj_arg is None:
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

    def get_logos(self, category, slider_count=None):
        if slider_count is not None:
            self.slider_count = slider_count
        logo_links = []
        if self.sel_obj is None:
            self.sel_obj = utils.create_scraper_object(self.site, category)      
        self.sel_obj.find_by_id = True
        for channel in range(self.slider_count):
            self.sel_obj.element_to_find = "channels_{}".format(channel+1)
            list_gen = self.sel_obj.list_elements_on_page()
            scraped_data = next(list_gen)
            image_gen = self.sel_obj.list_elements_by_tag(scraped_data)
            image = next(image_gen)
            logo_url = image[0].get_attribute("src")
            logo_links.append(logo_url)
        return logo_links
