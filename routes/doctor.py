import logging
from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from database.db import db
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.prescription import Prescription
from routes.auth import role_required

logger = logging.getLogger(__name__)

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')


@doctor_bp.route('/dashboard')
@role_required('Doctor')
def dashboard():
    """Doctor dashboard with summary metrics."""
    doctor = Doctor.query.get(current_user.linked_id)
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    today = date.today()

    # Today's appointments
    todays_appointments = Appointment.query.filter_by(
        doctor_id=doctor.doctor_id,
        appointment_date=today
    ).order_by(Appointment.appointment_time).all()

    # Pending appointments count
    pending_count = Appointment.query.filter_by(
        doctor_id=doctor.doctor_id,
        status='Pending'
    ).count()

    # Total patients seen (confirmed appointments)
    total_patients = Appointment.query.filter_by(
        doctor_id=doctor.doctor_id,
        status='Confirmed'
    ).count()

    # Total prescriptions written
    total_prescriptions = Prescription.query.filter_by(
        doctor_id=doctor.doctor_id
    ).count()

    return render_template(
        'doctor/dashboard.html',
        doctor=doctor,
        todays_appointments=todays_appointments,
        pending_count=pending_count,
        total_patients=total_patients,
        total_prescriptions=total_prescriptions,
        today=today
    )


@doctor_bp.route('/schedule')
@role_required('Doctor')
def schedule():
    """View doctor's appointment schedule."""
    doctor = Doctor.query.get(current_user.linked_id)
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    # Get filter date (default today)
    filter_date_str = request.args.get('date', '')
    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
        except ValueError:
            filter_date = date.today()
    else:
        filter_date = date.today()

    appointments = Appointment.query.filter_by(
        doctor_id=doctor.doctor_id,
        appointment_date=filter_date
    ).order_by(Appointment.appointment_time).all()

    return render_template(
        'doctor/schedule.html',
        doctor=doctor,
        appointments=appointments,
        filter_date=filter_date
    )


@doctor_bp.route('/appointment/<int:appointment_id>/accept', methods=['POST'])
@role_required('Doctor')
def accept_appointment(appointment_id):
    """Accept a pending appointment."""
    doctor = Doctor.query.get(current_user.linked_id)
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != doctor.doctor_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('doctor.schedule'))

    if appointment.status != 'Pending':
        flash('This appointment is no longer pending.', 'warning')
        return redirect(url_for('doctor.schedule'))

    try:
        appointment.status = 'Confirmed'
        db.session.commit()
        logger.info('Appointment %s confirmed by Dr. %s', appointment_id, doctor.doctor_name)
        flash('Appointment confirmed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error('Failed to confirm appointment %s: %s', appointment_id, str(e))
        flash('Failed to confirm appointment.', 'danger')

    return redirect(url_for('doctor.schedule'))


@doctor_bp.route('/appointment/<int:appointment_id>/reject', methods=['POST'])
@role_required('Doctor')
def reject_appointment(appointment_id):
    """Reject a pending appointment."""
    doctor = Doctor.query.get(current_user.linked_id)
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != doctor.doctor_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('doctor.schedule'))

    if appointment.status != 'Pending':
        flash('This appointment is no longer pending.', 'warning')
        return redirect(url_for('doctor.schedule'))

    try:
        appointment.status = 'Cancelled'
        db.session.commit()
        logger.info('Appointment %s rejected by Dr. %s', appointment_id, doctor.doctor_name)
        flash('Appointment has been rejected.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.error('Failed to reject appointment %s: %s', appointment_id, str(e))
        flash('Failed to reject appointment.', 'danger')

    return redirect(url_for('doctor.schedule'))


@doctor_bp.route('/prescription/<int:appointment_id>', methods=['GET', 'POST'])
@role_required('Doctor')
def write_prescription(appointment_id):
    """Write a prescription for a specific appointment."""
    doctor = Doctor.query.get(current_user.linked_id)
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != doctor.doctor_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('doctor.schedule'))

    patient = Patient.query.get(appointment.patient_id)

    # Check if prescription already exists
    existing_prescription = Prescription.query.filter_by(
        appointment_id=appointment_id
    ).first()

    if request.method == 'POST':
        medicines = request.form.get('medicines', '').strip()
        remarks = request.form.get('remarks', '').strip()

        if not medicines:
            flash('Medicines field is required.', 'warning')
            return render_template(
                'doctor/prescription_form.html',
                doctor=doctor, patient=patient, appointment=appointment,
                existing=existing_prescription
            )

        try:
            if existing_prescription:
                existing_prescription.medicines = medicines
                existing_prescription.remarks = remarks
                existing_prescription.date = date.today()
                flash('Prescription updated successfully.', 'success')
            else:
                prescription = Prescription(
                    patient_id=patient.patient_id,
                    doctor_id=doctor.doctor_id,
                    appointment_id=appointment_id,
                    medicines=medicines,
                    remarks=remarks,
                    date=date.today()
                )
                db.session.add(prescription)
                flash('Prescription created successfully.', 'success')

            db.session.commit()
            logger.info(
                'Prescription written by Dr. %s for patient %s (appointment %s)',
                doctor.doctor_name, patient.patient_id, appointment_id
            )
            return redirect(url_for('doctor.schedule'))

        except Exception as e:
            db.session.rollback()
            logger.error('Failed to save prescription: %s', str(e))
            flash('Failed to save prescription.', 'danger')

    return render_template(
        'doctor/prescription_form.html',
        doctor=doctor, patient=patient, appointment=appointment,
        existing=existing_prescription
    )
