import sys
import os
import cv2
import time
import config

db = config.db

def init_camera():
    # camera_port - Camera 0 is the integrated web cam on my netbook

    # We can set up the camera with the VideoCapture() class. All it needs is
    # the index to a camera port. The return will be a cv2.VideoCapture
    # object
    return cv2.VideoCapture(config.camera_port)

# Captures a single image from the camera and returns it in PIL format
def get_image(camera):
    # read is the easiest way to get a full image out of a VideoCapture object
    retval, im = camera.read()
    return im

# Takes image_count number of images, which it labels as
# mowmow<num>.png and saves to the specified directory.
def generate_image_set(image_count, img_directory, date_strings, sleep_time,
        camera, nomnom_id):

    while image_count > 0:
        # For now I am opening and closing the camera for each photo. This is
        # probably not ideal, but I have been having some problems with clearing
        # what I would imagine is the camera's internal buffer, i.e. if I keep the
        # camera open, even if I sleep after doing a cv2.VideoCapture.read() I will
        # get images from right after the camera object was opened when doing
        # another read() later
        if not camera.isOpened():
            camera.open(config.camera_port)
            # Sleep here for a sec so that the camera can focus and adjust light
            # levels
            time.sleep(1)
        print("Taking image " + str(image_count) + "\n")

        # Throw away a number of images to let the camera adjust to the light
        for i in xrange(30):
            camera_capture = get_image(camera)
        filename = ('kitteh-' + date_strings.current_time +
                '-' + str(image_count) + ".png")
        file = os.path.join(img_directory, filename)
        # A nice feature of the SaveImage method is that it will automatically
        # choose the correct format based on the file extension you provide.
        # Convenient!
        cv2.imwrite(file, camera_capture)
        db.insert('photo',
                file_name=filename,
                file_path=img_directory,
                nomnom_id=nomnom_id)
        image_count = image_count - 1
        camera.release()
        if image_count > 1:
            time.sleep(sleep_time)
    return
