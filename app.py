import json
import logging
import os

import bcrypt
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from database.db import db, init_db
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.prescription import Prescription

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)

    # ── Extensions ───────────────────────────────────────────────────────
    init_db(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ───────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.patient import patient_bp
    from routes.doctor import doctor_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)

    # ── CSRF exemption for JSON API endpoints ────────────────────────────
    csrf.exempt(patient_bp)  # For the slots API endpoint

    # ── Root redirect ────────────────────────────────────────────────────
    @app.route('/')
    def index():
        return render_template('landing.html')

    # ── Error Handlers ───────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        logger.error('Internal server error: %s', str(e))
        return render_template('errors/500.html'), 500

    # ── Seed Data ────────────────────────────────────────────────────────
    with app.app_context():
        _seed_data()

    logger.info('Hospital Appointment Booking System started successfully.')
    return app


def _seed_data():
    """Seed default admin, doctors, and sample data on first run."""
    # Check if admin already exists
    if User.query.filter_by(role='Admin').first():
        return

    logger.info('Seeding initial data...')

    try:
        # ── Admin account ────────────────────────────────────────────────
        admin_pw = bcrypt.hashpw('Admin@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_user = User(
            email='admin@hospital.com',
            password_hash=admin_pw,
            role='Admin',
            linked_id=None
        )
        db.session.add(admin_user)

        # ── Sample doctors ───────────────────────────────────────────────
        doctors_data = [
            {
                'name': 'Dr. Priya Sharma',
                'specialization': 'Cardiologist',
                'department': 'Cardiology',
                'contact': '9876543210',
                'email': 'dr.sharma@hospital.com',
                'availability': {
                    'Mon': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00'],
                    'Tue': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30'],
                    'Wed': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00'],
                    'Thu': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30'],
                    'Fri': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30'],
                }
            },
            {
                'name': 'Dr. Rahul Mehta',
                'specialization': 'Orthopedic Surgeon',
                'department': 'Orthopedics',
                'contact': '9876543211',
                'email': 'dr.mehta@hospital.com',
                'availability': {
                    'Mon': ['10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30'],
                    'Tue': ['10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00'],
                    'Wed': ['10:00', '10:30', '11:00', '11:30'],
                    'Thu': ['10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30'],
                    'Fri': ['10:00', '10:30', '11:00', '11:30', '14:00', '14:30'],
                    'Sat': ['10:00', '10:30', '11:00', '11:30'],
                }
            },
            {
                'name': 'Dr. Anita Desai',
                'specialization': 'Dermatologist',
                'department': 'Dermatology',
                'contact': '9876543212',
                'email': 'dr.desai@hospital.com',
                'availability': {
                    'Mon': ['09:00', '09:30', '10:00', '10:30', '11:00'],
                    'Tue': ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00'],
                    'Wed': ['09:00', '09:30', '10:00', '10:30', '11:00'],
                    'Thu': ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00'],
                    'Fri': ['09:00', '09:30', '10:00', '10:30', '11:00'],
                }
            },
            {
                'name': 'Dr. Vikram Singh',
                'specialization': 'Neurologist',
                'department': 'Neurology',
                'contact': '9876543213',
                'email': 'dr.singh@hospital.com',
                'availability': {
                    'Mon': ['11:00', '11:30', '14:00', '14:30', '15:00', '15:30', '16:00'],
                    'Tue': ['11:00', '11:30', '14:00', '14:30', '15:00', '15:30'],
                    'Wed': ['11:00', '11:30', '14:00', '14:30', '15:00', '15:30', '16:00'],
                    'Thu': ['11:00', '11:30', '14:00', '14:30', '15:00', '15:30'],
                    'Fri': ['11:00', '11:30', '14:00', '14:30', '15:00'],
                }
            },
            {
                'name': 'Dr. Kavita Patel',
                'specialization': 'Pediatrician',
                'department': 'Pediatrics',
                'contact': '9876543214',
                'email': 'dr.patel@hospital.com',
                'availability': {
                    'Mon': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30'],
                    'Tue': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30'],
                    'Wed': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30'],
                    'Thu': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30'],
                    'Fri': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30'],
                    'Sat': ['09:00', '09:30', '10:00', '10:30'],
                }
            },
        ]

        doctor_pw = bcrypt.hashpw('Doctor@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        for doc_data in doctors_data:
            doctor = Doctor(
                doctor_name=doc_data['name'],
                specialization=doc_data['specialization'],
                department=doc_data['department'],
                contact=doc_data['contact'],
                availability=json.dumps(doc_data['availability'])
            )
            db.session.add(doctor)
            db.session.flush()

            user = User(
                email=doc_data['email'],
                password_hash=doctor_pw,
                role='Doctor',
                linked_id=doctor.doctor_id
            )
            db.session.add(user)

        db.session.commit()
        logger.info('Seed data created successfully.')

    except Exception as e:
        db.session.rollback()
        logger.error('Failed to seed data: %s', str(e))


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
