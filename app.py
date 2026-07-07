from flask import Flask, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from models import db, User, Drive, Application
import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify

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

# --- API Endpoints Will Go Here ---

@app.route('/api/health', methods=['GET'])
def health_check():
    """A simple endpoint to test if the API is running."""
    return jsonify({"status": "success", "message": "Placement API V2 is running smoothly!"}), 200



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
        
    drives = Drive.query.filter_by(status='Approved').all()
    drives_data = [{
        'id': d.id,
        'job_title': d.job_title,
        'company': d.company.username,
        'description': d.description,
        'eligibility': d.eligibility_criteria,
        'deadline': d.deadline
    } for d in drives]
    
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)