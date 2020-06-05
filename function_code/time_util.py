# /**
#  * @author Rishi Khan
#  * @email rishi.rkhan@gmail.com
#  * @create date 2020-05-30 12:21:01
#  * @modify date 2020-05-30 12:21:01
#  * @desc Handles all timezone conversions and converting times to ms
#  */

import logging
from datetime import datetime as dt
from pytz import timezone, reference
from pytz import all_timezones_set, common_timezones_set
from pytz.exceptions import UnknownTimeZoneError
from dateutil import tz


#This is a helper function to know which code needs to be input in the conversion function
def get_all_available_timezone_codes(search_string):
    for tz in all_timezones_set:
        if search_string in tz:
            yield tz
            break


def get_current_timezone():
    local_tz = reference.LocalTimezone().tzname(dt.now())
    try:
        current_timezone = timezone(local_tz)
    except UnknownTimeZoneError:
        logging.warning(
            ("Invalid code: {}, searching for alternative..".format(local_tz)))
        generator_tz = get_all_available_timezone_codes(local_tz)
        current_timezone = timezone(next(generator_tz))
    return current_timezone

def get_ymd():
    year, month, day = dt.now().strftime('%Y,%m,%d').split(',')
    return [year, month, day]

def get_hm():
    hour, minute = dt.now().strftime('%H,%M').split(',')
    return "{}:{}".format(hour, minute)

#call the function get_ymd() to get the year, month and day for this function
def convert_from_US_to_GMT(current_timezone, time_to_convert, ymd):
    year, month, day = ymd
    hour, minute = time_to_convert.split(':')
    time_to_convert_formatted = dt.strptime('{0}-{1}-{2} {3}:{4}:{5}.{6}'.format(year, month, day, hour, minute, 0, 0), '%Y-%m-%d %H:%M:%S.%f')
    GMT_timezone = timezone('GMT')
    return current_timezone.localize(time_to_convert_formatted).astimezone(GMT_timezone)

def convert_to_ms(formatted_time_to_convert):
    string_formatted_time = str(formatted_time_to_convert)
    time = string_formatted_time.split('+')[0]
    try:
        time_obj = dt.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        time_obj = dt.strptime(time, '%Y-%m-%d %H:%M:%S')
    ms = time_obj.timestamp()*1000
    return ms
