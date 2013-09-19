import sys
import os
import cv2
import time
from http_cam import http_cam
import config
from urllib2 import URLError

db = config.db

def init_camera():
    # camera_port - Camera 0 is the integrated web cam on my netbook

    # We can set up the camera with the VideoCapture() class. All it needs is
    # the index to a camera port. The return will be a cv2.VideoCapture
    # object
    if (config.camera_type == 'usb'):
        return cv2.VideoCapture(config.camera_port)
    else:
        http_camera = http_cam(
                config.http_cam_url,
                config.http_cam_realm,
                config.http_cam_user,
                config.http_cam_pass
        )
        # Don't actually need to return the camera here for HTTP
        return http_camera
        
# Captures a single image from the camera and returns it in PIL format
def get_image(camera):
    # read is the easiest way to get a full image out of a VideoCapture object
    retval, im = camera.read()
    return im

# Takes image_count number of images, which it labels as
# mowmow<num>.png and saves to the specified directory.
def generate_image_set(image_count, img_directory, date_strings, sleep_time,
        camera, cycle_name, nomnom_id):

    dir_base = config.dir_base
    while image_count > 0:
        # need to close and reopen camera in order to flush the buffer,
        if (config.camera_type == 'usb'):
            if not camera.isOpened():
                camera.open(config.camera_port)
                # Sleep here for a sec so that the camera can focus and adjust light
                # levels
                time.sleep(1)
        print("Taking image " + str(image_count) + "\n")

        if (config.camera_type == 'usb'):
            # Throw away a number of images to let the camera adjust to the light
            for i in xrange(30):
                camera_capture = get_image(camera)
        else:
            try:
                camera_capture = camera.fetch_image()
            except URLError:
                raise
                return
        filename = ('kitteh-' + date_strings.current_time + '-' + str(image_count) + ".png")
        file = os.path.join(dir_base, img_directory, filename)

        print('writing image to file: %s' % file)
        # Use the opencv save for USB cam, PIL for HTTP cam
        if (config.camera_type == 'usb'):
            # Opencv will automatically convert to PNG based on the file
            # extension
            cv2.imwrite(file, camera_capture, config.compression_settings)
        else:
            camera_capture.save(file, optimize=True)

        # Shrink the image and compress for a thumbnail. Original
        # image is preserved, this new one has '_thumb' at the end
        os.system('convert %s -quality 9 -resize 200x150 %s' % (file,
            file.replace('.png','_thumb.png')))

        db.insert('photo',
                file_name=filename,
                file_path=img_directory,
                nomnom_id=nomnom_id)
        image_count = image_count - 1
        if (config.camera_type == 'usb'):
            camera.release()
        if image_count > 1:
            time.sleep(sleep_time)
    return
