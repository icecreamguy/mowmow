import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mowlib'))
sys.path.append(os.path.join(os.path.dirname(__file__)))
import web
import camowra
import mow_utils
import json
import datetime
import config 
db = config.db
img_root = config.img_root

# Not actually passing anything to the template renderer yet, not sure if I ever
# will
render = web.template.render(os.path.join(os.path.dirname(__file__),'templates/'))

urls = (
    '/nomnom', 'nomnom',
    mow_utils.date_regex_string, 'photo',
    '/status', 'status',
    '/login/?(new)?', 'login',
    '/openid', 'openid',
    '/(.*)', 'index',
)

class index:
    def GET(self, req_path):
        # Don't actually need to do anything here yet other than to return the
        # rendered template
        return render.index()

class login:
    def POST(self, req_path):
        data = web.input()
        print(req_path)
        if req_path == 'new':
            # Create new account
            return json.dumps(mow_utils.create_account(data))
#    def GET(self, req_path):
#        request = req_path.split('/')
#        print request[1]
#        if request[0] == 'auth':
#            if not request[1]:
#                return 'Auth error...'
#            # Check if a user's token is valid
#            print('authing')
#            return mow_utils.auth_user(request[1])
#
# This is where the it all happens. A call to this class will either tell the user
# that the feeder is locked, or it will feed the cat and take photos
class nomnom:
    def POST(self):
        data = web.input()

        # There are timestamp data associated with this specific image set. I 
        # plan to elimitate this in the future
        date_strings = mow_utils.date_strings()
        response = mow_utils.feed_cycle(data, date_strings)
        return response

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
        auth_token = web.cookies().get('auth_token')
        return json.dumps(mow_utils.get_status(auth_token),
                cls=mow_utils.webpy_db_encoder)

# out and enable the if block below it
application = web.application(urls, globals()).wsgifunc()
#if __name__ == "__main__":
#    application = web.application(urls, globals())
#    application.run()
