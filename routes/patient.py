import json
import logging
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import current_user

from database.db import db
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.prescription import Prescription
from routes.auth import role_required

logger = logging.getLogger(__name__)

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')


@patient_bp.route('/dashboard')
@role_required('Patient')
def dashboard():
    """Patient dashboard — search and filter doctors."""
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()

    query = Doctor.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Doctor.doctor_name.ilike(search_term),
                Doctor.specialization.ilike(search_term)
            )
        )

    if department:
        query = query.filter(Doctor.department == department)

    doctors = query.all()

    # Get unique departments for filter dropdown
    all_departments = db.session.query(Doctor.department).distinct().order_by(Doctor.department).all()
    departments = [d[0] for d in all_departments]

    return render_template(
        'patient/dashboard.html',
        doctors=doctors,
        departments=departments,
        search=search,
        selected_department=department
    )


@patient_bp.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@role_required('Patient')
def book_appointment(doctor_id):
    """Book an appointment with a specific doctor."""
    doctor = Doctor.query.get_or_404(doctor_id)
    patient = Patient.query.get(current_user.linked_id)

    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('patient.dashboard'))

    # Parse doctor availability
    availability = {}
    if doctor.availability:
        try:
            availability = json.loads(doctor.availability)
        except json.JSONDecodeError:
            logger.error('Invalid availability JSON for doctor %s', doctor_id)
            availability = {}

    if request.method == 'POST':
        appt_date_str = request.form.get('appointment_date', '').strip()
        appt_time = request.form.get('appointment_time', '').strip()

        if not appt_date_str or not appt_time:
            flash('Please select both a date and time slot.', 'warning')
            return render_template(
                'patient/book_appointment.html',
                doctor=doctor, availability=availability
            )

        try:
            appt_date = datetime.strptime(appt_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template(
                'patient/book_appointment.html',
                doctor=doctor, availability=availability
            )

        # Validate date is not in the past
        if appt_date < date.today():
            flash('Cannot book appointments in the past.', 'warning')
            return render_template(
                'patient/book_appointment.html',
                doctor=doctor, availability=availability
            )

        # Check day availability
        day_name = appt_date.strftime('%a')  # Mon, Tue, etc.
        available_slots = availability.get(day_name, [])
        if appt_time not in available_slots:
            flash('This time slot is not available for the selected date.', 'warning')
            return render_template(
                'patient/book_appointment.html',
                doctor=doctor, availability=availability
            )

        # Check for overbooking — verify slot is not already taken
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appt_date,
            appointment_time=appt_time
        ).filter(Appointment.status != 'Cancelled').first()

        if existing:
            flash('This time slot is already booked. Please choose another.', 'warning')
            return render_template(
                'patient/book_appointment.html',
                doctor=doctor, availability=availability
            )

        # Check if patient already has an appointment at the same time
        patient_conflict = Appointment.query.filter_by(
            patient_id=patient.patient_id,
            appointment_date=appt_date,
            appointment_time=appt_time
        ).filter(Appointment.status != 'Cancelled').first()

        if patient_conflict:
            flash('You already have an appointment at this time.', 'warning')
            return render_template(
                'patient/book_appointment.html',
                doctor=doctor, availability=availability
            )

        try:
            appointment = Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor_id,
                appointment_date=appt_date,
                appointment_time=appt_time,
                status='Pending'
            )
            db.session.add(appointment)
            db.session.commit()
            logger.info(
                'Appointment booked: Patient %s with Doctor %s on %s at %s',
                patient.patient_id, doctor_id, appt_date, appt_time
            )
            flash('Appointment booked successfully! Status: Pending confirmation.', 'success')
            return redirect(url_for('patient.history'))

        except Exception as e:
            db.session.rollback()
            logger.error('Appointment booking failed: %s', str(e))
            flash('Failed to book appointment. Please try again.', 'danger')

    return render_template(
        'patient/book_appointment.html',
        doctor=doctor,
        availability=availability
    )


@patient_bp.route('/history')
@role_required('Patient')
def history():
    """View patient's appointment history and prescriptions."""
    patient = Patient.query.get(current_user.linked_id)
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('patient.dashboard'))

    appointments = Appointment.query.filter_by(
        patient_id=patient.patient_id
    ).order_by(Appointment.appointment_date.desc()).all()

    prescriptions = Prescription.query.filter_by(
        patient_id=patient.patient_id
    ).order_by(Prescription.date.desc()).all()

    return render_template(
        'patient/medical_history.html',
        patient=patient,
        appointments=appointments,
        prescriptions=prescriptions
    )


@patient_bp.route('/prescription/<int:prescription_id>/download')
@role_required('Patient')
def download_prescription(prescription_id):
    """Generate a printable prescription page."""
    patient = Patient.query.get(current_user.linked_id)
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('patient.history'))

    prescription = Prescription.query.filter_by(
        prescription_id=prescription_id,
        patient_id=patient.patient_id
    ).first()

    if not prescription:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('patient.history'))

    doctor = Doctor.query.get(prescription.doctor_id)

    # Generate a styled HTML prescription for printing/saving
    html_content = render_template(
        'patient/prescription_print.html',
        prescription=prescription,
        patient=patient,
        doctor=doctor
    )

    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    return response


@patient_bp.route('/slots/<int:doctor_id>/<appointment_date>')
@role_required('Patient')
def get_available_slots(doctor_id, appointment_date):
    """API endpoint to get available slots for a doctor on a specific date."""
    doctor = Doctor.query.get_or_404(doctor_id)

    try:
        appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    except ValueError:
        return {'error': 'Invalid date'}, 400

    availability = {}
    if doctor.availability:
        try:
            availability = json.loads(doctor.availability)
        except json.JSONDecodeError:
            return {'error': 'Invalid availability data'}, 500

    day_name = appt_date.strftime('%a')
    all_slots = availability.get(day_name, [])

    # Get booked slots
    booked = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=appt_date
    ).filter(Appointment.status != 'Cancelled').all()

    booked_times = {a.appointment_time for a in booked}
    available = [s for s in all_slots if s not in booked_times]

    return {'slots': available, 'day': day_name}
