import sys
import os
os.chdir('/var/www/mowmow/')
sys.path.append('/var/www/mowmow/')
sys.path.append('/var/www/mowmow/mowlib/')
import mow_utils
import config
from web import utils

status = mow_utils.get_status(None)

if status['fed']:
    print('Already fed')
else:
    print('Feeding')
    data = utils.storage(feed = 1)
    mow_utils.feed_cycle(data, mow_utils.date_strings(), None)
