import web
from os import path
from datetime import datetime, timedelta
import time
from dateutil import tz

db = web.database(dbn='mysql', user='mowmow', pw='CHANGE ME',
        db='mowmow')
img_root = 'static/img/mrow'
dir_base = path.dirname(__file__)

camera_port = 0

morning_start = '05:00'
morning_end = '07:00'
evening_start = '17:00'
evening_end = '19:00'
noon = '12:00'

time_format = '%Y-%m-%d %H:%M'
