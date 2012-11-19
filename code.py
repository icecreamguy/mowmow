import sys
sys.path.append('./mowlib')
sys.path.append('.')
import os
import web
import camowra
import mow_utils
import json
import datetime
import config

db = config.db
img_root = config.img_root
schedule = mow_utils.schedule()

# Not actually passing anything to the template renderer yet, not sure if I ever
# will
render = web.template.render('templates/')

urls = (
    '/nomnom', 'nomnom',
    mow_utils.date_regex_string, 'photo',
    '/status', 'status',
    '/(.*)', 'index',
)

class index:
    def GET(self, req_path):
        # Don't actually need to do anything here yet other than to return the
        # rendered template
        return render.index()

# This is where the it all happens. A call to this class will either tell the user
# that the feeder is locked, or it will feed the cat and take photos
class nomnom:
    def POST(self):
        data = web.input()

        if 'feed' in data:
            schedule = mow_utils.schedule()
            status = mow_utils.get_status(db, schedule)
            nomnom_result = {}

            #if status['lock']:
               # return json.dumps({'result': 'locked'})

            # There are timestamp data associated with this specific image set. I 
            # plan to elimitate this in the future
            date_strings = mow_utils.date_strings()

            img_folder = mow_utils.make_imgfolder_string(img_root, date_strings)

            if not os.path.exists(img_folder):
                mow_utils.mkdir_p(img_folder)

            # Make an entry in the nomnoms table for this feeding. The images will
            # be associated with this record
            nomnom_id = db.insert('nomnoms')

            #Feed the baileycat
            mow_utils.activate_feeder()

            # Fire up the camera!
            camera = camowra.init_camera()

            # Grab a set of photos
            camowra.generate_image_set(4, img_folder, date_strings, 3, camera,
                    nomnom_id)

            # delete the camera object
            del(camera)

            return json.dumps(nomnom_result)

# Any requests for the location of photos come here. So far it can return photos by
# date or as a list of the most recent photos
class photo:
    def GET(self, req_path):
        inputs = web.input()
        request = mow_utils.obj_from_photo_path(req_path)
        # TODO: validate the request['recent'] string
        if 'recent' in request:
            response = db.query('SELECT * FROM photo,nomnoms WHERE photo.nomnom_id '
                                '= nomnoms.id ORDER BY nomnoms.time_stamp DESC '
                                'LIMIT ' + request['recent'])
            # Copy the db results out so that they can be postprocessed properly by
            # the JSONEncoder class
            response_list = list(response)
            return json.dumps(response_list, cls=mow_utils.webpy_db_encoder)
        elif 'date' in request:
            response = db.query('SELECT * FROM photo,nomnoms WHERE photo.nomnom_id '
                                ' = nomnoms.id AND DATE(time_stamp) LIKE $date '
                                'ORDER BY time_stamp DESC', vars=request)
            response_list = list(response)
            return json.dumps(response_list, cls=mow_utils.webpy_db_encoder)
        return

class status:
    def GET(self):
        return json.dumps(mow_utils.get_status(config.db, mow_utils.schedule()),
                cls=mow_utils.webpy_db_encoder)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
