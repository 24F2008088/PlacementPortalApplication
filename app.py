from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from models import db, User, Drive, Application
import os
import jwt
import datetime
from functools import wraps
from celery import Celery
from celery.schedules import crontab
import redis
import json
import csv
import uuid
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Core configurations
CORS(app)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'super_secret_jwt_key_v2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/resumes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mailpit setup
app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 1025
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_DEFAULT_SENDER'] = 'admin@placementportal.com'

mail = Mail(app)

# Init DB
db.init_app(app)
with app.app_context():
    db.create_all()

# Celery & Redis setup
app.config['broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

def make_celery(app):
    celery = Celery(
        app.import_name, 
        backend=app.config['result_backend'],
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXPORT_FOLDER = os.path.join(BASE_DIR, 'static', 'exports')
os.makedirs(EXPORT_FOLDER, exist_ok=True)


# JWT Auth Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing! Access denied.'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid or expired!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


# --- Admin Routes ---

@app.route('/api/admin/stats', methods=['GET'])
@token_required
def get_admin_stats(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    stats = {
        'total_students': User.query.filter_by(role='student').count(),
        'total_companies': User.query.filter_by(role='company').count(),
        'total_drives': Drive.query.count(),
        'total_applications': Application.query.count()
    }
    return jsonify({'status': 'success', 'data': stats}), 200

@app.route('/api/admin/pending_companies', methods=['GET'])
@token_required
def get_pending_companies(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
    
    companies = User.query.filter_by(role='company', is_approved=False).all()
    companies_data = [{'id': c.id, 'username': c.username} for c in companies]
    return jsonify(companies_data), 200

@app.route('/api/admin/approve_company/<int:company_id>', methods=['POST'])
@token_required
def approve_company(current_user, company_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    company = User.query.get(company_id)
    if not company:
        return jsonify({'message': 'Company not found.'}), 404
        
    company.is_approved = True
    db.session.commit()
    return jsonify({'message': 'Company approved successfully!'}), 200

@app.route('/api/admin/reject_company/<int:company_id>', methods=['POST'])
@token_required
def reject_company(current_user, company_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    company = User.query.get(company_id)
    if not company:
        return jsonify({'message': 'Company not found.'}), 404
        
    db.session.delete(company)
    db.session.commit()
    return jsonify({'message': 'Company rejected and removed.'}), 200

@app.route('/api/admin/pending_drives', methods=['GET'])
@token_required
def get_pending_drives(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
    
    drives = Drive.query.filter_by(status='Pending').all()
    drives_data = [{
        'id': d.id, 
        'job_title': d.job_title, 
        'description': d.description
    } for d in drives]
    return jsonify(drives_data), 200

@app.route('/api/admin/approve_drive/<int:drive_id>', methods=['POST'])
@token_required
def approve_drive(current_user, drive_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({'message': 'Drive not found.'}), 404
        
    drive.status = 'Approved'
    db.session.commit()
    cache.delete('approved_drives')
    
    
    send_new_drive_alert.delay(drive.company.username, drive.job_title, drive.deadline)
    
    return jsonify({'message': 'Drive approved successfully!'}), 200

@app.route('/api/admin/reject_drive/<int:drive_id>', methods=['POST'])
@token_required
def reject_drive(current_user, drive_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({'message': 'Drive not found.'}), 404
        
    db.session.delete(drive)
    db.session.commit()
    cache.delete('approved_drives')
    return jsonify({'message': 'Drive rejected and removed.'}), 200

@app.route('/api/admin/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
    
    # Fetch everyone except the admin
    users = User.query.filter(User.role != 'admin').all()
    user_data = [{
        'id': u.id,
        'username': u.username,
        'role': u.role,
        'is_approved': u.is_approved,
        'is_blacklisted': u.is_blacklisted
    } for u in users]
    
    return jsonify(user_data), 200

@app.route('/api/admin/toggle_blacklist/<int:user_id>', methods=['POST'])
@token_required
def toggle_blacklist(current_user, user_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found.'}), 404
        
    # Flip the boolean status
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    
    status = "blacklisted" if user.is_blacklisted else "restored"
    return jsonify({'message': f'User {status} successfully.'}), 200


@app.route('/api/admin/all_drives', methods=['GET'])
@token_required
def admin_all_drives(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    drives = Drive.query.all()
    drives_data = [{
        'id': d.id,
        'company': d.company.username if d.company else 'Unknown',
        'job_title': d.job_title,
        'ctc': d.ctc,
        'deadline': d.deadline,
        'status': d.status
    } for d in drives]
    
    return jsonify(drives_data), 200

@app.route('/api/admin/all_applications', methods=['GET'])
@token_required
def admin_all_applications(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    apps = Application.query.all()
    app_data = []
    
    for app_record in apps:
        student = User.query.get(app_record.student_id)
        drive = Drive.query.get(app_record.drive_id)
        
        app_data.append({
            'id': app_record.id,
            'student_name': student.username if student else 'Unknown',
            'company_name': drive.company.username if drive and drive.company else 'Unknown',
            'job_title': drive.job_title if drive else 'Unknown',
            'status': app_record.status
        })
        
    return jsonify(app_data), 200

# --- Student Routes ---

@app.route('/api/student/profile', methods=['GET', 'POST'])
@token_required
def student_profile(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403
        
    if request.method == 'GET':
        return jsonify({
            'full_name': current_user.full_name,
            'contact_info': current_user.contact_info,
            'branch': current_user.branch,
            'cgpa': current_user.cgpa,
            'resume_file': current_user.resume_file
        }), 200
        
    if request.method == 'POST':
        data = request.get_json()
        current_user.full_name = data.get('full_name', current_user.full_name)
        current_user.contact_info = data.get('contact_info', current_user.contact_info)
        current_user.branch = data.get('branch', current_user.branch)
        
        try:
            current_user.cgpa = float(data.get('cgpa')) if data.get('cgpa') else current_user.cgpa
        except ValueError:
            return jsonify({'message': 'CGPA must be a number.'}), 400
            
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'}), 200

@app.route('/api/student/upload_resume', methods=['POST'])
@token_required
def upload_resume(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403

    if 'resume' not in request.files:
        return jsonify({'message': 'No file part in the request.'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(f"user_{current_user.id}_resume.pdf")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        current_user.resume_file = f"/static/resumes/{filename}"
        db.session.commit()

        return jsonify({
            'message': 'Resume uploaded successfully!',
            'resume_url': current_user.resume_file
        }), 200

    return jsonify({'message': 'Invalid file type. Only PDFs are allowed.'}), 400

@app.route('/api/student/drives', methods=['GET'])
@token_required
def get_approved_drives(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403
        
    cached_drives = cache.get('approved_drives')
    if cached_drives:
        return jsonify({'status': 'success', 'data': json.loads(cached_drives)}), 200
        
    drives = Drive.query.filter_by(status='Approved').all()
    drives_data = [{
        'id': d.id,
        'job_title': d.job_title,
        'company': d.company.username,
        'description': d.description,
        'eligibility_criteria': d.eligibility_criteria,
        'ctc': d.ctc,
        'deadline': d.deadline
    } for d in drives]
    
    cache.setex('approved_drives', 300, json.dumps(drives_data))
    return jsonify({'status': 'success', 'data': drives_data}), 200

@app.route('/api/student/apply/<int:drive_id>', methods=['POST'])
@token_required
def apply_for_drive(current_user, drive_id):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403
        
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({'message': 'Drive not found.'}), 404
        
    existing_application = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing_application:
        return jsonify({'message': 'You have already applied for this drive!'}), 400
        
    new_app = Application(student_id=current_user.id, drive_id=drive_id, status='Applied')
    db.session.add(new_app)
    db.session.commit()
    return jsonify({'message': 'Successfully applied to the placement drive!'}), 201

@app.route('/api/student/my_applications', methods=['GET'])
@token_required
def get_my_applications(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403

    applications = Application.query.filter_by(student_id=current_user.id).all()
    app_data = []
    for app in applications:
        drive = Drive.query.get(app.drive_id)
        if drive:
            app_data.append({
            'application_id': app.id,
            'drive_id': app.drive_id,                
            'company_name': drive.company.username, 
            'job_title': drive.job_title,
            'status': app.status
        })
            
    return jsonify(app_data), 200

@app.route('/api/student/export', methods=['POST'])
@token_required
def trigger_student_export(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied.'}), 403
        
    task = export_student_applications_task.delay(current_user.id)
    return jsonify({'message': 'Export started!', 'task_id': task.id}), 202

@app.route('/api/student/export_status/<task_id>', methods=['GET'])
def get_student_export_status(task_id):
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING' or task.state == 'STARTED':
        return jsonify({'status': 'Processing'}), 202
    elif task.state == 'SUCCESS':
        return jsonify({
            'status': 'Ready', 
            'download_url': f"http://127.0.0.1:5000{task.result}"
        }), 200
    else:
        return jsonify({'status': 'Failed'}), 500


# --- Company Routes ---

@app.route('/api/company/stats', methods=['GET'])
@token_required
def get_company_stats(current_user):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
        
    drives = Drive.query.filter_by(company_id=current_user.id).all()
    drive_ids = [d.id for d in drives]
    
    total_applicants = 0
    total_hired = 0
    if drive_ids:
        total_applicants = Application.query.filter(Application.drive_id.in_(drive_ids)).count()
        total_hired = Application.query.filter(Application.drive_id.in_(drive_ids), Application.status == 'Accepted').count()
        
    return jsonify({
        'total_drives': len(drives),
        'total_applicants': total_applicants,
        'total_hired': total_hired
    }), 200

@app.route('/api/company/my_drives', methods=['GET'])
@token_required
def get_my_drives(current_user):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
    drives = Drive.query.filter_by(company_id=current_user.id).all()
    return jsonify([{'id': d.id, 'job_title': d.job_title, 'status': d.status} for d in drives]), 200

@app.route('/api/company/profile', methods=['GET', 'POST'])
@token_required
def company_profile(current_user):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
        
    if request.method == 'GET':
        return jsonify({
            'description': current_user.description or '',
            'industry': current_user.industry or '',
            'website': current_user.website or ''
        }), 200
        
    if request.method == 'POST':
        data = request.get_json()
        current_user.description = data.get('description', current_user.description)
        current_user.industry = data.get('industry', current_user.industry)
        current_user.website = data.get('website', current_user.website)
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'}), 200


@app.route('/api/company/drive', methods=['POST'])
@token_required
def create_placement_drive(current_user):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied. Companies only.'}), 403
        
    if not current_user.is_approved:
        return jsonify({'message': 'Your company profile is pending admin approval.'}), 403
        
    data = request.get_json()
    new_drive = Drive(
        company_id=current_user.id,
        job_title=data.get('job_title'),
        description=data.get('description'),
        eligibility_criteria=data.get('eligibility_criteria'),
        ctc=data.get('ctc'),
        deadline=data.get('deadline'),
        status='Pending'
    )
    db.session.add(new_drive)
    db.session.commit()
    return jsonify({'message': 'Placement drive created and pending admin approval.'}), 201

@app.route('/api/company/close_drive/<int:drive_id>', methods=['POST'])
@token_required
def close_drive(current_user, drive_id):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
        
    drive = Drive.query.get(drive_id)
    
    
    if not drive or drive.company_id != current_user.id:
        return jsonify({'message': 'Drive not found.'}), 404
        
    drive.status = 'Closed'
    db.session.commit()
    
    
    cache.delete('approved_drives')
    
    return jsonify({'message': 'Drive closed successfully!'}), 200

@app.route('/api/company/applicants', methods=['GET'])
@token_required
def get_company_applicants(current_user):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied. Companies only.'}), 403

    my_drives = Drive.query.filter_by(company_id=current_user.id).all()
    applicants_data = []
    
    for drive in my_drives:
        applications = Application.query.filter_by(drive_id=drive.id).all()
        for app in applications:
            student = User.query.get(app.student_id)
            applicants_data.append({
                'application_id': app.id,
                'job_title': drive.job_title,
                'student_name': student.full_name or student.username,
                'branch': student.branch or 'Not provided',
                'cgpa': student.cgpa or 'N/A',
                'contact_info': student.contact_info or 'Not provided',
                'resume_file': student.resume_file,
                'status': app.status,
                'drive_id': drive.id
            })
            
    return jsonify(applicants_data), 200

@app.route('/api/company/accept_applicant/<int:application_id>', methods=['POST'])
@token_required
def accept_applicant(current_user, application_id):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
        
    application = Application.query.get(application_id)
    if not application:
        return jsonify({'message': 'Application not found.'}), 404
        
    application.status = 'Accepted'
    db.session.commit()
    
    student = User.query.get(application.student_id)
    drive = Drive.query.get(application.drive_id)
    send_status_email.delay(student.username, current_user.username, drive.job_title, 'ACCEPTED 🎉')
    
    return jsonify({'message': 'Student accepted!'}), 200

@app.route('/api/company/reject_applicant/<int:application_id>', methods=['POST'])
@token_required
def reject_applicant(current_user, application_id):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
        
    application = Application.query.get(application_id)
    if not application:
        return jsonify({'message': 'Application not found.'}), 404
        
    application.status = 'Rejected'
    db.session.commit()
    
    student = User.query.get(application.student_id)
    drive = Drive.query.get(application.drive_id)
    send_status_email.delay(student.username, current_user.username, drive.job_title, 'REJECTED ❌')
    
    return jsonify({'message': 'Student rejected.'}), 200


# --- Background Tasks & Email Routing ---

celery.conf.beat_schedule = {
    'daily-student-reminder-job': {
        'task': 'app.send_daily_reminders',
        'schedule': crontab(hour=9, minute=0), 
    },
    'monthly-admin-report-job': {
        'task': 'app.generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=10, minute=0), 
    }
}


@celery.task(name='app.send_new_drive_alert')
def send_new_drive_alert(company_name, job_title, deadline):
    students = User.query.filter_by(role='student').all()
    if not students:
        return "No students to notify."
        
    subject = f"New Placement Drive: {company_name} is hiring!"
    body = (
        f"Great news!\n\n"
        f"A new placement drive by {company_name} for the role of '{job_title}' has just been approved and is now live.\n"
        f"The deadline to apply is {deadline}.\n\n"
        f"Log in to your Student Dashboard to check the eligibility criteria and apply!"
    )
    
    with mail.connect() as conn:
        for student in students:
            student_email = f"{student.username.replace(' ', '').lower()}@student.edu"
            msg = Message(subject, recipients=[student_email], body=body)
            conn.send(msg)
            
    return f"Alert sent to {len(students)} students."


@celery.task(name='app.export_student_applications_task')
def export_student_applications_task(student_id):
    applications = Application.query.filter_by(student_id=student_id).all()
    student = User.query.get(student_id)
    
    filename = f"application_history_{student.username}_{uuid.uuid4().hex[:6]}.csv"
    filepath = os.path.join(EXPORT_FOLDER, filename)
    
    with open(filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Application Status', 'Date Exported']) 
        
        for app_record in applications:
            drive = Drive.query.get(app_record.drive_id)
            company_name = drive.company.username if drive and drive.company else "N/A"
            drive_title = drive.job_title if drive else "N/A"
            date_exported = datetime.datetime.now().strftime("%Y-%m-%d") 
            
            writer.writerow([student.id, company_name, drive_title, app_record.status, date_exported])
            
    return f"/static/exports/{filename}"
    
@celery.task(name='app.send_status_email')
def send_status_email(student_username, company_name, job_title, status):
    student_email = f"{student_username.replace(' ', '').lower()}@student.edu"
    subject = f"Application Update: {company_name} - {job_title}"
    body = f"Hello {student_username},\n\nYour application for the role of {job_title} at {company_name} has been marked as: {status}.\n\nLog in to your dashboard to view more details."
    
    msg = Message(subject, recipients=[student_email])
    msg.body = body
    mail.send(msg)
    return f"Email sent to {student_email}"

@celery.task(name='app.send_daily_reminders')
def send_daily_reminders():
    active_drives = Drive.query.filter_by(status='Approved').all()
    if not active_drives:
        return "No active drives. Reminders skipped."

    students = User.query.filter_by(role='student').all()
    drive_list_text = "\n".join([f"- {d.company.username}: {d.job_title} (Deadline: {d.deadline})" for d in active_drives])
    
    with mail.connect() as conn:
        for student in students:
            student_email = f"{student.username.replace(' ', '').lower()}@student.edu"
            subject = "Daily Reminder: Upcoming Placement Deadlines"
            body = f"Hello {student.full_name or student.username},\n\nDon't forget to apply for these active placement drives before they close:\n\n{drive_list_text}\n\nLog into your dashboard to apply!"
            
            msg = Message(subject, recipients=[student_email], body=body)
            conn.send(msg)
            
    return f"Daily reminders sent to {len(students)} students."

@celery.task(name='app.generate_monthly_report')
def generate_monthly_report():
    total_drives = Drive.query.count()
    total_applications = Application.query.count()
    total_selected = Application.query.filter_by(status='Accepted').count()
    
    subject = "Monthly Placement Activity Report"
    
    html_body = f"""
    <h2>Monthly Placement Activity Report</h2>
    <p>Here is the summary of the institute's placement activities for this month:</p>
    <ul>
        <li><strong>Total Drives Conducted:</strong> {total_drives}</li>
        <li><strong>Total Students Applied:</strong> {total_applications}</li>
        <li><strong>Total Students Selected:</strong> {total_selected}</li>
    </ul>
    <p>Log in to the Admin Command Center for more details.</p>
    """
    
    msg = Message(subject, recipients=['admin@placementportal.com'])
    msg.html = html_body
    mail.send(msg)
    
    return "Monthly HTML report sent to admin."


# --- Authentication Routes ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password') or not data.get('role'):
        return jsonify({'message': 'Missing required fields.'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists.'}), 400

    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    is_approved = True if data['role'] == 'student' else False

    new_user = User(
        username=data['username'],
        password=hashed_pw,
        role=data['role'],
        is_approved=is_approved
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing credentials.'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password.'}), 401

    if user.is_blacklisted:
        return jsonify({'message': 'Account restricted by Administrator.'}), 403

    if user.role == 'company' and not user.is_approved:
        return jsonify({'message': 'Company profile is pending Admin approval.'}), 403

    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'role': user.role
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)