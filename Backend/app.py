from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO
from transformers import pipeline
import uuid, os
from utils import generate_od_assets 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///od_system.db'
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Login Configuration ---
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # This is the modern way to fetch the user by ID
    return db.session.get(User, int(user_id))
# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False) # 'student' or 'hod'

class OD_Record(db.Model):
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String, nullable=False)
    roll_no = db.Column(db.String, nullable=False)
    od_date = db.Column(db.String, nullable=False)
    # Changed nullable to True and added a default string
    summary = db.Column(db.String, nullable=True, default="OD Request") 
    status = db.Column(db.String, default='pending')

# --- NLP Setup ---
# Using T5 for better "HOD-friendly" summaries
summarizer = pipeline("summarization", model="t5-small")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    # If the user is NOT logged in, show the login page
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # If they ARE logged in, send them to their specific dashboard
    if current_user.role == 'hod':
        return redirect(url_for('hod_dashboard'))
    
    return redirect(url_for('student_dashboard'))


# --- Login Logic ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            login_user(user)
            return redirect(url_for('hod_dashboard' if user.role == 'hod' else 'student_dashboard'))
        flash('Invalid Credentials')
    return render_template('login.html')

# --- Student Dashboard (View their own ODs) ---
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    # Only get ODs for the person logged in
    user_requests = OD_Record.query.filter_by(user_id=current_user.id).all()
    return render_template('student_dashboard.html', requests=user_requests)

# --- HOD Dashboard (View ALL requests) ---
@app.route('/hod')
@login_required
def hod_dashboard():
    if current_user.role != 'hod': 
        return redirect(url_for('login'))
    
    # Force a fresh fetch of all records
    try:
        all_requests = db.session.execute(db.select(OD_Record)).scalars().all()
        return render_template('hod_dashboard.html', requests=all_requests)
    except Exception as e:
        print(f"Template Rendering Error: {e}")
        return "Error loading dashboard. Check terminal.", 500

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.')
            return redirect(url_for('signup'))
        
        # Create new student account
        new_user = User(username=username, password=password, role='student')
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/submit', methods=['POST'])
@login_required
def submit_od():
    name = request.form.get('name')
    roll = request.form.get('roll_no')
    reason = request.form.get('reason', '').strip()
    od_date = request.form.get('date')

    # Initialize with a fallback immediately
    summary_text = "OD Application" 

    if reason:
        try:
            # NLP logic
            input_text = f"summarize: {reason}"
            summary_result = summarizer(input_text, max_new_tokens=15, min_length=2, do_sample=False)
            
            if summary_result and 'summary_text' in summary_result[0]:
                temp_summary = summary_result[0]['summary_text']
                if temp_summary: # Check if it's not empty
                    summary_text = temp_summary.strip().title()
        except Exception as e:
            print(f"AI Model Error: {e}")
            summary_text = " ".join(reason.split()[:4]).title()

    # --- THE ULTIMATE SAFETY CHECK ---
    if summary_text is None or summary_text == "":
        summary_text = "OD Request"

    print(f"DEBUG: Saving OD with summary: {summary_text}") # Check your terminal for this!

    unique_id = str(uuid.uuid4())[:8]
    new_entry = OD_Record(
        id=unique_id,
        user_id=current_user.id,
        name=name,
        roll_no=roll,
        summary=summary_text,
        od_date=od_date,
        status='pending'
    )
    
    try:
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {e}")
        return "Internal Database Error", 500

    socketio.emit('new_od_request', {
        'id': unique_id,
        'name': name,
        'roll': roll,
        'summary': summary_text
    })

    return redirect(url_for('student_dashboard'))

@app.route('/apply')
@login_required
def apply_od():
    # This route simply opens the form for the student
    return render_template('index.html')

@app.route('/promote/<id>', methods=['GET', 'POST'])
@login_required
def approve_od(id):
    if current_user.role != 'hod':
        return redirect(url_for('login'))

    # 1. Fetch the record
    record = db.session.get(OD_Record, id)
    
    if record:
        try:
            # 2. Update status only
            record.status = 'Approved'
            
            # 3. Commit immediately to release the database lock
            db.session.commit()
            print(f"✅ OD {id} status updated to Approved.")
            
            # Note: We are NOT calling generate_od_assets here.
            # This makes the refresh instant. 
            # The PDF will be created when the student clicks 'Download'.
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database Error: {e}")
            
    # 4. Redirect immediately back to HOD dashboard
    return redirect(url_for('hod_dashboard'))

import os
from flask import send_file

@app.route('/download/<od_id>')
@login_required
def download_od(od_id):
    record = db.session.get(OD_Record, od_id)
    
    if not record or record.status != 'Approved':
        return "OD not approved yet.", 403

    directory = os.path.join(os.getcwd(), 'generated_ods')
    filename = f"OD_{od_id}.pdf"
    file_path = os.path.join(directory, filename)

    # 🚀 If the file doesn't exist yet, generate it now!
    if not os.path.exists(file_path):
        from utils import generate_od_assets
        
        # Clean data for PDF
        student_data = {
            'name': str(record.name or "Student"),
            'roll_no': str(record.roll_no or "N/A"),
            'date': str(record.od_date or "N/A"),
            'summary': str(record.summary or "Approved OD")
        }
        
        print(f"Generating PDF for {od_id} on-demand...")
        generate_od_assets(student_data, record.id)

    return send_from_directory(directory, filename, as_attachment=True)

# Keep your /submit and /promote routes here, but add @login_required to them!
# In /submit, make sure to add user_id=current_user.id when creating new_entry.

if __name__ == "__main__":
    with app.app_context():
        # Create the tables if they don't exist
        db.create_all()

        # Check for HOD and create if missing
        if not User.query.filter_by(username='hod1').first():
            print("Creating default HOD account...")
            db.session.add(User(username='hod1', password='123', role='hod'))
            db.session.commit()
            print("HOD created!")

    # Start the SocketIO server
    socketio.run(app, debug=True)
