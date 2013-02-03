from config import db

def get(req_path):
    if req_path == 'top_users':
        top_users_data = db.query(
            'SELECT name, count(nomnoms.id) as count '
            'FROM users,nomnoms '
            'WHERE nomnoms.user_id = users.id '
            'GROUP BY users.name ORDER BY count DESC LIMIT 5'
        )
        top_users = []
        for user in top_users_data:
            top_users.append(user)
        return {'top_users': top_users}

