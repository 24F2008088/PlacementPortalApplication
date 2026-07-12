from flask import Flask, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from models import db, User, Drive, Application
import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from celery import Celery
from celery.schedules import crontab
#from tasks import export_student_applications_csv
import redis
import json


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

# 4. Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

# 5. Celery Configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

def make_celery(app):
    celery = Celery(
        app.import_name, 
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    # Ensure Celery tasks run within the Flask app context (crucial for DB access)
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

# Ensure export directory exists for async tasks
EXPORT_FOLDER = 'static/exports'
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


# PROTECTED API ENDPOINTS


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

# --- ASYNC TRIGGER ENDPOINT ---
@app.route('/api/student/export', methods=['POST'])
@token_required
def trigger_csv_export(current_user):
    # if current_user.role != 'student':
    #     return jsonify({'message': 'Access denied. Students only.'}), 403
    
    # task = export_student_applications_csv.delay(current_user.id, current_user.username)
    
    # return jsonify({
    #     'message': 'CSV Export started in the background. You will be alerted when it is ready.',
    #     'task_id': task.id
    # }), 202
    
    # Temporary return to keep the server happy
    return jsonify({'message': 'Export feature temporarily disabled'}), 200







# ------------------ Register User ------------------ #

@app.route('/api/register', methods=['POST'])
def register():

    # Get data sent from frontend
    data = request.get_json()

    # Check if all required fields are provided
    if not data or not data.get('username') or not data.get('password') or not data.get('role'):
        return jsonify({'message': 'Missing required fields.'}), 400

    # Don't allow duplicate usernames
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists.'}), 400

    # Hash password before storing it in the database
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # Students are approved automatically, companies need admin approval
    is_approved = True if data['role'] == 'student' else False

    # Create new user object
    new_user = User(
        username=data['username'],
        password=hashed_pw,
        role=data['role'],
        is_approved=is_approved
    )

    # Save user to database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully!'}), 201


# ------------------ Login User ------------------ #

@app.route('/api/login', methods=['POST'])
def login():

    # Read login details from request
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing credentials.'}), 400

    # Find user by username
    user = User.query.filter_by(username=data['username']).first()

    # Check if username exists and password matches
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password.'}), 401

    # Prevent blacklisted users from logging in
    if user.is_blacklisted:
        return jsonify({'message': 'Account restricted by Administrator.'}), 403

    # Companies must be approved before they can log in
    if user.role == 'company' and not user.is_approved:
        return jsonify({'message': 'Company profile is pending Admin approval.'}), 403

    # Generate JWT token valid for 24 hours
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    # Send token back to frontend
    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'role': user.role
    }), 200

# --- ADMIN ROUTES ---

@app.route('/api/admin/pending_companies', methods=['GET'])
@token_required
def get_pending_companies(current_user):
    # Security check: Only admins allowed
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
    
    # Find all users who are companies AND have not been approved yet
    companies = User.query.filter_by(role='company', is_approved=False).all()
    
    # Format the data to send back to Vue
    companies_data = [{'id': c.id, 'username': c.username} for c in companies]
    return jsonify(companies_data), 200


@app.route('/api/admin/approve_company/<int:company_id>', methods=['POST'])
@token_required
def approve_company(current_user, company_id):
    # Security check
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    company = User.query.get(company_id)
    if not company:
        return jsonify({'message': 'Company not found.'}), 404
        
    # Flip the switch to approve them!
    company.is_approved = True
    db.session.commit()
    
    return jsonify({'message': 'Company approved successfully!'}), 200

@app.route('/api/admin/reject_company/<int:company_id>', methods=['POST'])
@token_required
def reject_company(current_user, company_id):
    # Security check
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
        
    company = User.query.get(company_id)
    if not company:
        return jsonify({'message': 'Company not found.'}), 404
        
    # Delete the rejected company from the database entirely
    db.session.delete(company)
    db.session.commit()
    
    return jsonify({'message': 'Company rejected and removed.'}), 200

# --- ADMIN ROUTES FOR DRIVES ---

@app.route('/api/admin/pending_drives', methods=['GET'])
@token_required
def get_pending_drives(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
    
    # Fetch all drives that are still marked as 'Pending'
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
        
    # Change the status so students can see it!
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
        
    # Delete the rejected drive
    db.session.delete(drive)
    db.session.commit()
    
    return jsonify({'message': 'Drive rejected and removed.'}), 200

# --- STUDENT ROUTES ---

@app.route('/api/student/apply/<int:drive_id>', methods=['POST'])
@token_required
def apply_for_drive(current_user, drive_id):
    # Security check
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403
        
    # Check if the drive actually exists
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({'message': 'Drive not found.'}), 404
        
    # Prevent duplicate applications
    existing_application = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing_application:
        return jsonify({'message': 'You have already applied for this drive!'}), 400
        
    # Create the new application
    new_app = Application(student_id=current_user.id, drive_id=drive_id, status='Applied')
    db.session.add(new_app)
    db.session.commit()
    
    return jsonify({'message': 'Successfully applied to the placement drive!'}), 201

@app.route('/api/student/my_applications', methods=['GET'])
@token_required
def get_my_applications(current_user):
    if current_user.role != 'student':
        return jsonify({'message': 'Access denied. Students only.'}), 403

    # Find all applications for this specific student
    applications = Application.query.filter_by(student_id=current_user.id).all()
    
    app_data = []
    for app in applications:
        drive = Drive.query.get(app.drive_id)
        if drive:
            app_data.append({
                'application_id': app.id,
                # Using our fallback just in case the company name isn't stored
                'company_name': getattr(drive, 'company_name', 'Company'),
                'job_title': drive.job_title,
                'status': app.status
            })
            
    return jsonify(app_data), 200

#Company routes

@app.route('/api/company/applicants', methods=['GET'])
@token_required
def get_company_applicants(current_user):
    # Security check
    if current_user.role != 'company':
        return jsonify({'message': 'Access denied. Companies only.'}), 403

    # 1. Find all drives posted by this specific company
    my_drives = Drive.query.filter_by(company_id=current_user.id).all()
    
    applicants_data = []
    
    # 2. Loop through the drives and find the students who applied
    for drive in my_drives:
        applications = Application.query.filter_by(drive_id=drive.id).all()
        for app in applications:
            # Look up the student's username
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
    
    return jsonify({'message': 'Student rejected.'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)