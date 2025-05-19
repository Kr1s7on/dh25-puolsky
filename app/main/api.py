from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Resident

api = Blueprint('api', __name__)

@api.route('/residents')
@login_required
def get_residents():
    """Get a list of all residents for the sidebar."""
    residents = []
    
    # Admins see all residents
    if current_user.is_admin():
        residents_query = Resident.query.all()
    else:
        # Regular caregivers only see assigned residents
        residents_query = current_user.residents
    
    # Format the response
    residents = [
        {
            'id': resident.id,
            'name': resident.name,
            'photo_url': resident.photo_url
        }
        for resident in residents_query
    ]
    
    return jsonify({'residents': residents})
