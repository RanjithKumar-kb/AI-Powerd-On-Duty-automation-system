# AI-Powerd-On-Duty-automation-system

Professional Summary
"An AI-integrated administrative framework leveraging Transformer-based NLP for automated request summarization and secure, real-time OD verification via dynamic QR-coded document synthesis."
Methodology & System Architecture
The system is built on a Modular Micro-service Architecture consisting of four distinct layers:

Authentication & Data Layer: Uses Flask-Login for role-based access control (Student/HOD) and SQLAlchemy for relational data persistence.

Cognitive NLP Layer: Integrated with the T5-Small Transformer model (HuggingFace) to perform abstractive summarization. It processes unstructured student reasons into concise, professional headers for the HOD.

Real-time Event Layer: Utilizes WebSockets (Socket.IO) to bridge the communication gap between students and faculty, allowing for instant dashboard updates without page reloads.

Security & Synthesis Layer: Automates the creation of tamper-proof documents using FPDF and QR-Code generation, ensuring each OD has a unique digital footprint for verification.

🚀 Key Features
AI Reason Summarization: Reduces HOD cognitive load by summarizing long student justifications.

Live Notifications: Real-time Socket.IO alerts for incoming requests.

Dynamic QR Verification: Every PDF includes a QR code that links back to the database for authenticity checks.

On-Demand PDF Generation: Optimized server performance by generating assets only when requested for download.

Responsive Dashboard: A clean, Bootstrap-based UI for both faculty and students.

📈 Benefits & Applications
Benefits
Zero Latency: Eliminates the physical transit time of paper applications.

Accountability: Maintains a digital trail of every request and approval.

Security: Prevents forgery through centralized, QR-verifiable documents.

Scalability: Can be easily adapted for employee gate-passes or medical leave systems.

Applications
University Departments: Automating student event attendance and leave.

Corporate Offices: Digitalizing short-duration out-of-office permissions.

Event Registrations: Generating verified participant entry passes.

📦 Installation & Setup
Clone the repository:

Bash:
git clone https://github.com/RanjithKumar-kb/AI-Powerd-On-Duty-automation-system
Install dependencies:

Bash:
pip install -r requirements.txt
Initialize the AI Model: The T5 model will download automatically on the first run.

Run the application:

Bash:
python app.py
