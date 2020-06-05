import os
import json
import copy
from selenium_scraper import SeleniumScraper as sel_sc
from datetime import datetime as dt
import time_util as tu
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from site_one import SiteOne as s1

def write_master_list_json(master_list_objects, filename):
    with open(os.path.join(os.getcwd(), "json_files", filename), 'w') as json_file:
        json_data = dict()
        json_data.update({"master_list": master_list_objects})
        json.dump(json_data, json_file)


def json_read_from_file(filename):
    with open(os.path.join(os.getcwd(), "json_files", filename)) as json_file:
        data = json.load(json_file)
        return data


def get_scrape_data(site):
    return json_read_from_file("scrape_queries.json")[site]


def create_scraper_object(site, click_item=None, click_wait_for=None):
    data = get_scrape_data(site)
    obj = sel_sc(url=data["url"], search_query=data["search_query"], search_id=data["search_box_id"],
                 wait_for_element=data["wait_for_element"], element_to_find=data["element_to_find"])
    obj.wait_for_element_presence()
    if click_item is not None:
        try:
            obj.click_element_on_page(click_item, click_wait_for, by_id=True)
        except:
            print("Could not find by id, trying by class")
            obj.find_by_id = False
            try:
                obj.click_element_on_page(click_item, click_wait_for, by_class=True)
            except:
                print("Could not find element by class either")
                obj.find_by_class = False
    return obj


def convert_scraped_data_to_json(master_list, genre, logos):
    current_timezone = tu.get_current_timezone()
    ymd = tu.get_ymd()
    all_show_objects = []
    for channel in master_list:
        try:
            channel_logo = logos[master_list.index(channel)]
        except IndexError:
            print("Could not find any logos")
            channel_logo = ''
        for time_slot in channel:
            item = time_slot.split('\n')
            title = item[2].replace('\t', '')
            duration = item[5].replace('\xa0', '')
            json_format = copy.deepcopy(
                json_read_from_file('time_slot_template.json'))
            json_format["showName"] = json_format["channelName"] = title
            start_time, endtime = duration.split(
                '-')
            start_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, start_time, ymd)
            end_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, endtime, ymd)
            json_format["startTime"] = tu.convert_to_ms(start_time_GMT)
            json_format["endTime"] = tu.convert_to_ms(end_time_GMT)
            json_format["timestampKey"] = json_format["startTime"]
            json_format["type"] = genre
            json_format["channelLogo"] = channel_logo
            if channel_logo != '':
                json_format["channel"] = channel_logo.split('/')[::-1][0].split('.')[0]
            json_format["ttl"] = json_format["endTime"]
            json_format["duration"] = json_format["ttl"] - json_format["timestampKey"]
            ctf = tu.convert_from_US_to_GMT(current_timezone, tu.get_hm(), ymd)
            if filter_previous_times(ctf, end_time_GMT):
                all_show_objects.append(json_format)
            else:
                print("Skipping previous show")
    return all_show_objects


def filter_previous_times(current_time_formatted, end_time):
    if (current_time_formatted.hour == end_time.hour and current_time_formatted.minute < end_time.minute) or (current_time_formatted.day == end_time.day and current_time_formatted.hour < end_time.hour) or (current_time_formatted.month == end_time.month and current_time_formatted.day < end_time.day) or (current_time_formatted.day < end_time.day) or (current_time_formatted.hour < end_time.hour) or (current_time_formatted.minute < end_time.minute):
        return True
    else:
        return False
