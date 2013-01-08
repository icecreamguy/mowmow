from web import database, utils
from os import path
from cv2.cv import CV_IMWRITE_PNG_COMPRESSION

db = database(dbn='mysql', user='mowmow', pw='CHANGE ME',
        db='mowmow')
img_root = 'static/img/mrow'
dir_base = path.dirname(__file__)

camera_port = 0
compression_settings = [int(CV_IMWRITE_PNG_COMPRESSION), 9]

# web.storage object to store the feeding times. There are one or more feeding
# cycles. You can call each time anything. Each cycle must have a "start" and an
# "end" time, between which times the cat can be fed once.
nom_cycles = utils.storify({
    'morning': {
        'start': '05:00',
        'end': '07:00',
    },
    'evening': {
        'start': '17:00',
        'end': '19:00',
    },
})
