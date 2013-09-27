import sys
import os
os.chdir('/var/www/mowmow/')
sys.path.append('/var/www/mowmow/api')
sys.path.append('/var/www/mowmow/api/mowlib/')
import mow_utils
import config
from web import utils

db = config.db

print(status)
if status['fed']:
    print('Already fed')
else:
    print('Feeding')
    data = utils.storage(feed = 1)
    mow_utils.feed_cycle(data, mow_utils.date_strings(), None, external=True)
