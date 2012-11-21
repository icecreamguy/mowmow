import sys
sys.path.append('.')
sys.path.append('./mowlib')
import mow_utils
import config
from web import utils

db = config.db
schedule = mow_utils.schedule()
status = mow_utils.get_status(db, schedule)

if status['fed']:
    pass
else:
    data = utils.storage(feed = 1)
    mow_utils.feed_cycle(data, mow_utils.schedule(), mow_utils.date_strings())
