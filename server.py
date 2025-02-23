from flask import Flask, request, send_file, jsonify
import os
import shutil
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)
BASE_DB_PATH = "databases"
os.makedirs(BASE_DB_PATH, exist_ok=True)
CENTRAL_DB = os.path.join(BASE_DB_PATH, "central.db")
USERS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "user1": hashlib.sha256("password1".encode()).hexdigest()
}

def check_auth():
    auth = request.authorization
    if not auth or auth.username not in USERS:
        return False
    hashed_password = hashlib.sha256(auth.password.encode()).hexdigest()
    return USERS[auth.username] == hashed_password

def is_valid_db(file_path):
    try:
        conn = sqlite3.connect(file_path)
        conn.close()
        return True
    except sqlite3.Error:
        return False

def get_db_list():
    db_files = [f for f in os.listdir(BASE_DB_PATH) if f.endswith('.db') and f != 'central.db']
    return [{"name": f, "size": os.path.getsize(os.path.join(BASE_DB_PATH, f))} for f in db_files]

@app.route('/central.db', methods=['GET'])
def get_db():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    if os.path.exists(CENTRAL_DB):
        return send_file(CENTRAL_DB)
    return jsonify({"error": "Central database not found"}), 404

@app.route('/upload', methods=['POST'])
def upload_db():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    if 'file' not in request.files:
        return jsonify({"error": "No file sent"}), 400
    
    file = request.files['file']
    username = request.authorization.username
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_db = os.path.join(BASE_DB_PATH, f"{username}_{timestamp}.db")
    
    file.save(user_db)
    if not is_valid_db(user_db):
        os.remove(user_db)
        return jsonify({"error": "Invalid database file"}), 400
    
    if os.path.exists(CENTRAL_DB):
        shutil.copy(CENTRAL_DB, CENTRAL_DB + f".bak_{timestamp}")
    shutil.copy(user_db, CENTRAL_DB)
    
    return jsonify({"message": "Database uploaded successfully"}), 200

@app.route('/db_list', methods=['GET'])
def list_dbs():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    db_list = get_db_list()
    return jsonify({"databases": db_list}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # پورت دینامیک برای Render
    app.run(host='0.0.0.0', port=port, debug=True)
