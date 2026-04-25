from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import PlacementDrive, Application, StudentProfile
from functools import wraps
from werkzeug.utils import secure_filename
from flask import current_app
import os

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    applications = Application.query.filter_by(student_id=current_user.student_profile.id).all()
    return render_template('student/dashboard.html', applications=applications)

@student_bp.route('/drives')
@login_required
@student_required
def drives():
    approved_drives = PlacementDrive.query.filter_by(status='Approved').all()
    # Get IDs of drives the student has already applied to
    applied_drive_ids = [app.drive_id for app in current_user.student_profile.applications]
    return render_template('student/drives.html', drives=approved_drives, applied_drive_ids=applied_drive_ids)

@student_bp.route('/drive/<int:drive_id>/apply', methods=['POST'])
@login_required
@student_required
def apply_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != 'Approved':
        flash('You can only apply to approved drives.', 'danger')
        return redirect(url_for('student.drives'))

    # Check for existing application
    existing_app = Application.query.filter_by(student_id=current_user.student_profile.id, drive_id=drive_id).first()
    if existing_app:
        flash('You have already applied to this drive.', 'warning')
    else:
        new_app = Application(student_id=current_user.student_profile.id, drive_id=drive_id)
        db.session.add(new_app)
        db.session.commit()
        flash('Successfully applied to the placement drive.', 'success')

    return redirect(url_for('student.drives'))

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    if request.method == 'POST':
        profile = current_user.student_profile
        profile.full_name = request.form.get('full_name')
        profile.roll_number = request.form.get('roll_number')
        profile.contact = request.form.get('contact')
        profile.branch = request.form.get('branch')
        
        cgpa_str = request.form.get('cgpa')
        if cgpa_str:
            profile.cgpa = float(cgpa_str)
            
        grad_year_str = request.form.get('graduation_year')
        if grad_year_str:
            profile.graduation_year = int(grad_year_str)

        # Handle resume file upload
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename != '':
            filename = secure_filename(resume_file.filename)
            # Create a unique filename to prevent overwrites
            unique_filename = f"{current_user.id}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            resume_file.save(filepath)
            # Store relative path for serving later
            profile.resume_path = f"uploads/resumes/{unique_filename}"

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student.profile'))
        
    return render_template('student/profile.html', profile=current_user.student_profile)
