from database.db import db


class Doctor(db.Model):
    """Doctor profile model."""
    __tablename__ = 'doctors'

    doctor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Text, nullable=True)  # JSON string: {"Mon": ["09:00","10:00"], ...}
    contact = db.Column(db.String(15), nullable=True)

    # Relationships
    appointments = db.relationship(
        'Appointment', backref='doctor', lazy=True,
        cascade='all, delete-orphan'
    )
    prescriptions = db.relationship(
        'Prescription', backref='doctor', lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Doctor {self.doctor_name} - {self.specialization}>'
