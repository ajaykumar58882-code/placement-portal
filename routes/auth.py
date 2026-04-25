from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models import User, StudentProfile, CompanyProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated/blacklisted by the admin.', 'danger')
                return redirect(url_for('auth.login'))
            if not user.is_approved:
                flash('Your account is pending approval from the admin.', 'info')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect_dashboard(user)
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register_student'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password_hash=hashed_password, role='student', is_approved=True)
        db.session.add(user)
        db.session.commit()

        student_profile = StudentProfile(user_id=user.id, full_name=full_name)
        db.session.add(student_profile)
        db.session.commit()

        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_student.html')

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        hr_name = request.form.get('hr_name')
        hr_phone = request.form.get('hr_phone')
        website = request.form.get('website')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register_company'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password_hash=hashed_password, role='company', is_approved=False)
        db.session.add(user)
        db.session.commit()

        company_profile = CompanyProfile(
            user_id=user.id, 
            company_name=company_name,
            hr_contact_name=hr_name,
            hr_contact_phone=hr_phone,
            website=website
        )
        db.session.add(company_profile)
        db.session.commit()

        flash('Your company account has been created and is pending approval from the admin.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_company.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def redirect_dashboard(user):
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'company':
        return redirect(url_for('company.dashboard'))
    elif user.role == 'student':
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('index'))
