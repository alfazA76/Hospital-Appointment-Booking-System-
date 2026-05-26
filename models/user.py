from flask_login import UserMixin
from database.db import db


class User(UserMixin, db.Model):
    """Unified user model for authentication across all roles."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Patient')  # Patient, Doctor, Admin
    linked_id = db.Column(db.Integer, nullable=True)  # FK to patient_id or doctor_id
    is_active_user = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.is_active_user
