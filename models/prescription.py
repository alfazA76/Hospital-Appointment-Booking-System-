from datetime import date
from database.db import db


class Prescription(db.Model):
    """Prescription model linked to patient, doctor, and appointment."""
    __tablename__ = 'prescriptions'

    prescription_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('patients.patient_id', ondelete='CASCADE'),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctors.doctor_id', ondelete='CASCADE'),
        nullable=False
    )
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointments.appointment_id', ondelete='SET NULL'),
        nullable=True
    )
    medicines = db.Column(db.Text, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)

    # Relationship to appointment
    appointment = db.relationship('Appointment', backref='prescription', lazy=True)

    def __repr__(self):
        return f'<Prescription {self.prescription_id} for Patient {self.patient_id}>'
