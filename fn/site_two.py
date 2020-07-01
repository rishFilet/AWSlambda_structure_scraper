import time
import json
import itertools
import copy
import concurrent.futures
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, ElementNotVisibleException
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import utils as ut


class SiteTwo:
    def __init__(self, max_workers=60, batch_size=20):
        self.site = "site2"
        self.load_hits = 0
        self.unfiltered_len_shows = 0
        self.load_more_markers_list = []
        self.MAX_WORKERS = max_workers
        self.BATCH_SIZE = batch_size
        self.OSN_SKIP = ["SKH", "BBW", "BBA", "CAR", "CNB", "CT9", "FRE", "NHK", "MDN", "SNH", "SNA", "MMK", "RUS", "ALH", "ALQ",
                    "BBA", "FRA", "CTA", "DUH", "DR3", "SHS", "KTS", "TFC", "BRO", "COG", "ANC", "DZM", "DWR", "VIV", "MYX", "ARC", "AKS", "CIN", "LSN", "GMA", "GML", "GMN", "NET"]
        self.OSN_SKIP_SET = set(self.OSN_SKIP)

    def check_load_more_marker(self, show_box_no):
        load_times = 0
        for marker in self.load_more_markers_list:
            if show_box_no < marker:
                break
            else:
                load_times += 1
        return load_times

    def click_collect_site_data(self, show_box_no):
        dict_returned = False
        sel_obj = None
        driver = None
        while not dict_returned:
            try:
                if sel_obj is not None:
                    sel_obj.webdriver.quit()
                start = time.time()
                sel_obj = ut.create_scraper_object("site2")
                driver = sel_obj.webdriver
                wait = sel_obj.wait
                retry = 0
                while retry < 5:
                    try:
                        show_box = None
                        show_box_retry = 0
                        show_box_xpath = f"(//div[contains(@class, 'tv-show-title-ch-1')])[{show_box_no+1}]"
                        while show_box is None:
                            try:
                                self.load_more_button(sel_obj, show_box_xpath, self.check_load_more_marker(show_box_no))
                                driver = sel_obj.webdriver
                                wait = sel_obj.wait
                                # wait.until(EC.presence_of_element_located(
                                #     (By.XPATH, show_box_xpath)),  message=f"Timeout looking for {show_box_xpath}")
                                show_box = driver.find_element_by_xpath(
                                    show_box_xpath)
                            except Exception as ne:
                                print(
                                    f"Could not find show box {show_box_no} : {ne}")
                                show_box_retry += 1
                                if show_box_retry == 10:
                                    raise TimeoutException(
                                        f"Show boxes not found on page load for {show_box_no}")
                                driver.refresh()
                                print(
                                    f"Refreshing page on retry: {int(show_box_retry)} for show {show_box_no}")

                        title = show_box.get_attribute(
                            'textContent').strip()
                        if title == '':
                            raise ValueError(
                                f"Title for {show_box_no} is empty")
                        else:
                            ActionChains(driver).move_to_element(
                                show_box).click().perform()
                    # #             # TODO : Add logging here

                        try:
                            wait.until(EC.visibility_of_element_located((
                                By.CLASS_NAME, "tv-show-popup-detailes")), message=f"Timeout waiting for popup details to appear after first click attempt")
                        except TimeoutException as te:
                            driver.refresh()
                            self.load_more_button(
                                sel_obj, show_box_xpath, self.check_load_more_marker(show_box_no))
                            # wait.until(EC.presence_of_element_located((
                            #     By.XPATH, show_box_xpath)), message=f"Timeout looking for {show_box_xpath} on second click")
                            driver.execute_script(
                                "arguments[0].click();", driver.find_element_by_xpath(
                                    show_box_xpath))
                            wait.until(EC.visibility_of_element_located((
                                By.CLASS_NAME, "tv-show-popup-detailes")), message=f"Timeout waiting for popup details to appear after second click attempt")
                        popup = driver.find_element_by_class_name(
                            "tv-show-popup-detailes")
                        if popup.size['height'] and popup.size['width'] != 0:
                            details = []
                            details_retry = 0
                            while not details:
                                details = driver.find_elements_by_xpath(
                                    "//div[@class='tv-show-popup-detailes']/div/span")
                                details_retry += 1
                                if details_retry > 20:
                                    raise NoSuchElementException(
                                        "Unable to find DETAILS text")
                            *details_text_list, = genre, day, start_time, duration = details[1].text, details[2].text, details[3].text, details[5].text
                            if '' in details_text_list:
                                raise ValueError(
                                    f"Details missing information for {show_box_no}")
                            channel_logos = driver.find_element_by_css_selector(
                                'div.logo-pop-wrapper > img')
                            try:
                                channel_logo = channel_logos.get_attribute(
                                    "src")
                            except:
                                raise ValueError(
                                    f"Channel Logo information cannot be located for {show_box_no}")
                            info_dict = {"title": title, "genre": genre, "day": day,
                                         "start_time": start_time, "duration": duration, "channel_logo": channel_logo}
                            print(
                                f"Returning info for show_box {show_box_no} : Time - {time.time() - start}")
                            driver.quit()
                            dict_returned = True
                            return info_dict
                        else:
                            raise NoSuchElementException(
                                f"Could not find show box {show_box_no} after popup did not appear when clicked")
                    except IndexError:
                        driver.refresh()
                        retry += 1
                        print(f"Retry : {retry} for show Box: {show_box_no}")
                        print(
                            "Unable to locate element details or channel logo in popup")
                    except Exception as e:
                        try:
                            driver.refresh()
                        except WebDriverException:
                            sel_obj = ut.create_scraper_object("site2")
                            driver = sel_obj.webdriver
                            wait = sel_obj.wait
                        retry += 1
                        print(f"Retry : {retry} for show Box: {show_box_no}")
                        print(f"Could not get popup data on due to : {e}")
                #         # TODO : Add logging here
            except (WebDriverException, TimeoutException) as e:
                print(
                    f"Caught driver timeout exception as {e}, Retrying for show {show_box_no}")


    def load_more_button(self, sel_obj, xpath_to_find, times_to_click_load):
            load_btn = sel_obj.webdriver.find_element_by_id("loadMoreBtn")
            click = 0
            while click < times_to_click_load:
                sel_obj.wait.until(EC.element_to_be_clickable(
                    (By.ID, "loadMoreBtn")))
                while True:
                    try:
                        load_btn.click()
                        break
                    except WebDriverException as we:
                        #print("Waiting for load to be clickable..")
                        pass

                if click == times_to_click_load - 1:
                    try:
                        sel_obj.wait.until(EC.presence_of_element_located(
                            (By.XPATH, xpath_to_find)))
                        break
                    except TimeoutException as te:
                        print(f"Clicked load but could not locate element {te}. Trying again...")
                        click = 0
                click += 1


    def load_all_shows(self):
        sel_obj = ut.create_scraper_object("site2")
        #before_load_list_len = len(self.get_all_show_boxes_on_screen(sel_obj))
        program_wrapper = sel_obj.webdriver.find_element_by_id(
            "programWrapper")
        before_load_list = program_wrapper.find_elements_by_class_name(
            "tv-show-title-ch-1")
        before_load_list_len = len(before_load_list)
        sel_obj.wait_element_appear(
            "loadMoreBtn", by_id=True, to_click=True)
        load_more_btn = sel_obj.webdriver.find_element_by_id(
            "loadMoreBtn")
        self.load_more_markers_list.append(before_load_list_len)
        start_time = time.time()
        while True:
            try:
                print("Loading more shows......")
                load_more_btn.click()
                time.sleep(0.5)
                self.load_hits += 1
                after_load_list = program_wrapper.find_elements_by_class_name(
                    "tv-show-title-ch-1")
                self.load_more_markers_list.append(len(after_load_list))
            except ElementNotVisibleException:
                print("Finished loading all shows")
                break
            #     pass
            # if before_load_list_len == len(after_load_list):
            #     break
            # else:
            #     before_load_list_len = len(after_load_list)
        print(f"Total Loads: {self.load_hits}")
        duration = time.time() - start_time
        print(self.load_more_markers_list)
        print(f"Finished loading all shows in {duration} seconds")
        return after_load_list, sel_obj
    
    def check_for_skipped_channels(self, show):
        
        parent = show.find_element_by_xpath('..')
        channel_name = parent.get_attribute("class")
        channel = channel_name.strip()[-3:]
        if channel in self.OSN_SKIP_SET:
            return show

    def get_filtered_show_box_nos(self):
         # Load all shows
        all_loaded_shows, sel_obj = self.load_all_shows()
        self.unfiltered_len_shows = len(all_loaded_shows)
        show_box_nos = list(range(len(all_loaded_shows)))
        print(f"Unfiltered number of shows: {len(show_box_nos)}")

        start = time.time()
        all_loaded_shows_iterator = (self.check_for_skipped_channels(
            show) for show in all_loaded_shows)
        show_box_nos_to_remove = [[i for i, value in enumerate(all_loaded_shows) if value == returned_show] for returned_show in all_loaded_shows_iterator if returned_show is not None]
        unpacked_show_nos_to_remove = [
            item for sublist in show_box_nos_to_remove for item in sublist]
        show_box_nos = list(set(show_box_nos)-set(unpacked_show_nos_to_remove))
        sel_obj.stop_driver()
        print(f"Filtered number of shows: {len(show_box_nos)} in {time.time()-start}")
        return show_box_nos

    def get_items_in_channels(self, test=False, start=None, end=None):
        # self.load_all_shows()
        shows_list = []
        shows_to_scrape = self.get_filtered_show_box_nos()
        # sel_obj = ut.create_scraper_object("site2")
        # all_show_boxes = sel_obj.webdriver.find_elements_by_class_name(
        #     "tv-show-title-ch-1")
        # all_show_boxes = ut.sort_img_elements(all_show_boxes)
        if test and start is None and end is None:
            if start is None:
                start = 0
            if end is None and end > start:
                end = round(0.2*len(shows_to_scrape))
            else:
                end = len(shows_to_scrape)

        if start > end or end > len(shows_to_scrape):
            end = len(shows_to_scrape)
        shows_to_scrape = shows_to_scrape[start:end]

        start_time = time.time()
        print(f"Scraping for {len(shows_to_scrape)} shows from {start} to {end}")
        show_box_no_iterator = iter(shows_to_scrape)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {executor.submit(self.click_collect_site_data, show_box_no): show_box_no
                       for show_box_no in itertools.islice(show_box_no_iterator, self.BATCH_SIZE)}
            while futures:
                done, _ = concurrent.futures.wait(
                    futures, return_when=concurrent.futures.FIRST_COMPLETED)
                if len(futures) < 5:
                    print(f"futures left: {len(futures)} : {futures}")
                    print(f"Remaining: {_}")
                for fut in done:
                    try:
                        result = fut.result()
                        if result not in shows_list:
                            shows_list.append(result)
                        futures.pop(fut)
                    except concurrent.futures.TimeoutError as e:
                        print(f"When appending shows_list in futures: {e}")
                for show_box_no in itertools.islice(show_box_no_iterator, len(done)):
                    fut = executor.submit(
                        self.click_collect_site_data, show_box_no)
                    futures[fut] = show_box_no

        duration = time.time() - start_time
        print(
            f"Scrapped site2 for {len(shows_list)} shows from {start} to {end} in {duration} seconds")
        # sel_obj.webdriver.quit()
        return shows_list


    def get_all_show_boxes_on_screen(self, sel_obj):
        retry = 0
        while retry < 5:
            try:
                sel_obj.wait.until(EC.visibility_of_element_located(
                    (By.CLASS_NAME, "all-shows-time-area")))
                break
            except TimeoutException as e:
                retry += 1
                print(
                    f"{e} : Getting all show boxes on screen. Trying again on retry {retry}")
        return sel_obj.webdriver.find_elements_by_class_name("tv-show-title-ch-1")

# NOTE: i don't need to resinstatniate the find elements, all boxes will be moved when using the actions and will be updated. Try to remove doing the webdriver find elements again and just seeing if allboxes updates after doing the swipe.
