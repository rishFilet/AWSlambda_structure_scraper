import os
import json
import copy
from selenium_scraper import SeleniumScraper as sel_sc
from datetime import datetime as dt
from datetime import timedelta as tdelt
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
    retry = 0
    while retry < 3:
        obj = sel_sc(url=data["url"], search_query=data["search_query"], search_id=data["search_box_id"],
                    wait_for_element=data["wait_for_element"], element_to_find=data["element_to_find"])
        try:
            obj.wait_for_element_presence()
            if click_item is not None:
                try:
                    obj.click_element_on_page(click_item, click_wait_for, by_id=True)
                    break
                except TimeoutException:
                    print("Could not find by id, trying by class")
                    obj.find_by_id = False
                    try:
                        obj.click_element_on_page(
                            click_item, click_wait_for, by_class=True)
                        break
                    except TimeoutException:
                        obj.find_by_class = False
                        raise TimeoutException(
                            "Could not find element by class either")
            else:
                break
        except Exception as e:
            print(e)
        retry += 1
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
        for index, time_slot in enumerate(channel):
            item = time_slot.split('\n')
            title = item[2].replace('\t', '')
            if genre is None:
                scraped_genre = item[3].replace('\t', '')
            duration = item[5].replace('\xa0', '')
            json_format = copy.deepcopy(
                json_read_from_file('time_slot_template.json'))
            json_format["showName"] = title
            start_time, end_time = duration.split(
                '-')
            start_hr = start_time.split(":")[0].strip()
            end_hr = end_time.split(":")[0].strip()
            if int(start_hr) > int(end_hr) and index == 0:
                start_ymd = tu.get_ymd_minus_day()
            else:
                start_ymd = ymd
            start_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, start_time, start_ymd)
            # This is a check to see if the show goes past midnight and thus 00 might be seen as less than 23, so we need to add day +1
            if int(start_hr) > int(end_hr) and index > 0:
                end_ymd = tu.get_ymd_plus_day()
            else:
                end_ymd = ymd
            end_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, end_time, end_ymd)
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
            #if dt.fromtimestamp(json_format["ttl"]/1000) > dt.fromtimestamp(dt.now().timestamp()/1000):
            all_show_objects.append(json_format)
    return all_show_objects


def convert_scraped_data_to_json_site_two(shows_list):
    current_timezone = tu.get_current_timezone()
    ymd = tu.get_ymd()
    all_show_objects = []
    day = dt.today().strftime('%A')
    for show in shows_list:
        if show["day"].replace(':', '') == day:
            json_format = copy.deepcopy(
                json_read_from_file('time_slot_template.json'))
            json_format["showName"] = show["title"]
            start_time_GMT = tu.convert_from_US_to_GMT(
                current_timezone, show["start_time"], ymd)
            json_format["startTime"] = tu.convert_to_ms(start_time_GMT)
            json_format["duration"] = tu.convert_site_two_duration_to_ms(
                show["duration"])
            json_format["endTime"] = json_format["startTime"] + \
                json_format["duration"]
            json_format["timestampKey"] = json_format["startTime"]
            json_format["type"] = show["genre"]
            json_format["channelLogo"] = show["channel_logo"]
            if show["channel_logo"] != '':
                json_format["channel"] = json_format["channelName"] = show["channel_logo"].split(
                    '/')[::-1][0].split('.')[0]
            json_format["ttl"] = json_format["endTime"]
            all_show_objects.append(json_format)
    return all_show_objects

#TODO: Filter by start time vs now time
def convert_master_list_to_show_obj(master_list, site):
    channel_dict = {}
    show_objects = []
    show_list = master_list[site]
    # Sorting the items by channel
    for item in show_list:
        try:
            channel_dict[item["channel"]].append(item)
        except KeyError:
            channel_dict.update({item["channel"]: []})
            channel_dict[item["channel"]].append(item)
    # Sorting each channel by start time
    for channel_name, item_array in channel_dict.items():
        remove_dupes_channel_dict = check_start_end_time_dupes_chronology(
            item_array, channel_name)
        sorted_channel = sort_channel_by_start_time(remove_dupes_channel_dict)
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
        while pos >= 0 and dt.fromtimestamp(cursor["timestampKey"]/1000) < dt.fromtimestamp(arr[pos]["timestampKey"]/1000):
            arr[pos+1] = arr[pos]
            pos -= 1
        arr[pos+1] = cursor
        dupe_items_to_raise_exception = [x for x in arr if arr.count(x) > 2]
        if dupe_items_to_raise_exception:
            raise Exception(
                f"More than 2 Duplicates exist in site 1 data {dupe_items_to_raise_exception}")
    return arr

def check_start_end_time_dupes_chronology(dict_arr, channel):
    timestampkeys = [info["timestampKey"] for info in dict_arr]
    ttl = [info["ttl"] for info in dict_arr]
    dupe_tsks = [x for x in timestampkeys if timestampkeys.count(x) > 1]
    dupe_ttls = [x for x in ttl if ttl.count(x) > 1]
    if dupe_tsks > 0:
        print(
            f"Duplicates exist in timestampkey for channel: {channel}\n Original List: {dupe_tsks}\n Set List: {set(dupe_tsks)}")
        dupe_list_w_one_of = list(set(dupe_tsks))
        duped_channel = []
        for duped_show_timestampkey in dupe_list_w_one_of:
            dupe_count = 0
            for show in dict_arr:
                if show["timestampKey"] == duped_show_timestampkey:
                    duped_channel.append(show)
                    dupe_count += 1
                if dupe_count > 1:
                    dict_arr.remove(show) 
            print(f"Duplicated channels: {duped_channel}")
        #raise Exception(f"Duplicates exist in timestampkey for channel: {channel}\n Original List: {dupe_tsks}\n Set List: {set(dupe_tsks)}")
    if dupe_ttls:
        print(
            f"Duplicates exist in ttl for channel: {channel}\n Original List: {dupe_ttls}\n Set List: {set(dupe_ttls)}")
        dupe_list_w_one_of = list(set(dupe_ttls))
        duped_channel = []
        for duped_show_ttls in dupe_list_w_one_of:
            dupe_count = 0
            for show in dict_arr:
                if show["ttl"] == duped_show_ttls:
                    duped_channel.append(show)
                    dupe_count += 1
                if dupe_count > 1:
                    dict_arr.remove(show)
            print(f"Duplicated channels: {duped_channel}")
    #    raise Exception(
    #         f"Duplicates exist in ttl for channel: {channel}\n Original List: {dupe_ttls}\n Set List: {set(dupe_ttls)}")
    for i, value in enumerate(ttl):
        if dt.fromtimestamp(timestampkeys[i]/1000) > dt.fromtimestamp(ttl[i]/1000):
            raise Exception(f"End time is less than start time for {channel}. Start: {timestampkeys[i]}, End: {value}")
        if dt.fromtimestamp(timestampkeys[i]/1000) < dt.fromtimestamp(0) or dt.fromtimestamp(ttl[i]/1000) < dt.fromtimestamp(0):
            raise Exception(
                f"Start or End time is negative {channel}. Start: {timestampkeys[i]}, End: {value}")
    return dict_arr

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

def remove_dupe_dicts(list_to_check):
    list_of_strings = [json.dumps(d, sort_keys=True)
                        for d in list_to_check]
    #Using the set here will cause issues with order of the elements
    list_of_strings = set(list_of_strings)
    return [json.loads(s) for s in list_of_strings]
