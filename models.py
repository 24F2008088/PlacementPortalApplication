from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'student', 'company'
    
    
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    
    full_name = db.Column(db.String(150))
    contact_info = db.Column(db.String(150))
    branch = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    resume_file = db.Column(db.String(255))
    

    description = db.Column(db.String(255))
    industry = db.Column(db.String(255))
    website = db.Column(db.String(255))
    
    
    drives = db.relationship('Drive', backref='company', lazy=True, cascade="all, delete-orphan")
    applications = db.relationship('Application', backref='student', lazy=True, cascade="all, delete-orphan")


class Drive(db.Model):
    __tablename__ = 'drive'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    job_title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.String(100))
    
    
    ctc = db.Column(db.String(50)) 
    
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pending') # Pending, Approved
    
    
    applications = db.relationship('Application', backref='drive', lazy=True, cascade="all, delete-orphan")


class Application(db.Model):
    __tablename__ = 'application'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Applied') # Applied, Accepted, Rejected