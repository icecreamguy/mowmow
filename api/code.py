import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mowlib'))
sys.path.append(os.path.dirname(__file__))
import web
import mow_utils
import json
import datetime
import config 
db = config.db
img_root = config.img_root

urls = (
    '/nomnom', 'nomnom',
    mow_utils.date_regex_string, 'photo',
    '/status', 'status',
    '/login/?(new|existing)?', 'login',
    '/logout', 'logout',
    '/stats/(top_users)', 'stats',
)

# Doing this correctly finally and keeping the model logic organized. This goes
# straight to the stats model file's get method, passing the req_path in
class stats:
    def GET(self, req_path):
        from models import stats_model

        # No cache during testing
        web.header('cache-control', 'max-age=0')
        #return stats_model.get(req_path)
        return json.dumps(stats_model.get(req_path))

class login:
    def POST(self, req_path):
        data = web.input()
        # Never cache login replies
        web.header('cache-control', 'max-age=0')
        if req_path == 'new':
            # Create new account
            return json.dumps(mow_utils.create_account(data))
        elif req_path == 'existing':
            return json.dumps(mow_utils.login_account(data))

class logout:
    def POST(self):
        auth_token = web.cookies().get('auth_token')
        return mow_utils.logout_user(auth_token)

class nomnom:
    def POST(self):
        data = web.input()

        auth_token = web.cookies().get('auth_token')
        # There are timestamp data associated with this specific image set. I 
        # plan to elimitate this in the future
        date_strings = mow_utils.date_strings()
        response = mow_utils.feed_cycle(data, date_strings, auth_token)
        return response

# Any requests for the location of photos come here. So far it can return photos by
# date or as a list of the most recent photos
class photo:
    def GET(self, req_path):
        from models import photo_model
        inputs = web.input()
        return json.dumps(photo_model.get(req_path, inputs), cls=mow_utils.webpy_db_encoder)

class status:
    def GET(self):
        auth_token = web.cookies().get('auth_token')
        web.header('cache-control', 'max-age=0')
        return json.dumps(mow_utils.get_status(auth_token),
                cls=mow_utils.webpy_db_encoder)

# out and enable the if block below it
application = web.application(urls, globals()).wsgifunc()
#if __name__ == "__main__":
#    application = web.application(urls, globals())
#    application.run()
