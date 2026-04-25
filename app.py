from flask import Flask, redirect, url_for, render_template, request
from extensions import db, login_manager, bcrypt
from models import User
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key-for-placement-portal-2026'
    
    # Use an absolute path for the sqlite database to ensure it's written locally
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure file uploads
    upload_folder = os.path.join(basedir, 'static', 'uploads', 'resumes')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5 MB max

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(student_bp, url_prefix='/student')

    @app.route('/')
    def index():
        return render_template('index.html')

    # Initialize Admin if not exists
    with app.app_context():
        db.create_all()
        create_admin()

    return app

def create_admin():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(username='admin', password_hash=hashed_password, role='admin', is_approved=True)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created (username: admin, password: admin123)")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
