import os
import qrcode
from fpdf import FPDF

def generate_assets(data, doc_id):
    qr_folder = 'static/qrcodes'
    pdf_folder = 'generated_docs'
    os.makedirs(qr_folder, exist_ok=True)
    os.makedirs(pdf_folder, exist_ok=True)

    # 1. QR Generation
    # Points to the verification portal
    verify_url = f"http://127.0.0.1:5000/verify/{doc_id}"
    qr = qrcode.make(verify_url)
    qr_path = os.path.join(qr_folder, f"{doc_id}.png")
    qr.save(qr_path)

    # 2. PDF Generation
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 18)
    # Dynamically changes title based on type (OD, GatePass, or Leave)
    pdf.cell(200, 15, f"OFFICIAL {data['type'].upper()} DOCUMENT", ln=True, align='C')
    pdf.ln(10)
    
    # Student Info
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Student Name: {data['name']}", ln=1)
    pdf.cell(0, 10, f"Roll Number: {data['roll_no']}", ln=1)
    pdf.cell(0, 10, f"Request Date: {data['date']}", ln=1)
    pdf.cell(0, 10, f"Request Type: {data['type']}", ln=1)
    
    # Conditional Time (Only for GatePass)
    if data['type'] == 'GatePass':
        pdf.set_text_color(255, 0, 0) # Red text for time
        pdf.cell(0, 10, f"Validity: {data['exit_time']} to {data['return_time']}", ln=1)
        pdf.set_text_color(0, 0, 0) # Reset to black
    
    pdf.ln(5)
    
    # AI Summary Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "AI Verified Summary:", ln=1)
    pdf.set_font("Arial", 'I', 11)
    pdf.set_fill_color(240, 240, 240) # Light grey background for summary
    pdf.multi_cell(0, 10, f"\"{data['summary']}\"", border=1, fill=True)
    
    # QR Code Footer
    pdf.ln(15)
    pdf.image(qr_path, x=80, w=50)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 10, "This is an AI-generated digital pass. Scan QR to verify authenticity.", ln=True, align='C')

    path = os.path.join(pdf_folder, f"{doc_id}.pdf")
    pdf.output(path)
    return path
