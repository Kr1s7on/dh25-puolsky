from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from flask_rq import get_queue
import os
from werkzeug.utils import secure_filename

from app import db
from app.admin.forms import (
    ChangeAccountTypeForm,
    ChangeUserEmailForm,
    InviteUserForm,
    NewUserForm,
)
from app.admin.resident_forms import ResidentForm
from app.decorators import admin_required
from app.email import send_email
from app.models import EditableHTML, Role, User, Resident

admin = Blueprint('admin', __name__)


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'admin/registered_users.html', users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'.format(
            user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<int:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash('Role for user {} successfully changed to {}.'.format(
            user.full_name(), user.role.name), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200

# Resident Management Routes

@admin.route('/residents')
@login_required
@admin_required
def residents():
    """View all residents."""
    residents = Resident.query.all()
    return render_template('admin/residents.html', residents=residents)


@admin.route('/resident/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_resident():
    """Create a new resident."""
    form = ResidentForm()
    if form.validate_on_submit():
        # Handle photo upload
        photo_url = None
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join('app', 'static', 'images', 'residents', filename)
            form.photo.data.save(photo_path)
            photo_url = url_for('static', filename=f'images/residents/{filename}')
        
        # Create resident
        resident = Resident(
            name=form.name.data,
            date_of_birth=form.date_of_birth.data,
            photo_url=photo_url
        )
        
        # Add resident to database
        db.session.add(resident)
        db.session.commit()
        
        # Assign caregivers
        for caregiver in form.caregivers.data:
            caregiver.residents.append(resident)
        
        db.session.commit()
        flash(f'Resident {resident.name} successfully created.', 'success')
        return redirect(url_for('admin.residents'))
    
    return render_template('admin/new_resident.html', form=form)


@admin.route('/resident/<int:resident_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_resident(resident_id):
    """Edit a resident."""
    resident = Resident.query.get_or_404(resident_id)
    form = ResidentForm(obj=resident)
    
    # Pre-select current caregivers
    if request.method == 'GET':
        form.caregivers.data = resident.caregivers.all()
    
    if form.validate_on_submit():
        # Update resident info
        resident.name = form.name.data
        resident.date_of_birth = form.date_of_birth.data
        
        # Handle photo upload
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join('app', 'static', 'images', 'residents', filename)
            form.photo.data.save(photo_path)
            resident.photo_url = url_for('static', filename=f'images/residents/{filename}')
        
        # Update caregiver assignments
        # Clear current caregivers
        for caregiver in resident.caregivers.all():
            caregiver.residents.remove(resident)
        
        # Add selected caregivers
        for caregiver in form.caregivers.data:
            caregiver.residents.append(resident)
        
        db.session.commit()
        flash(f'Resident {resident.name} successfully updated.', 'success')
        return redirect(url_for('admin.residents'))
    
    return render_template('admin/edit_resident.html', form=form, resident=resident)


@admin.route('/resident/<int:resident_id>/delete')
@login_required
@admin_required
def delete_resident(resident_id):
    """Delete a resident."""
    resident = Resident.query.get_or_404(resident_id)
    name = resident.name
    
    # Delete the resident
    db.session.delete(resident)
    db.session.commit()
    
    flash(f'Resident {name} successfully deleted.', 'success')
    return redirect(url_for('admin.residents'))
