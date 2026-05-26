import logging
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt

from database.db import db
from models.user import User
from models.patient import Patient

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def role_required(*roles):
    """Custom decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                logger.warning(
                    'Unauthorized access attempt by user %s (role: %s) to %s',
                    current_user.email, current_user.role, request.path
                )
                logout_user()
                session.clear()
                flash('Access denied. You do not have permission to view that page.', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            if not user.is_active:
                flash('Your account has been deactivated. Contact the administrator.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=False)
            session.permanent = True
            logger.info('User %s logged in successfully (role: %s)', email, user.role)
            flash(f'Welcome back!', 'success')
            return _redirect_by_role(user.role)
        else:
            logger.warning('Failed login attempt for email: %s from IP: %s', email, request.remote_addr)
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle patient registration."""
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        # Validation
        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if age:
            try:
                age = int(age)
                if age < 0 or age > 150:
                    errors.append('Please enter a valid age.')
            except ValueError:
                errors.append('Age must be a number.')
                age = None

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        # Check uniqueness
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        if phone and Patient.query.filter_by(phone=phone).first():
            flash('This phone number is already registered.', 'danger')
            return render_template('auth/register.html')

        try:
            # Create patient profile
            patient = Patient(
                full_name=full_name,
                email=email,
                age=age if age else None,
                gender=gender if gender else None,
                phone=phone if phone else None,
                address=address if address else None
            )
            db.session.add(patient)
            db.session.flush()  # Get patient_id before committing

            # Create user account
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(
                email=email,
                password_hash=hashed_pw,
                role='Patient',
                linked_id=patient.patient_id
            )
            db.session.add(user)
            db.session.commit()

            logger.info('New patient registered: %s (ID: %s)', email, patient.patient_id)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logger.error('Registration failed for %s: %s', email, str(e))
            flash('Registration failed. Please try again later.', 'danger')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logger.info('User %s logged out', current_user.email)
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role(role):
    """Redirect user to their role-specific dashboard."""
    if role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'Doctor':
        return redirect(url_for('doctor.dashboard'))
    else:
        return redirect(url_for('patient.dashboard'))
