from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. Updated User Table (Admin, Companies, and Students)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'company', or 'student'
    is_approved = db.Column(db.Boolean, default=False) 
    is_blacklisted = db.Column(db.Boolean, default=False) 

    # --- STUDENT SPECIFIC FIELDS ---
    full_name = db.Column(db.String(100))
    contact_info = db.Column(db.String(15))
    branch = db.Column(db.String(50))
    cgpa = db.Column(db.Float)
    resume_file = db.Column(db.String(200)) # Stores the filename of the uploaded PDF

    # --- COMPANY SPECIFIC FIELDS ---
    hr_contact = db.Column(db.String(15))
    website = db.Column(db.String(100))

# 2. Placement Drive Table
class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text)
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pending')

    # this allows drive.company.username to work
    company = db.relationship('User', backref='drives')

# 3. Updated Application Table
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow) # For history tracking 
    status = db.Column(db.String(20), default='Applied') # Applied, Shortlisted, Selected, Rejected
    
    # Establish relationship to access drive details from application object 
    drive = db.relationship('Drive', backref='applications')
    student = db.relationship('User', backref='my_applications')