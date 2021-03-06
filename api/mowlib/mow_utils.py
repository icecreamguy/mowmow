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
from urllib2 import URLError

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

def get_status(auth_token):
    status = utils.storage()
    status.fed = False
    status.fed_today = False
    status.lock = True
    if (auth_token):
        status.user_name, status.user_id = auth_user(auth_token)
    else:
        status.user_name = status.user_id = None
    # This variable will keep track of whether or not the next feeding time occurs
    # today, or tomorrow
    status.next_start_day = 'today'
    # Cycle name will be "Unscheduled" when called outside of feeding times
    status.cycle_name = 'unscheduled'
    # List to be used in next-feed-time calculations
    nom_times_left = []

    db_last_nom = list(config.db.query('SELECT nomnoms.time_stamp,name '
        'FROM nomnoms,users '
        'WHERE nomnoms.user_id = users.id '
        'ORDER BY nomnoms.time_stamp DESC '
        'LIMIT 1'))

    # If there are no DB entries at least set some date for the last feeding time
    if db_last_nom.__len__() < 1:
        status.last_nomtime = datetime(2000, 1, 1, 0, 0)
    else:
        status.last_nomtime = db_last_nom[0].time_stamp
        status.last_feeder = db_last_nom[0].name

    time_now = datetime.today().time()
    day_now = datetime.today().date()

    if status.last_nomtime.date() == day_now:
        status.fed_today = True

    # Main loop here - figure out if we're in a feed cycle, if we are then has the 
    # cat already been fed? When does it get fed next?
    for cycle_name in nom_cycles.iterkeys():
        start = nom_cycles[cycle_name]['start']
        end = nom_cycles[cycle_name]['end']
        if time_now > strphour(start) and time_now < strphour(end):
            # it's after the cycle start and before the cycle end
            status.cycle_name = cycle_name
            if status.last_nomtime.time() > strphour(start) and status.fed_today:
                # The last feeding was today and the time was after this cycle start
                # time
                status.fed = True
            else:
                # Cat hasn't been fed today, or was fed at an earlier cycle
                status.lock = False

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
    status.tz = time.tzname[0]
    return status

# Saw this on StackOverflow at
# http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
# by user Joe Holloway. Thanks, Joe!
    def local_to_utc(self, datetime):
        local_tz = tz.tzlocal()
        utc_tz = tz.tzutc()
        datetime = datetime.replace(tzinfo=local_tz)
        return datetime.astimezone(utc_tz)

def feed_cycle(data, date_strings, auth_token, external=False):
    if 'feed' in data:
        db = config.db
        img_root = config.img_root
        dir_base = config.dir_base
        status = get_status(auth_token)
        if external:
            # This is an externally triggered cycle, use the system account and
            # unlock the feeder
            status.user_id = 1
            status.user_name = 'System'
            status.lock = False
        if not status.user_name:
            return json.dumps({'result': 'unauthorized'})
        nomnom_result = {}

        if status['lock']:
            return json.dumps({'result': 'locked'})

        img_folder = make_imgfolder_string(img_root, date_strings)
        img_folder_abs = os.path.join(dir_base, img_folder)

        if not os.path.exists(img_folder_abs):
            mkdir_p(img_folder_abs)

        # Make an entry in the nomnoms table for this feeding. The images will
        # be associated with this record
        nomnom_id = db.insert('nomnoms',
                cycle_name=status.cycle_name,
                user_id = status.user_id)

        #Feed the baileycat
        activate_feeder()

        # Fire up the camera!
        camera = camowra.init_camera()

        # Grab a set of photos
        try:
            camowra.generate_image_set(4, img_folder, date_strings, 3, camera,
                status.cycle_name, nomnom_id)
        except URLError:
            print("Can't communicate with camera!")
            db.delete('nomnoms',
                where='id = $nomnom_id',
                vars={'nomnom_id':nomnom_id}
            )
            return json.dumps({'result': 'cam_error'})
        finally:
            if (config.camera_type == 'usb'):
                # delete the camera object
                del(camera)

        return json.dumps(nomnom_result)

