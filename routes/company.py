from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import PlacementDrive, Application
from functools import wraps
from datetime import datetime

company_bp = Blueprint('company', __name__)

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'company':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('index'))
        if not current_user.is_approved:
            flash('Your account is pending approval from the admin.', 'info')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    drives = PlacementDrive.query.filter_by(company_id=current_user.company_profile.id).all()
    return render_template('company/dashboard.html', drives=drives)

@company_bp.route('/drive/create', methods=['GET', 'POST'])
@login_required
@company_required
def create_drive():
    if request.method == 'POST':
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        eligibility_criteria = request.form.get('eligibility_criteria')
        application_deadline_str = request.form.get('application_deadline')
        
        try:
            application_deadline = datetime.strptime(application_deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('company.create_drive'))

        new_drive = PlacementDrive(
            company_id=current_user.company_profile.id,
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility_criteria,
            application_deadline=application_deadline,
            status='Pending'
        )
        db.session.add(new_drive)
        db.session.commit()
        flash('Placement drive created successfully and is pending admin approval.', 'success')
        return redirect(url_for('company.dashboard'))
        
    return render_template('company/create_drive.html')

@company_bp.route('/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        drive.job_title = request.form.get('job_title')
        drive.job_description = request.form.get('job_description')
        drive.eligibility_criteria = request.form.get('eligibility_criteria')
        application_deadline_str = request.form.get('application_deadline')
        
        try:
            drive.application_deadline = datetime.strptime(application_deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('company.edit_drive', drive_id=drive.id))

        db.session.commit()
        flash('Placement drive updated successfully.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/edit_drive.html', drive=drive)

@company_bp.route('/drive/<int:drive_id>/delete', methods=['POST'])
@login_required
@company_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('company.dashboard'))

    db.session.delete(drive)
    db.session.commit()
    flash('Placement drive deleted.', 'success')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/drive/<int:drive_id>')
@login_required
@company_required
def view_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('company.dashboard'))
        
    applications = Application.query.filter_by(drive_id=drive.id).all()
    return render_template('company/view_drive.html', drive=drive, applications=applications)

@company_bp.route('/application/update_status/<int:app_id>', methods=['POST'])
@login_required
@company_required
def update_application_status(app_id):
    application = Application.query.get_or_404(app_id)
    if application.drive.company_id != current_user.company_profile.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('company.dashboard'))
        
    new_status = request.form.get('status')
    if new_status in ['Shortlisted', 'Selected', 'Rejected', 'Applied']:
        application.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
        
    return redirect(url_for('company.view_drive', drive_id=application.drive_id))
