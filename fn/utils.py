import os
import json
import copy
from selenium_scraper import SeleniumScraper as sel_sc
from datetime import datetime as dt
import time_util as tu
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.common.exceptions import TimeoutException


def write_master_list_json(master_list_objects, filename, site):
    with open(os.path.join(os.getcwd(), "json_files", filename), 'w') as json_file:
        # json_data = dict()
        # json_data.update({site: master_list_objects})
        json.dump(master_list_objects, json_file)


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
        except TimeoutException:
            print("Could not find by id, trying by class")
            obj.find_by_id = False
            try:
                obj.click_element_on_page(
                    click_item, click_wait_for, by_class=True)
            except TimeoutException:
                print("Could not find element by class either")
                obj.find_by_class = False
    return obj


def convert_scraped_data_to_json_site_one(master_list, genre, logos):
    current_timezone = tu.get_current_timezone()
    ymd = tu.get_ymd()
    all_show_objects = []
    scraped_genre = genre
    for channel in master_list:
        try:
            channel_logo = logos[master_list.index(channel)]
        except IndexError:
            print("Could not find any logos")
            channel_logo = ''
        for time_slot in channel:
            item = time_slot.split('\n')
            title = item[2].replace('\t', '')
            if genre is None:
                scraped_genre = item[3].replace('\t', '')
            duration = item[5].replace('\xa0', '')
            json_format = copy.deepcopy(
                json_read_from_file('time_slot_template.json'))
            json_format["showName"] = title
            start_time, endtime = duration.split(
                '-')
            start_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, start_time, ymd)
            end_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, endtime, ymd)
            json_format["startTime"] = tu.convert_to_ms(start_time_GMT)
            json_format["endTime"] = tu.convert_to_ms(end_time_GMT)
            json_format["timestampKey"] = json_format["startTime"]
            json_format["type"] = scraped_genre
            json_format["channelLogo"] = channel_logo
            if channel_logo != '':
                json_format["channel"] = json_format["channelName"] = channel_logo.split(
                    '/')[::-1][0].split('.')[0]
            json_format["ttl"] = json_format["endTime"]
            json_format["duration"] = json_format["ttl"] - \
                json_format["timestampKey"]
            all_show_objects.append(json_format)
    return all_show_objects


def convert_scraped_data_to_json_site_two(shows_list):
    current_timezone = tu.get_current_timezone()
    ymd = tu.get_ymd()
    all_show_objects = []
    for show in shows_list:
        json_format = copy.deepcopy(
            json_read_from_file('time_slot_template.json'))
        json_format["showName"] = show["title"]
        start_time_GMT = tu.convert_from_US_to_GMT(
            current_timezone, show["start_time"], ymd)
        json_format["startTime"] = tu.convert_to_ms(start_time_GMT)
        json_format["duration"] = tu.convert_site_two_duration_to_ms(
            show["duration"])
        json_format["endTime"] = json_format["startTime"] + json_format["duration"]
        json_format["timestampKey"] = json_format["startTime"]
        json_format["type"] = show["genre"]
        json_format["channelLogo"] = show["channel_logo"]
        if show["channel_logo"] != '':
            json_format["channel"] = json_format["channelName"] = show["channel_logo"].split(
                '/')[::-1][0].split('.')[0]
        json_format["ttl"] = json_format["endTime"]
        all_show_objects.append(json_format)
    return all_show_objects

def convert_master_list_to_show_obj(master_list, site):
    channel_dict = {}
    show_objects = []
    show_list = master_list[site]
    # Sorting the items by channel
    for item in show_list:
        try:
            channel_dict[item["channel"]].append(item)
        except KeyError:
            channel_dict.update({item["channel"]:[]})
            channel_dict[item["channel"]].append(item)
    # Sorting each channel by start time
    for channel_name, item_array in channel_dict.items():
        sorted_channel = sort_channel_by_start_time(item_array)
        channel_dict[channel_name] = sorted_channel
    # Outputting the channel_dict into the desired showObject template
    for channel_name, item_array in channel_dict.items():
        for item in item_array:
            show_obj_format = copy.deepcopy(
                json_read_from_file("show_object_template.json"))
            show_obj_format["channelNameKey"] = item["channelName"]
            show_obj_format["timestampKey"] = item["timestampKey"]
            show_obj_format["startTime"] = item["startTime"]
            show_obj_format["endTime"] = item["endTime"]
            show_obj_format["type"] = item["type"]
            show_obj_format["rate"] = item["rate"]
            show_obj_format["ttl"] = item["ttl"]
            show_obj_format["channelLogo"] = item["channelLogo"]
            show_obj_format["channel"] = item["channel"]
            if item_array.index(item) == len(item_array) - 1:
                items = [item]
                show_obj_format["type2"] = item["type"]
            else:
                items = [item, item_array[item_array.index(item)+1]]
                show_obj_format["type2"] = item_array[item_array.index(
                    item)+1]["type"]
            show_obj_format["items"] = items
            show_objects.append(show_obj_format)
    return show_objects

# Currently not being used as the check for previous times is done by looking at the x position of the show elements
def filter_previous_times(current_time_formatted, end_time):
    if (current_time_formatted.hour == end_time.hour and current_time_formatted.minute < end_time.minute) or (current_time_formatted.day == end_time.day and current_time_formatted.hour < end_time.hour) or (current_time_formatted.month == end_time.month and current_time_formatted.day < end_time.day) or (current_time_formatted.day < end_time.day) or (current_time_formatted.hour < end_time.hour) or (current_time_formatted.minute < end_time.minute):
        return True
    else:
        return False

def sort_channel_by_start_time(arr):
    # TODO : Add tutorial on insertion sort
    for i in range(1, len(arr)):
        cursor = arr[i]
        pos = i-1

        while pos >= 0 and cursor["timestampKey"] < arr[pos]["timestampKey"]:
            arr[pos+1] = arr[pos]
            pos -= 1
        arr[pos+1] = cursor
    return arr

def sort_img_elements(arr):
    # Insertion sort algorithm
    for i in range(1, len(arr)):
        key = arr[i]
        j = i-1
        while j >= 0 and key.location['y'] < arr[j].location['y']:
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr
