🚀 AI-Powered Unified Management System (College & Industry)


  An intelligent, hybrid administrative platform designed to manage On-Duty (OD), Leave, and Gate Pass protocols. This system serves a dual purpose: providing academic efficiency for colleges and operational security for industrial environments.

🌟 The Hybrid Solution

This project bridges two different sectors into one unified codebase:

For Colleges: Manages Student On-Duty (OD) and academic Leave applications with Faculty/HOD oversight.

For Industry: Manages Employee Gate Passes and Shift-Leave management to track workforce movement in real-time.

✨ Core Features

🧠 1. AI-Driven Summarization
Integrated with the HuggingFace T5-Small Transformer, the system automatically condenses long, detailed reasons into concise 1-sentence summaries.

Benefit: Managers and HODs can review dozens of applications in seconds without reading paragraphs of text.

🛡️ 2. QR-Based Live Verification
Every approved document is generated as a PDF featuring a unique, encrypted QR code.

The Scan: Security personnel scan the QR code to reach a Live Verification Portal.

Security: The portal displays the user's stored profile photo, name, and live status (ACTIVE/INACTIVE) to prevent the use of forged or photoshopped documents.

⏳ 3. Dynamic Expiry Engine
Auto-Invalidation: Once the approved date or the return time (for Gate Passes) has passed, the system automatically marks the form as Expired.

Access Control: Expired forms cannot be used for entry/exit, and the PDF download link is automatically disabled for the user.

🛠️ Technical Architecture

Backend	- Python (Flask), Flask-SocketIO

AI Engine	- Transformers (HuggingFace T5)

Database - SQLAlchemy (SQLite)

Document Engine -	FPDF & PyQRCode

Frontend - Bootstrap 5, Jinja2, JavaScript

📸 System Overview

Student/Employee Portal: Submit requests for OD, Leave, or Gate Pass.

HOD/Manager Portal: View AI-summarized reasons and approve/reject with one click.

Security Portal: Mobile-responsive page for scanning QR codes and viewing the Active/Inactive status of the bearer.

🔮 Future Enhancements

Face Matching: Comparing the live person’s face at the gate with the stored profile photo using OpenCV.

Multi-Level Approval: Adding a "Supervisor" level before it reaches the HOD/Manager.

Real-time Notifications: SMS alerts to parents/HR when a gate pass is scanned.
