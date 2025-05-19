from app import create_app, db
from app.models.user import Role

app = create_app('development')
with app.app_context():
    Role.insert_roles()
    print('Roles updated successfully.')
