import web
from datetime import datetime, timedelta
import time
from dateutil import tz

db = web.database(dbn='mysql', user='mowmow', pw='CHANGE_THIS_PASSWORD!',
        db='mowmow_test')
img_root = 'static/img/mrow'

camera_port = 0

morning_start = '05:00'
morning_end = '07:00'
evening_start = '17:00'
evening_end = '19:00'
noon = '12:00'

time_format = '%Y-%m-%d %H:%M'

#class schedule:
#    def __init__(self):
#        self.date_time = datetime.today()
#        self.date_time = self.local_to_utc(self.date_time)
#        self.today = datetime.strftime(self.date_time.date(), '%Y-%m-%d ')
#        self.noon = self.local_to_utc(datetime.strptime(self.today + noon,
#            time_format))
#        self.morning = {
#                'start': self.local_to_utc(datetime.strptime(self.today +
#                    morning_start, time_format)),
#                'end': self.local_to_utc(datetime.strptime(self.today + morning_end,
#                    time_format))
#                }
#        self.evening = {
#                'start': self.local_to_utc(datetime.strptime(self.today +
#                    evening_start, time_format)),
#                'end': self.local_to_utc(datetime.strptime(self.today + evening_end,
#                    time_format))
#                }
#
#    def local_to_utc(self, datetime):
#        local_tz = tz.tzlocal()
#        utc_tz = tz.tzutc()
#        datetime = datetime.replace(tzinfo=local_tz)
#        return datetime.astimezone(utc_tz)
#
