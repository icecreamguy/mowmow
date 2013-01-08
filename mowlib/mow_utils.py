import sys
sys.path.append('.')
import os
import re
import errno
from datetime import datetime, date, timedelta
import time
import json
import config
from config import nom_cycles
import serial
import camowra
from web import utils

# Two capture groups - the date string and the number of recent photos. Only one
# group is active at a time. Example strings:
# Date request for 2012/11/06 - /photos/date/2012-11-26
# Request for the 6 most recent photos - /photos/recent/6
date_regex_string = ("/photo/((?:date/(?:19|20\d\d)-(?:0[1-9]|1[012])-(?:0[1-9]|[12"
                     "][0-9]|3[01]))$|recent/\d{1,2}$)")

photo_path_regex_string = ("date/((?:19|20\d\d)-(?:0[1-9]|1[012])-(?:0[1-9]|[12][0-"
                           "9]|3[01]))$|recent/(\d{1,2})$")

# Saw this on stackoverflow from user tzot - 
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
# nice clean way to recursively make directories
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exceptn:
        if exceptn.errno == errno.EEXIST:
            pass
        else:
            raise

# Utility class for convenient date strings and date objects
class date_strings():
    def __init__(self):
        self.date_time = datetime.now()
        self.current_time = self.date_time.strftime("%H_%M_%S")
        self.current_day = self.date_time.strftime("%d")
        self.current_month = self.date_time.strftime("%m")
        self.current_year = self.date_time.strftime("%Y")
        self.mysql_date_string = (self.current_year + "-" + self.current_month +
                "-" + self.current_day)

def make_imgfolder_string(img_root, date_strings):
    #folder structure is image root/yyyy/mm/dd/image1.png
    return os.path.join(img_root, date_strings.current_year,
            date_strings.current_month, date_strings.current_day)

def folder_string_from_mysql(mysql_date_string):
    return re.sub('-','/',str(mysql_date_string)) 

def obj_from_photo_path(path):
    request = {}
    photo_path_regex = re.compile(photo_path_regex_string)
    groups = photo_path_regex.match(path).groups()
    # Put the results in a small dictionary based on what matched
    if groups[1]:
        request = {'recent': groups[1]}
    else:
        request = {'date': groups[0]}
    return request

# Needed to extend the JSONEncoder to support MySQL dates. Pretty much straight
# from the python documentation
class webpy_db_encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M %Z')
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, obj)

def strphour(hour_string):
    return datetime.strptime(hour_string, '%H:%M').time()

def get_status():

    status = utils.storage()
    status.fed = False
    status.fed_today = False
    status.lock = True
    # This variable will keep track of whether or not the next feeding time occurs
    # today, or tomorrow
    status.next_start_day = 'today'
    # List to be used in next-feed-time calculations
    nom_times_left = []

    db_last_nom = list(config.db.select('nomnoms',
        what='time_stamp',
        limit=1,
        order='time_stamp DESC'
    ))

    # If there are no DB entries at least set some date for the last feeding time
    if db_last_nom.__len__() < 1:
        status.last_nomtime = datetime(2000, 1, 1, 0, 0)
    else:
        status.last_nomtime = db_last_nom[0].time_stamp

    time_now = datetime.today().time()
    day_now = datetime.today().date()

    if status.last_nomtime.date() == day_now:
        status.fed_today = True

    print('schedule: time_now is ' + time_now.strftime('%H:%M:%S'))
    print('schedule: last_nomtime was ' + str(status.last_nomtime))
    print(status.last_nomtime).time()

    # Main loop here - figure out if we're in a feed cycle, if we are then has the 
    # cat already been fed? When does it get fed next?
    for cycle_name in nom_cycles.iterkeys():
        start = nom_cycles[cycle_name]['start']
        end = nom_cycles[cycle_name]['end']
        print('schedule: checking if in ' +\
                cycle_name + ' cycle, starts at ' +\
                start + ' and ends at ' + end
        )
        if time_now > strphour(start) and time_now < strphour(end):
            # it's after the cycle start and before the cycle end
            print('in ' + cycle_name)
            if status.last_nomtime.time() > strphour(start) and status.fed_today:
                # The last feeding was today and the time was after this cycle start
                # time
                print('schedule: already fed')
                status.fed = True
            else:
                # Cat hasn't been fed today, or was fed at an earlier cycle
                print('schedule: not fed')
                status.lock = False
        else:
            print('schedule: not in ' + cycle_name)

        # Already in the loop, why not build this list of remaining nom_times here?
        if strphour(start) > time_now:
            nom_times_left.append(cycle_name)

    if len(nom_times_left) == 0:
        # There are no more nom times left today, set the next_start_day to
        # tomorrow, and set the nom_times_left list to the original nom_cycles list
        status.next_start_day = 'tomorrow'
        nom_times_left = list(nom_cycles.iterkeys())
    # At this point, if we sort the list of nom_times_left on the start time, the 
    # first position in the list should be the next cycle the feeder will unlock,
    # and the next_start_day variable should be accurate.
    nom_times_left.sort(key=lambda cycle_name:
        nom_cycles[cycle_name]['start']
    )
    next_cycle = nom_times_left[0]
    status.next_nom_start = nom_cycles[next_cycle]['start']
    status.next_nom_end = nom_cycles[next_cycle]['end']
    print(status)
    return status

# Saw this on StackOverflow at
# http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
# by user Joe Holloway. Thanks, Joe!
    def local_to_utc(self, datetime):
        local_tz = tz.tzlocal()
        utc_tz = tz.tzutc()
        datetime = datetime.replace(tzinfo=local_tz)
        return datetime.astimezone(utc_tz)

def feed_cycle(data, date_strings):
    if 'feed' in data:
        db = config.db
        img_root = config.img_root
        dir_base = config.dir_base
        status = get_status()
        nomnom_result = {}

        if status['lock']:
            return json.dumps({'result': 'locked'})

        img_folder = make_imgfolder_string(img_root, date_strings)
        print(img_folder)
        img_folder_abs = os.path.join(dir_base, img_folder)

        if not os.path.exists(img_folder_abs):
            mkdir_p(img_folder_abs)

        # Make an entry in the nomnoms table for this feeding. The images will
        # be associated with this record
        nomnom_id = db.insert('nomnoms')

        #Feed the baileycat
        print('Activating feeder...')
        activate_feeder()

        # Fire up the camera!
        camera = camowra.init_camera()

        # Grab a set of photos
        camowra.generate_image_set(4, img_folder, date_strings, 3, camera,
                nomnom_id)

        # delete the camera object
        del(camera)

        return json.dumps(nomnom_result)

# This function is ugly as hell right now, but I have an actual need to feed Bailey
# on vacation, so i'm leaving it as-is for now
def activate_feeder():
    serial_port = serial.Serial('/dev/ttyUSB0')

    serial_port.write('\xff\x01\x01')
    time.sleep(1)
    serial_port.write('\xff\x01\x00')
    time.sleep(1)
    serial_port.write('\xff\x01\x01')
    time.sleep(1)
    serial_port.write('\xff\x01\x00')
