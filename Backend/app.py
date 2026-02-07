import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO # Corrected import usage
from flask_socketio import SocketIO, emit
# Helper import
from utils import generate_assets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'campus_flow_2026_secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_system.db'
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['DOC_FOLDER'] = 'generated_docs'

# Initialize SocketIO correctly
socketio = SocketIO(app)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOC_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- AI Summarizer  ---
# Move the import to the top of your file
from transformers import pipeline

# Load the model ONCE when the app starts, not inside the function
print("🚀 Loading AI Summarization Model... Please wait.")
try:
    summarizer = pipeline("summarization", model="t5-small", device=-1)
    print("✅ AI Model Loaded Successfully!")
except Exception as e:
    print(f"❌ AI Model failed to load: {e}")
    summarizer = None

def get_ai_summary(text):
    if not text or len(text.split()) < 5: 
        return text
    
    if summarizer:
        try:
            # Clean the text (remove extra spaces/newlines)
            clean_text = " ".join(text.split())
            result = summarizer(clean_text, max_length=25, min_length=5, do_sample=False)
            return result[0]['summary_text']
        except Exception as e:
            print(f"Summarization error: {e}")
            return (text[:47] + "...") if len(text) > 50 else text
    else:
        # Fallback if model isn't available
        return (text[:47] + "...") if len(text) > 50 else text

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False) # Roll No
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), default='student')
    image_file = db.Column(db.String(50), nullable=False, default='default.jpg')
    requests = db.relationship('RequestRecord', backref='author', lazy=True)

class RequestRecord(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(20)) # OD, GatePass, Leave
    od_date = db.Column(db.String(20))
    exit_time = db.Column(db.String(10), nullable=True)
    return_time = db.Column(db.String(10), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Pending')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        roll_no = request.form.get('username')
        
        # Prevent duplicate roll numbers
        if User.query.filter_by(username=roll_no).first():
            flash("Roll Number already registered. Please login.")
            return redirect(url_for('register'))

        file = request.files.get('profile_photo')
        filename = secure_filename(f"{roll_no}.jpg") if file else 'default.jpg'
        if file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Automatically set role to 'student'
        new_user = User(
            username=roll_no, 
            full_name=request.form.get('full_name'),
            password=request.form.get('password'), 
            role='student', 
            image_file=filename
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('hod_dashboard' if user.role == 'hod' else 'student_dashboard'))
    return render_template('login.html')

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    req_type = request.form.get('request_type')
    reason = request.form.get('reason')
    
    # 1. Generate the Summary
    ai_summary = get_ai_summary(reason)

    # 2. Save to Database
    new_req = RequestRecord(
        id=str(uuid.uuid4())[:8].upper(),
        user_id=current_user.id,
        request_type=req_type,
        od_date=request.form.get('od_date'),
        exit_time=request.form.get('exit_time') if req_type == 'GatePass' else None,
        return_time=request.form.get('return_time') if req_type == 'GatePass' else None,
        reason=reason,        # Full reason
        summary=ai_summary    # THE SUMMARIZED VERSION
    )
    db.session.add(new_req)
    db.session.commit()
    return redirect(url_for('student_dashboard'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    reqs = RequestRecord.query.filter_by(user_id=current_user.id).all()
    return render_template('student_dashboard.html', requests=reqs)

@app.route('/hod_dashboard')
@login_required
def hod_dashboard():
    if current_user.role != 'hod': return redirect(url_for('student_dashboard'))
    reqs = RequestRecord.query.order_by(RequestRecord.status.desc()).all()
    return render_template('hod_dashboard.html', requests=reqs)

@app.route('/approve/<id>')
@login_required
def approve(id):
    req = RequestRecord.query.get(id)
    if req and current_user.role == 'hod':
        req.status = 'Approved'
        db.session.commit()
    return redirect(url_for('hod_dashboard'))

@app.route('/download/<id>')
@login_required
def download(id):
    req = RequestRecord.query.get(id)
    pdf_path = generate_assets({
        'name': req.author.full_name,
        'roll_no': req.author.username,
        'type': req.request_type,
        'date': req.od_date,
        'summary': req.summary, # MAKE SURE THIS IS req.summary
        'exit_time': req.exit_time,
        'return_time': req.return_time
    }, id)
    return send_from_directory(app.config['DOC_FOLDER'], f"{id}.pdf")

@app.route('/verify/<id>')
def verify(id):
    # Search database for the unique ID from the QR code
    record = RequestRecord.query.get(id)
    
    if not record:
        return "<h1>Invalid Pass</h1><p>This document was not found in our system.</p>", 404

    # Determine if the pass is ACTIVE or INACTIVE
    # Logic: If HOD approved it, it's Active. Otherwise, it's Inactive.
    is_active = True if record.status == 'Approved' else False
    
    return render_template('verify_portal.html', record=record, is_active=is_active)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

from datetime import datetime

@app.context_processor
def inject_now():
    # This allows us to use now_date() and now_time() inside HTML templates
    return {
        'now_date': lambda: datetime.now().strftime("%Y-%m-%d"),
        'now_time': lambda: datetime.now().strftime("%H:%M")
    }
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Create default HOD if missing - No photo required
        if not User.query.filter_by(username='hod1').first():
            db.session.add(User(username='hod1', password='123', 
                               full_name="Department HOD", role='hod'))
            db.session.commit()

    # Use the socketio wrapper to run the app
    socketio.run(app, debug=True)
