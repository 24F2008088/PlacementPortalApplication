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


app = Flask(__name__)

# 1. Enable CORS so the VueJS frontend can communicate with this API
CORS(app)

# 2. Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# 3. Configuration
# NEVER hardcode a real secret key in production, but this is fine for local dev
app.config['SECRET_KEY'] = 'super_secret_jwt_key_v2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Resume Upload Folder Setup
UPLOAD_FOLDER = 'static/resumes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- EMAIL CONFIGURATION (Connecting to Mailpit) ---
app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 1025
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_DEFAULT_SENDER'] = 'admin@placementportal.com'

mail = Mail(app)

# 4. Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

# 5. Celery Configuration
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

# --- REDIS CACHE SETUP ---
# decode_responses=True ensures we get normal strings back instead of byte data
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Force Python to use the absolute path of your specific machine
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXPORT_FOLDER = os.path.join(BASE_DIR, 'static', 'exports')
os.makedirs(EXPORT_FOLDER, exist_ok=True)


# Decorator to check if the user has a valid JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Token is sent in the Authorization header
        if 'Authorization' in request.headers:
            # Format: Bearer <token>
            token = request.headers['Authorization'].split(" ")[1]

        # No token means user is not logged in
        if not token:
            return jsonify({'message': 'Token is missing! Access denied.'}), 401

        try:
            # Decode the token and get the logged-in user
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid or expired!'}), 401

        # Pass the current user to the protected route
        return f(current_user, *args, **kwargs)

    return decorated


# --- ADMIN ROUTES ---

@app.route('/api/admin/stats', methods=['GET'])
@token_required
def get_admin_stats(current_user):
    # Security Check
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
    
    return jsonify({'message': 'Drive rejected and removed.'}), 200


# --- STUDENT ROUTES ---

@app.route('/api/student/drives', methods=['GET'])
@token_required
def get_approved_drives(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403
        
    # 1. Check the Redis Cache FIRST
    cached_drives = cache.get('approved_drives')
    
    if cached_drives:
        print("[CACHE HIT] Serving drives instantly from Redis!")
        return jsonify({'status': 'success', 'data': json.loads(cached_drives)}), 200
        
    # 2. If nothing is in the cache (Cache Miss), query the SQLite database
    print("[CACHE MISS] Fetching from SQLite database...")
    drives = Drive.query.filter_by(status='Approved').all()
    drives_data = [{
        'id': d.id,
        'job_title': d.job_title,
        'company': d.company.username,
        'description': d.description,
        'eligibility': d.eligibility_criteria,
        'deadline': d.deadline
    } for d in drives]
    
    # 3. Save the result to Redis with an expiration time.
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
                'company_name': getattr(drive, 'company_name', 'Company'),
                'job_title': drive.job_title,
                'status': app.status
            })
            
    return jsonify(app_data), 200


# --- COMPANY ROUTES ---

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
        eligibility_criteria=data.get('eligibility'),
        deadline=data.get('deadline'),
        status='Pending'
    )
    
    db.session.add(new_drive)
    db.session.commit()
    
    return jsonify({'message': 'Placement drive created and pending admin approval.'}), 201


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
                'student_name': student.username,
                'status': app.status
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
    
    # --- FIRE THE BACKGROUND EMAIL TASK ---
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
    
    # --- FIRE THE BACKGROUND EMAIL TASK ---
    student = User.query.get(application.student_id)
    drive = Drive.query.get(application.drive_id)
    send_status_email.delay(student.username, current_user.username, drive.job_title, 'REJECTED ❌')
    
    return jsonify({'message': 'Student rejected.'}), 200


# --- CELERY BEAT SCHEDULE ---
celery.conf.beat_schedule = {
    'daily-reminder-job': {
        'task': 'send_daily_reminders',
        'schedule': crontab(hour=9, minute=0), # Runs every day at 9:00 AM
    },
    'monthly-report-job': {
        'task': 'generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=10, minute=0), # Runs 1st of every month at 10:00 AM
    }
}


# --- NEW CELERY BACKGROUND TASKS & ROUTES FOR CSV EXPORT ---

@celery.task(name='app.export_applicants_task')
def export_applicants_task(drive_id):
    applications = Application.query.filter_by(drive_id=drive_id).all()
    
    # Generate a unique filename using your existing EXPORT_FOLDER
    filename = f"applicants_drive_{drive_id}_{uuid.uuid4().hex[:6]}.csv"
    filepath = os.path.join(EXPORT_FOLDER, filename)
    
    # Write the data to the CSV file
    with open(filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Student Name', 'Status']) # CSV Headers
        
        for app_record in applications:
            student = User.query.get(app_record.student_id)
            writer.writerow([student.username, app_record.status])
            
    # Return the static URL path so the frontend can download it
    return f"/static/exports/{filename}"


@app.route('/api/company/export/<int:drive_id>', methods=['POST'])
@token_required
def trigger_company_export(current_user, drive_id):
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied.'}), 403
        
    # Send the task to Redis!
    task = export_applicants_task.delay(drive_id)
    
    return jsonify({'message': 'Export started!', 'task_id': task.id}), 202


@app.route('/api/company/export_status/<task_id>', methods=['GET'])
def get_export_status(task_id):
    # Ask Redis for the task status
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING' or task.state == 'STARTED':
        return jsonify({'status': 'Processing'}), 202
    elif task.state == 'SUCCESS':
        # Send the complete download URL back to Vue
        return jsonify({
            'status': 'Ready', 
            'download_url': f"http://127.0.0.1:5000{task.result}"
        }), 200
    else:
        return jsonify({'status': 'Failed'}), 500
    
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
    # Count how many items need admin attention
    pending_companies = User.query.filter_by(role='company', is_approved=False).count()
    pending_drives = Drive.query.filter_by(status='Pending').count()
    
    # Only send the email if there is actually work to do
    if pending_companies > 0 or pending_drives > 0:
        subject = "Daily Admin Digest: Pending Approvals"
        body = (
            f"Good morning Admin,\n\n"
            f"You have items waiting in the queue that require your approval:\n"
            f"- {pending_companies} Pending Companies\n"
            f"- {pending_drives} Pending Placement Drives\n\n"
            f"Please log in to your Command Center to review them."
        )
        
        # Sending to our default admin testing email
        msg = Message(subject, recipients=['admin@placementportal.com'])
        msg.body = body
        mail.send(msg)
        
        return f"Daily reminder sent: {pending_companies} companies, {pending_drives} drives."
    
    return "No pending approvals today. Email skipped."


# ------------------ Register User ------------------ #

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


# ------------------ Login User ------------------ #

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