def activate_feeder():
    print("Activating feeder...")

    if config.ignore_hardware:
        print("Ignore hardware set, aborting")
        return

    serial_port = serial.Serial(
            config.serial_port,
            baudrate=config.serial_baudrate
    )

    # Wait for the Arduino to reinitialize
    time.sleep(2)

    # CMDMessenger is running on the Arduino, with the feeding routine in
    # slot 4
    serial_port.write('4;')

    return

# Function to validate and create a new account
def create_account(account_data):
    db = config.db
    account_creation_state = {'message': [], 'problems': 0}

    for field, val in account_data.iteritems():
        if not len(val):
            account_creation_state['message'].append('%s cannot be blank' % field)

    # ONly allow letters, numbers, and spaces in the name field
    username_regex = ("^[\w\s]{0,70}$")

    # Check if it's a valid username
    if not re.compile(username_regex).match(account_data.name_field):
        account_creation_state['message'].append('Invalid username. Letters,'
            'numbers, spaces only')

    # Email regex from regular-expressions.info/email.html
    email_regex = ("[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
                   "@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-"
                   "z0-9])?")

    # Check if it's a valid email address
    if not re.compile(email_regex).match(account_data.email_field.lower()):
        account_creation_state['message'].append('Invalid email format')

    # Make sure the passords match
    if account_data.pass_field != account_data.pass_confirm_field:
        account_creation_state['message'].append('Passwords don\'t match')

    # Make sure the user's name will fit
    if len(account_data.name_field) > 70:
        account_creation_state['message'].append('Name needs to be less than 70 characters')

    # If everything validates, make sure that the email address and username haven't
    # already been registered. Only do this after validation to keep db queries low
    if (not len(account_creation_state['message'])) and len(account_data.name_field):
        emails = db.select('users', account_data,
            where = 'email LIKE $email_field'
        )
        if len(emails):
            account_creation_state['message'].append('Email address already registered, contact '
                                       'Julius to reset it, or use a different '
                                       'email address')
        accounts = db.select('users', account_data,
            where = 'name LIKE $name_field'
        )
        if len(accounts):
            account_creation_state['message'].append('Username already taken, please choose '
                                       'a different one. Sorry!')


    # If there were any validation account_creation_state, exit here and provide them
    if len(account_creation_state['message']):
        account_creation_state['problems'] = 1
        return account_creation_state
    else:
        # Otherwise, create the account

        from passlib.hash import bcrypt
        # 15 rounds seems to be the max that is reasonable to ask a user to wait for
        # password validation or hash creation. Takes about 2.40 seconds on my
        # system
        pass_hash = bcrypt.encrypt(account_data.pass_field, rounds=15)

        user_id = db.insert('users',
            name = account_data.name_field,
            email = account_data.email_field,
            pass_hash = pass_hash,
            privilege = 0
        )
        account_creation_state['message'] = 'Account created!'
        account_creation_state['token'] = generate_user_token(user_id)
        return account_creation_state

# Utility to create and return a token for user identification. Each token is linked
# to an account and is to be stored in the browser's localstorage
def generate_user_token (user_id):
    import base64
    db = config.db
    token = base64.urlsafe_b64encode(os.urandom(99))[:100]

    # Create a new token in the database, it's just a random string mapped to a user
    db.insert('user_tokens',
        user_id = user_id,
        token = token
    )

    return token

def auth_user(token):
    db = config.db
    auth = db.query(
        'SELECT name,users.id FROM users,user_tokens '
        'WHERE users.id = user_tokens.user_id '
        'AND token = $token',
        vars = {'token': token.strip('"')}
    )
    
    if not bool(auth):
        #This token is not valid
        return None, None
    else:
        user_details = auth[0]
        return user_details['name'], user_details['id']

def logout_user(token):
    db = config.db
    rows_deleted = db.delete('user_tokens',
        where = 'token = $token',
        vars = {'token':token.strip('"')}
    )

    if rows_deleted < 1:
        return False
    else:
        return True

def login_account(account_data):
    db = config.db
    user_account = db.select('users',
        what = 'id,users.pass_hash',
        where = 'users.email = $email',
        vars = {'email': account_data.email_field}
    )
    if not len(user_account):
        return False;
    else:
        account = user_account[0]
        from passlib.hash import bcrypt
        if bcrypt.verify(account_data.pass_field, account.pass_hash):
            new_token = generate_user_token(account['id'])
            return new_token
        else:
            return False;
