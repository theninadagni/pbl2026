"""
Cloud-Based Video Streaming Application with User Authentication
A complete video upload, management, and streaming platform with user login

Requirements:
pip install flask flask-cors werkzeug pillow bcrypt

Run: python app.py
Access: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify, send_file, Response, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import mimetypes
import bcrypt
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads/videos'
app.config['METADATA_FILE'] = 'uploads/metadata.json'
app.config['USERS_FILE'] = 'uploads/users.json'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_users():
    if os.path.exists(app.config['USERS_FILE']):
        with open(app.config['USERS_FILE'], 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    os.makedirs(os.path.dirname(app.config['USERS_FILE']), exist_ok=True)
    with open(app.config['USERS_FILE'], 'w') as f:
        json.dump(users, f, indent=2)

def load_metadata():
    if os.path.exists(app.config['METADATA_FILE']):
        with open(app.config['METADATA_FILE'], 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    os.makedirs(os.path.dirname(app.config['METADATA_FILE']), exist_ok=True)
    with open(app.config['METADATA_FILE'], 'w') as f:
        json.dump(metadata, f, indent=2)

def get_file_size(filepath):
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Login/Register Page Template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Video Streaming Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .auth-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input[type="text"],
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
            margin-top: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .toggle-form {
            text-align: center;
            margin-top: 20px;
            color: #666;
        }
        .toggle-form a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .toggle-form a:hover {
            text-decoration: underline;
        }
        .message {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            display: block;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            display: block;
        }
        .form-container {
            display: none;
        }
        .form-container.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <h1>🎬 Video Stream</h1>
        <p class="subtitle">Your Personal Cloud Video Platform</p>
        
        <div id="message" class="message"></div>

        <!-- Login Form -->
        <div id="loginForm" class="form-container active">
            <h2 style="margin-bottom: 20px; color: #333;">Login</h2>
            <form onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="loginUsername" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="loginPassword" required>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
            <div class="toggle-form">
                Don't have an account? <a href="#" onclick="toggleForm()">Sign Up</a>
            </div>
        </div>

        <!-- Register Form -->
        <div id="registerForm" class="form-container">
            <h2 style="margin-bottom: 20px; color: #333;">Create Account</h2>
            <form onsubmit="handleRegister(event)">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" id="registerName" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="registerEmail" required>
                </div>
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="registerUsername" required minlength="3">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="registerPassword" required minlength="6">
                </div>
                <button type="submit" class="btn">Create Account</button>
            </form>
            <div class="toggle-form">
                Already have an account? <a href="#" onclick="toggleForm()">Login</a>
            </div>
        </div>
    </div>

    <script>
        function toggleForm() {
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const message = document.getElementById('message');
            
            loginForm.classList.toggle('active');
            registerForm.classList.toggle('active');
            message.className = 'message';
        }

        function showMessage(text, type) {
            const message = document.getElementById('message');
            message.textContent = text;
            message.className = 'message ' + type;
            setTimeout(() => {
                message.className = 'message';
            }, 5000);
        }

        function handleLogin(event) {
            event.preventDefault();
            
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;

            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/dashboard';
                } else {
                    showMessage(data.message, 'error');
                }
            })
            .catch(error => {
                showMessage('Login failed. Please try again.', 'error');
            });
        }

        function handleRegister(event) {
            event.preventDefault();
            
            const name = document.getElementById('registerName').value;
            const email = document.getElementById('registerEmail').value;
            const username = document.getElementById('registerUsername').value;
            const password = document.getElementById('registerPassword').value;

            fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, username, password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    setTimeout(() => {
                        toggleForm();
                    }, 1500);
                } else {
                    showMessage(data.message, 'error');
                }
            })
            .catch(error => {
                showMessage('Registration failed. Please try again.', 'error');
            });
        }
    </script>
</body>
</html>
"""

