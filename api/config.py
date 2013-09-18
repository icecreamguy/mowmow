from web import database, utils
from os import path

# I have never been able to get this value to import properly from OpenCV,
# so it is manually defined here
CV_IMWRITE_PNG_COMPRESSION = 16

# Database settings
db = database(dbn='mysql', user='mowmow', pw='CHANGE_ME',
        db='mowmow')

# Image root for the website. HTTP user needs write access here
img_root = 'static/img/mrow'

# Assuming that the base for the API and website are both the directory
# that this config file is in. Can be changed if needed
dir_base, api_path = path.split(path.dirname(__file__))

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

######### Camera Settings ###########

# Type of camera to use. Currently only 'usb' and 'http' cameras are supported
camera_type = "http"

# Settings for USB cameras. Leave at default settings if not using USB camera
# USB camera port #, e.g. /dev/video0 would be port '0'
camera_port = 0

# Settings for HTTP cameras. Leave at default settings if not using an HTTP
# camera
# http cameral snapshot URL. Most HTTP cameras provide a streaming and 
# snapshot URL - use the snapshot URL here
http_cam_url = 'http://192.168.2.51/snapshot.cgi'

# Most HTTP cameras will be protected by a username and password. If not
# just leave these blank
http_cam_user = 'admin'
http_cam_pass = 'cramera'
# When you log into your camera using HTTP Basic authentication, it will
# provide a "realm" to your browser for which the credentials are valid.
# There will most likely be a message like "Server says: ipcamera_xxxxxxxx" 
# or "Site says: sucksco_ipcam_6500" This is the authentication realm.
http_cam_realm = 'ipcamera_00626E4A1F86'

# PNG compression settings, probably do not need modification
compression_settings = [int(CV_IMWRITE_PNG_COMPRESSION), 9]

