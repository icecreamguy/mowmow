import sys
import os
os.chdir('/var/www/mowmow/')
sys.path.append('/var/www/mowmow/')
sys.path.append('/var/www/mowmow/mowlib/')
import mow_utils
import config
from web import utils

db = config.db
schedule = mow_utils.schedule()
status = mow_utils.get_status(db, schedule)

if status['fed'] == 1:
    print('Already fed')
else:
    print('Feeding')
    data = utils.storage(feed = 1)
    mow_utils.feed_cycle(data, schedule, mow_utils.date_strings())
