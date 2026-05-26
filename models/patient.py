from database.db import db


class Patient(db.Model):
    """Patient profile model."""
    __tablename__ = 'patients'

    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=True)

    # Relationships
    appointments = db.relationship(
        'Appointment', backref='patient', lazy=True,
        cascade='all, delete-orphan'
    )
    prescriptions = db.relationship(
        'Prescription', backref='patient', lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Patient {self.full_name}>'
