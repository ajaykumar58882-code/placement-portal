from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    students_count = StudentProfile.query.count()
    companies_count = CompanyProfile.query.count()
    drives_count = PlacementDrive.query.count()
    applications_count = Application.query.count()
    
    pending_companies = User.query.filter_by(role='company', is_approved=False).count()
    pending_drives = PlacementDrive.query.filter_by(status='Pending').count()

    return render_template('admin/dashboard.html', 
                           students_count=students_count,
                           companies_count=companies_count,
                           drives_count=drives_count,
                           applications_count=applications_count,
                           pending_companies=pending_companies,
                           pending_drives=pending_drives)

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    search = request.args.get('search', '')
    if search:
        companies_list = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f'%{search}%')).all()
    else:
        companies_list = CompanyProfile.query.all()
    return render_template('admin/companies.html', companies=companies_list)

@admin_bp.route('/companies/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_company(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'company':
        user.is_approved = True
        db.session.commit()
        flash(f'Company {user.username} has been approved.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/companies/toggle_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_company_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'company':
        user.is_active = not user.is_active
        db.session.commit()
        status_msg = "activated" if user.is_active else "blacklisted"
        flash(f'Company account has been {status_msg}.', 'info')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '')
    if search:
        students_list = StudentProfile.query.join(User).filter(
            (StudentProfile.full_name.ilike(f'%{search}%')) | 
            (StudentProfile.roll_number.ilike(f'%{search}%')) |
            (StudentProfile.contact.ilike(f'%{search}%'))
        ).all()
    else:
        students_list = StudentProfile.query.all()
    return render_template('admin/students.html', students=students_list)

@admin_bp.route('/students/toggle_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_student_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'student':
        user.is_active = not user.is_active
        db.session.commit()
        status_msg = "activated" if user.is_active else "blacklisted"
        flash(f'Student account has been {status_msg}.', 'info')
    return redirect(url_for('admin.students'))

@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    drives_list = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drives_list)

@admin_bp.route('/drives/update_status/<int:drive_id>', methods=['POST'])
@login_required
@admin_required
def update_drive_status(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    new_status = request.form.get('status')
    if new_status in ['Approved', 'Rejected', 'Closed', 'Pending']:
        drive.status = new_status
        db.session.commit()
        flash(f'Drive status updated to {new_status}.', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/drives/delete/<int:drive_id>', methods=['POST'])
@login_required
@admin_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    db.session.delete(drive)
    db.session.commit()
    flash('Placement drive deleted successfully.', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/students/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'student':
        db.session.delete(user)
        db.session.commit()
        flash('Student account deleted successfully.', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/companies/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_company(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'company':
        db.session.delete(user)
        db.session.commit()
        flash('Company account deleted successfully.', 'success')
    return redirect(url_for('admin.companies'))
