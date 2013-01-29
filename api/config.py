from web import database, utils
from os import path

# Something is seriously screwed up with this import here. Just going to pull out
# the information I need manually and skip it
# from cv2.cv import CV_IMWRITE_PNG_COMPRESSION
CV_IMWRITE_PNG_COMPRESSION = 16

db = database(dbn='mysql', user='mowmow', pw='Iq2UKpvgwqKP83WmdrsQB',
        db='mowmow')
img_root = 'static/img/mrow'
dir_base, api_path = path.split(path.dirname(__file__))

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