# Main App Template
APP_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Video Streaming Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .navbar {
            background: white;
            padding: 15px 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar h1 {
            color: #667eea;
            font-size: 1.8em;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .username {
            color: #333;
            font-weight: 600;
        }
        .btn-logout {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }
        .btn-logout:hover {
            transform: translateY(-2px);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .upload-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-area:hover {
            background: #f8f9ff;
            border-color: #764ba2;
        }
        .upload-area.dragover {
            background: #e8ebff;
            border-color: #667eea;
        }
        input[type="file"] {
            display: none;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
            margin: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 20px;
            display: none;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .video-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        .video-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .video-thumbnail {
            width: 100%;
            height: 180px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 48px;
        }
        .video-info {
            padding: 15px;
        }
        .video-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .video-owner {
            font-size: 13px;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .video-meta {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        .video-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn-small {
            padding: 8px 15px;
            font-size: 14px;
            flex: 1;
        }
        .btn-delete {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: white;
            padding: 20px;
            border-radius: 15px;
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
        }
        video {
            width: 100%;
            max-height: 70vh;
            border-radius: 10px;
        }
        .close-modal {
            float: right;
            font-size: 30px;
            cursor: pointer;
            color: #666;
        }
        .message {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            display: block;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            display: block;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>🎬 Video Streaming Platform</h1>
        <div class="user-info">
            <span class="username">👤 {{ username }}</span>
            <button class="btn-logout" onclick="logout()">Logout</button>
        </div>
    </div>

    <div class="container">
        <div class="upload-section">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="videoCount">0</div>
                    <div class="stat-label">Total Videos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalSize">0 MB</div>
                    <div class="stat-label">Storage Used</div>
                </div>
            </div>
        </div>

        <div class="upload-section">
            <h2 style="margin-bottom: 20px; color: #333;">Upload Video</h2>
            <div id="message" class="message"></div>
            
            <div class="upload-area" id="uploadArea">
                <p style="font-size: 48px; margin-bottom: 10px;">📁</p>
                <p style="font-size: 18px; color: #666;">Drag & Drop your video here</p>
                <p style="color: #999; margin: 10px 0;">or</p>
                <button class="btn" onclick="document.getElementById('fileInput').click()">
                    Choose File
                </button>
                <input type="file" id="fileInput" accept="video/*" multiple>
                <p style="margin-top: 15px; color: #999; font-size: 14px;">
                    Supported formats: MP4, AVI, MOV, MKV, WEBM (Max 500MB)
                </p>
            </div>
            
            <div class="progress-bar" id="progressBar">
                <div class="progress-fill" id="progressFill">0%</div>
            </div>
        </div>

        <div class="upload-section">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="color: #333; margin: 0;">Videos</h2>
                <div>
                    <button class="btn btn-small" onclick="filterVideos('my')" id="btnMyVideos" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">My Videos</button>
                    <button class="btn btn-small" onclick="filterVideos('all')" id="btnAllVideos" style="background: #e0e0e0; color: #333;">All Videos</button>
                </div>
            </div>
            <div class="video-grid" id="videoGrid">
                <p style="text-align: center; color: #666; grid-column: 1/-1;">
                    Loading videos...
                </p>
            </div>
        </div>
    </div>

    <div class="modal" id="videoModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal()">&times;</span>
            <h2 id="modalTitle" style="margin-bottom: 20px; color: #333;"></h2>
            <video id="modalVideo" controls></video>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const videoGrid = document.getElementById('videoGrid');
        const message = document.getElementById('message');
        let currentFilter = 'my';
        let allVideosData = [];

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            handleFiles(files);
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        function filterVideos(type) {
            currentFilter = type;
            const btnMy = document.getElementById('btnMyVideos');
            const btnAll = document.getElementById('btnAllVideos');
            
            if (type === 'my') {
                btnMy.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                btnMy.style.color = 'white';
                btnAll.style.background = '#e0e0e0';
                btnAll.style.color = '#333';
            } else {
                btnAll.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                btnAll.style.color = 'white';
                btnMy.style.background = '#e0e0e0';
                btnMy.style.color = '#333';
            }
            
            displayVideos(allVideosData, type);
        }

        function displayVideos(videos, filter = 'my') {
            const filteredVideos = filter === 'my' 
                ? videos.filter(v => v.is_owner)
                : videos;
            
            updateStats(videos.filter(v => v.is_owner));
            
            if (filteredVideos.length === 0) {
                const emptyMessage = filter === 'my' 
                    ? 'No videos uploaded yet. Upload your first video!'
                    : 'No videos available yet.';
                videoGrid.innerHTML = `<p style="text-align: center; color: #666; grid-column: 1/-1;">${emptyMessage}</p>`;
                return;
            }

            videoGrid.innerHTML = filteredVideos.map(video => `
                <div class="video-card">
                    <div class="video-thumbnail">🎬</div>
                    <div class="video-info">
                        <div class="video-title">${video.title}</div>
                        <div class="video-owner">👤 ${video.owner_name}</div>
                        <div class="video-meta">📅 ${video.uploaded}</div>
                        <div class="video-meta">💾 ${video.size}</div>
                        <div class="video-meta">🎞️ ${video.format}</div>
                        <div class="video-actions">
                            <button class="btn btn-small" onclick="playVideo('${video.id}', '${video.title}')">
                                ▶️ Play
                            </button>
                            ${video.is_owner ? `
                                <button class="btn btn-small btn-delete" onclick="deleteVideo('${video.id}')">
                                    🗑️ Delete
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function handleFiles(files) {
            Array.from(files).forEach(file => {
                if (file.type.startsWith('video/')) {
                    uploadFile(file);
                } else {
                    showMessage('Please select valid video files only', 'error');
                }
            });
        }

        function uploadFile(file) {
            const formData = new FormData();
            formData.append('video', file);

            progressBar.style.display = 'block';
            progressFill.style.width = '0%';
            progressFill.textContent = '0%';

            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = percent + '%';
                    progressFill.textContent = percent + '%';
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    showMessage('Video uploaded successfully!', 'success');
                    setTimeout(() => {
                        progressBar.style.display = 'none';
                        fileInput.value = '';
                        loadVideos();
                    }, 1000);
                } else {
                    showMessage('Upload failed: ' + xhr.responseText, 'error');
                    progressBar.style.display = 'none';
                }
            });

            xhr.addEventListener('error', () => {
                showMessage('Upload failed. Please try again.', 'error');
                progressBar.style.display = 'none';
            });

            xhr.open('POST', '/upload');
            xhr.send(formData);
        }

        function showMessage(text, type) {
            message.textContent = text;
            message.className = 'message ' + type;
            setTimeout(() => {
                message.className = 'message';
            }, 5000);
        }

        function loadVideos() {
            fetch('/videos/all')
                .then(response => response.json())
                .then(videos => {
                    allVideosData = videos;
                    displayVideos(videos, currentFilter);
                })
                .catch(error => {
                    console.error('Error loading videos:', error);
                    videoGrid.innerHTML = '<p style="text-align: center; color: #f5576c; grid-column: 1/-1;">Error loading videos</p>';
                });
        }

        function updateStats(videos) {
            document.getElementById('videoCount').textContent = videos.length;
            
            let totalBytes = 0;
            videos.forEach(video => {
                const sizeStr = video.size;
                const [value, unit] = sizeStr.split(' ');
                const num = parseFloat(value);
                
                if (unit === 'GB') totalBytes += num * 1024;
                else if (unit === 'MB') totalBytes += num;
                else if (unit === 'KB') totalBytes += num / 1024;
                else if (unit === 'B') totalBytes += num / (1024 * 1024);
            });
            
            document.getElementById('totalSize').textContent = totalBytes.toFixed(2) + ' MB';
        }

        function playVideo(videoId, title) {
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalVideo').src = '/stream/' + videoId;
            document.getElementById('videoModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('videoModal').classList.remove('active');
            document.getElementById('modalVideo').pause();
            document.getElementById('modalVideo').src = '';
        }

        function deleteVideo(videoId) {
            if (!confirm('Are you sure you want to delete this video?')) return;

            fetch('/delete/' + videoId, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    showMessage(data.message, 'success');
                    loadVideos();
                })
                .catch(error => {
                    showMessage('Error deleting video', 'error');
                });
        }

        function logout() {
            fetch('/api/logout', { method: 'POST' })
                .then(() => {
                    window.location.href = '/';
                });
        }

        loadVideos();

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    users = load_users()
    user = users.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    return render_template_string(APP_TEMPLATE, username=user['name'])

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    if not all([name, email, username, password]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if len(username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
    
    users = load_users()
    
    # Check if username or email already exists
    for user_id, user_data in users.items():
        if user_data['username'] == username:
            return jsonify({'success': False, 'message': 'Username already exists'})
        if user_data['email'] == email:
            return jsonify({'success': False, 'message': 'Email already registered'})
    
    # Create new user
    user_id = f"user_{len(users) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    users[user_id] = {
        'id': user_id,
        'name': name,
        'email': email,
        'username': username,
        'password': hash_password(password),
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Account created successfully! Please login.'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    users = load_users()
    
    # Find user by username
    user_found = None
    user_id = None
    for uid, user_data in users.items():
        if user_data['username'] == username:
            user_found = user_data
            user_id = uid
            break
    
    if not user_found:
        return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    if not check_password(password, user_found['password']):
        return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    # Set session
    session['user_id'] = user_id
    session['username'] = user_found['username']
    
    return jsonify({'success': True, 'message': 'Login successful'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'user_id' not in session:
        return 'Unauthorized', 401
    
    if 'video' not in request.files:
        return 'No video file provided', 400
    
    file = request.files['video']
    if file.filename == '':
        return 'No file selected', 400
    
    if not allowed_file(file.filename):
        return 'Invalid file type. Allowed: MP4, AVI, MOV, MKV, WEBM', 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{session['user_id']}_{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    file.save(filepath)
    
    # Save metadata
    metadata = load_metadata()
    video_id = unique_filename
    metadata[video_id] = {
        'id': video_id,
        'title': filename,
        'filename': unique_filename,
        'uploaded': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'size': get_file_size(filepath),
        'format': filename.rsplit('.', 1)[1].upper(),
        'user_id': session['user_id']
    }
    save_metadata(metadata)
    
    return jsonify({'message': 'Video uploaded successfully', 'id': video_id}), 200

@app.route('/videos/all', methods=['GET'])
def get_all_videos():
    if 'user_id' not in session:
        return jsonify([])
    
    metadata = load_metadata()
    users = load_users()
    
    # Get all videos with owner information
    all_videos = []
    for video in metadata.values():
        video_data = video.copy()
        
        # Get owner name
        owner_id = video.get('user_id', '')
        owner = users.get(owner_id, {})
        video_data['owner_name'] = owner.get('name', 'Unknown User')
        video_data['is_owner'] = (owner_id == session['user_id'])
        
        all_videos.append(video_data)
    
    # Sort by upload date, newest first
    all_videos.sort(key=lambda x: x.get('uploaded', ''), reverse=True)
    
    return jsonify(all_videos)

@app.route('/stream/<video_id>')
def stream_video(video_id):
    if 'user_id' not in session:
        return 'Unauthorized', 401
    
    metadata = load_metadata()
    if video_id not in metadata:
        return 'Video not found', 404
    
    # Allow all authenticated users to stream videos
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], metadata[video_id]['filename'])
    
    if not os.path.exists(video_path):
        return 'Video file not found', 404
    
    # Support for video streaming with range requests
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        return send_file(video_path)
    
    size = os.path.getsize(video_path)
    byte_start = 0
    byte_end = size - 1
    
    if range_header:
        byte_start = int(range_header.split('=')[1].split('-')[0])
        if '-' in range_header.split('=')[1]:
            range_end = range_header.split('=')[1].split('-')[1]
            if range_end:
                byte_end = int(range_end)
    
    length = byte_end - byte_start + 1
    
    with open(video_path, 'rb') as f:
        f.seek(byte_start)
        data = f.read(length)
    
    response = Response(
        data,
        206,
        mimetype=mimetypes.guess_type(video_path)[0],
        direct_passthrough=True
    )
    
    response.headers.add('Content-Range', f'bytes {byte_start}-{byte_end}/{size}')
    response.headers.add('Accept-Ranges', 'bytes')
    response.headers.add('Content-Length', str(length))
    
    return response

@app.route('/delete/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    metadata = load_metadata()
    
    if video_id not in metadata:
        return jsonify({'error': 'Video not found'}), 404
    
    # Check if video belongs to current user
    if metadata[video_id].get('user_id') != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], metadata[video_id]['filename'])
    
    if os.path.exists(video_path):
        os.remove(video_path)
    
    del metadata[video_id]
    save_metadata(metadata)
    
    return jsonify({'message': 'Video deleted successfully'})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
