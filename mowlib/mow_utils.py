import sys
sys.path.append('.')
import os
import re
import errno
from datetime import datetime, date, timedelta
import time
from pytz import timezone
import pytz
import json
import config
import serial
import camowra

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
        if exceptn.errno == erno.EEXIST:
            pass
        else:
            raise

# The idea was that an image "set" is taken, all of which
# share a certain time, i.e. you can view the set of images from, say, Tuesday 
# morning, and there are maybe 4 photos in that set. They should all share the
# same time data. I moved most of this over to the database entry's timestamp, will
# eliminate this later
class date_strings():
    def __init__(self):
        self.date_time = datetime.utcnow()
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

# Simple function to determine if it is past noon. I don't think I'm using this
# anymore and will probably remove it
def is_morning():
    schedule = config.schedule()
    date_time = datetime.utcnow()
    if date_time.hour < schedule.noon.hour:
        return 1
    else:
        return 0

# This class initializes the schedule times in the config into datetime objects, 
# and provides a method for converting them to UTC when sent to the frontend
class schedule:
    def __init__(self):
        self.date_time = datetime.today()
        self.today = datetime.strftime(self.date_time.date(), '%Y-%m-%d ')
        self.noon = datetime.strptime(self.today + config.noon, config.time_format)
        self.morning_start = datetime.strptime(self.today + config.morning_start,
                config.time_format)
        self.morning_end = datetime.strptime(self.today + config.morning_end,
                config.time_format)
        self.evening_start = datetime.strptime(self.today + config.evening_start,
                config.time_format)
        self.evening_end = datetime.strptime(self.today + config.evening_end,
                config.time_format)

    # Saw this on StackOverflow at
    # http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
    # by user Joe Holloway. Thanks, Joe!
    def local_to_utc(self, datetime):
        local_tz = tz.tzlocal()
        utc_tz = tz.tzutc()
        datetime = datetime.replace(tzinfo=local_tz)
        return datetime.astimezone(utc_tz)

def get_status(db, schedule):
    status = {}
    dbresponse = db.select('nomnoms',
            what='time_stamp',
            limit=1,
            order='time_stamp DESC')
    dbresponse = list(dbresponse)
    # If there are no DB entries at least set some date for the last feeding time
    if dbresponse.__len__() < 1:
        last_nomtime_time = datetime(2000, 1, 1, 0, 0)
    else:
        last_nomtime_time = dbresponse[0].time_stamp
    now = schedule.date_time
    status['last_nomtime'] = last_nomtime_time

    # Assume that the feeder is locked. The logic below will unlock it only under 
    # specific circumstances
    status['lock'] = 1

    # Start out with the morning, which is calculated as any time "today" earlier
    # than the end of the morning feeding time
    if (now < schedule.morning_end):
        status['tod'] = 'morning'
        if last_nomtime_time > schedule.morning_start:
            # The cat has been fed for the morning
            status['fed'] = 1
            status['next_nom_time'] = schedule.evening_end
            status['next_nom_start'] = schedule.evening_start
        else:
            # The cat has not yet been fed
            status['fed'] = 0
            status['next_nom_time'] = schedule.morning_end
            status['next_nom_start'] = schedule.evening_start
            if now > schedule.morning_start:
                # The cat has not yet been fed AND the morning feeding time has
                # started
                status['lock'] = 0
    else:
        status['tod'] = 'evening'
        if last_nomtime_time > schedule.evening_start:
            # The cat has been fed
            status['fed'] = 1
            status['next_nom_time'] = schedule.morning_end + timedelta(days=1)
            status['next_nom_start'] = schedule.morning_start + timedelta(days=1)
        else:
            # The cat has not been fed yet
            status['fed'] = 0
            status['next_nom_time'] = schedule.evening_end
            status['next_nom_start'] = schedule.evening_start
            if now > schedule.evening_start:
                # The cat has not yet been fed AND the evening feeding time has
                # started
                status['lock'] = 0
    return status

def feed_cycle(data, schedule, date_strings):
    if 'feed' in data:
        db = config.db
        img_root = config.img_root
        status = get_status(db, schedule)
        nomnom_result = {}

        #if status['lock']:
            #return json.dumps({'result': 'locked'})

        img_folder = make_imgfolder_string(img_root, date_strings)

        if not os.path.exists(img_folder):
            mkdir_p(img_folder)

        # Make an entry in the nomnoms table for this feeding. The images will
        # be associated with this record
        nomnom_id = db.insert('nomnoms')

        #Feed the baileycat
        print('Activating feeder...')
        #activate_feeder()

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
