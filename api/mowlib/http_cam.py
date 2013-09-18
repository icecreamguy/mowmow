import urllib2
import Image
from cStringIO import StringIO

class http_cam:
    # If I keep adding cameral drivers I will reorganize all of this,
    # but for now this is made expressly to fit into the existing USB
    # camera API

    def __init__(self, http_cam_url, http_cam_realm, http_cam_user, http_cam_pass):
        self.cam_url = http_cam_url
        self.cam_realm = http_cam_realm
        self.cam_user = http_cam_user
        self.cam_pass = http_cam_pass

        # Pretty much verbatim from the docs here, initialize once
        # for the set of photos
        self.auth_handler = urllib2.HTTPBasicAuthHandler()
        self.auth_handler.add_password(
                realm = self.cam_realm,
                uri = self.cam_url,
                user = self.cam_user,
                passwd = self.cam_pass
        )

        self.opener = urllib2.build_opener(self.auth_handler)
        urllib2.install_opener(self.opener)

    # return the camera URL on initialization
    def init_camera(self):
        return self.cam_url

    def fetch_image(self):
        print("Fetching image from " + self.cam_url)
        self.img = urllib2.urlopen(self.cam_url).read()
        return Image.open(StringIO(self.img))
