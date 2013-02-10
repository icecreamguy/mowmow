import re
from config import db

photo_path_regex_string = ("date/((?:19|20\d\d)-(?:0[1-9]|1[012])-(?:0[1-9]|[12][0-"
                           "9]|3[01]))$|recent/(\d{1,2})$")

def get(req_path, inputs):
    request = obj_from_photo_path(req_path)
    if 'recent' in request:
        photo_sets = db.query(
            'SELECT cycle_name, nomnoms.time_stamp, users.name, nomnoms.id '
            'FROM nomnoms,users '
            'WHERE nomnoms.user_id = users.id '
            'ORDER BY nomnoms.time_stamp DESC '
            'LIMIT 2')
        # Get this into a list so it can be filled with it's photos before being
        # sent back to the client
        photo_sets_filled = [fill_photo_set(photo_set) for photo_set in photo_sets]
        return photo_sets_filled
    #return {'photo_sets': fill_photo_sets(photo_sets)}
    elif 'date' in request:
        response = db.query('SELECT cycle_name,nomnoms.time_stamp,file_name,'
                            'file_path,users.name '
                            'FROM photo,nomnoms,users '
                            'WHERE photo.nomnom_id = nomnoms.id '
                            'AND nomnoms.user_id = users.id '
                            'AND DATE(nomnoms.time_stamp) LIKE $date '
                            'ORDER BY nomnoms.time_stamp DESC', vars=request)
        response_list = list(response)
        return response_list
    return

# For each set of photos, get a dict of the details of each photo
def fill_photo_set(photo_set):
    photos = db.select('photo',
            what = 'file_name,file_path',
            where = 'nomnom_id = $id',
            vars = photo_set)
    photo_set.photos = photos.list()
    return photo_set

def obj_from_photo_path(path):
    request = {}
    photo_path_regex = re.compile(photo_path_regex_string)
    groups = photo_path_regex.match(path).groups()
    # Put the results in a small dictionary based on what matched
    if groups[1]:
        request = {'recent': groups[1]}
    else:
        request = {'date': groups[0]}
    return request
