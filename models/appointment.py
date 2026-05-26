from database.db import db


class Appointment(db.Model):
    """Appointment model linking patients and doctors."""
    __tablename__ = 'appointments'

    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(10), nullable=False)  # HH:MM format
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Confirmed, Cancelled

    def __repr__(self):
        return f'<Appointment {self.appointment_id} - {self.status}>'
