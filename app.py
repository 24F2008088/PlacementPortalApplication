from flask import Flask, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from models import db, User, Drive, Application
import os

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)