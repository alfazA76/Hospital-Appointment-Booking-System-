import json
import logging

import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.db import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from routes.auth import role_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@role_required('Admin')
def dashboard():
    """Admin dashboard with real-time metrics."""
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    active_doctors = Doctor.query.count()
    pending_appointments = Appointment.query.filter_by(status='Pending').count()
    confirmed_appointments = Appointment.query.filter_by(status='Confirmed').count()
    cancelled_appointments = Appointment.query.filter_by(status='Cancelled').count()

    # Recent appointments
    recent_appointments = Appointment.query.order_by(
        Appointment.appointment_date.desc()
    ).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_patients=total_patients,
        total_appointments=total_appointments,
        active_doctors=active_doctors,
        pending_appointments=pending_appointments,
        confirmed_appointments=confirmed_appointments,
        cancelled_appointments=cancelled_appointments,
        recent_appointments=recent_appointments
    )


@admin_bp.route('/doctors')
@role_required('Admin')
def manage_doctors():
    """View and manage all doctors."""
    doctors = Doctor.query.order_by(Doctor.doctor_name).all()
    return render_template('admin/manage_doctors.html', doctors=doctors)


@admin_bp.route('/doctors/add', methods=['GET', 'POST'])
@role_required('Admin')
def add_doctor():
    """Add a new doctor profile and user account."""
    if request.method == 'POST':
        doctor_name = request.form.get('doctor_name', '').strip()
        specialization = request.form.get('specialization', '').strip()
        department = request.form.get('department', '').strip()
        contact = request.form.get('contact', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Availability — build from form
        availability = {}
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for day in days:
            slots = request.form.get(f'slots_{day}', '').strip()
            if slots:
                availability[day] = [s.strip() for s in slots.split(',') if s.strip()]

        # Validation
        errors = []
        if not doctor_name:
            errors.append('Doctor name is required.')
        if not specialization:
            errors.append('Specialization is required.')
        if not department:
            errors.append('Department is required.')
        if not email:
            errors.append('Email is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin/add_doctor.html')

        # Check email uniqueness
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('admin/add_doctor.html')

        try:
            doctor = Doctor(
                doctor_name=doctor_name,
                specialization=specialization,
                department=department,
                contact=contact if contact else None,
                availability=json.dumps(availability) if availability else None
            )
            db.session.add(doctor)
            db.session.flush()

            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(
                email=email,
                password_hash=hashed_pw,
                role='Doctor',
                linked_id=doctor.doctor_id
            )
            db.session.add(user)
            db.session.commit()

            logger.info('New doctor added: %s (ID: %s)', doctor_name, doctor.doctor_id)
            flash(f'Dr. {doctor_name} has been added successfully.', 'success')
            return redirect(url_for('admin.manage_doctors'))

        except Exception as e:
            db.session.rollback()
            logger.error('Failed to add doctor: %s', str(e))
            flash('Failed to add doctor. Please try again.', 'danger')

    return render_template('admin/add_doctor.html')


@admin_bp.route('/doctors/delete/<int:doctor_id>', methods=['POST'])
@role_required('Admin')
def delete_doctor(doctor_id):
    """Remove a doctor profile and associated user account."""
    doctor = Doctor.query.get_or_404(doctor_id)

    try:
        # Find and delete the associated user account
        user = User.query.filter_by(role='Doctor', linked_id=doctor_id).first()
        if user:
            db.session.delete(user)

        db.session.delete(doctor)
        db.session.commit()

        logger.info('Doctor deleted: %s (ID: %s)', doctor.doctor_name, doctor_id)
        flash(f'Dr. {doctor.doctor_name} has been removed.', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error('Failed to delete doctor %s: %s', doctor_id, str(e))
        flash('Failed to remove doctor. Please try again.', 'danger')

    return redirect(url_for('admin.manage_doctors'))


@admin_bp.route('/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
@role_required('Admin')
def edit_doctor(doctor_id):
    """Edit an existing doctor profile."""
    doctor = Doctor.query.get_or_404(doctor_id)

    if request.method == 'POST':
        doctor_name = request.form.get('doctor_name', '').strip()
        specialization = request.form.get('specialization', '').strip()
        department = request.form.get('department', '').strip()
        contact = request.form.get('contact', '').strip()

        # Availability
        availability = {}
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for day in days:
            slots = request.form.get(f'slots_{day}', '').strip()
            if slots:
                availability[day] = [s.strip() for s in slots.split(',') if s.strip()]

        if not doctor_name or not specialization or not department:
            flash('Name, specialization, and department are required.', 'danger')
            return render_template('admin/edit_doctor.html', doctor=doctor)

        try:
            doctor.doctor_name = doctor_name
            doctor.specialization = specialization
            doctor.department = department
            doctor.contact = contact if contact else None
            doctor.availability = json.dumps(availability) if availability else None
            db.session.commit()

            logger.info('Doctor updated: %s (ID: %s)', doctor_name, doctor_id)
            flash(f'Dr. {doctor_name} profile updated successfully.', 'success')
            return redirect(url_for('admin.manage_doctors'))

        except Exception as e:
            db.session.rollback()
            logger.error('Failed to update doctor %s: %s', doctor_id, str(e))
            flash('Failed to update doctor profile.', 'danger')

    # Parse current availability for form pre-population
    current_availability = {}
    if doctor.availability:
        try:
            current_availability = json.loads(doctor.availability)
        except json.JSONDecodeError:
            pass

    return render_template('admin/edit_doctor.html', doctor=doctor, current_availability=current_availability)
