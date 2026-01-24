import os
import qrcode
from fpdf import FPDF

def generate_od_assets(student_data, od_id):
    try:
        # Define Paths
        base_dir = os.getcwd()
        qr_folder = os.path.join(base_dir, 'static', 'qrcodes')
        pdf_folder = os.path.join(base_dir, 'generated_ods')

        for folder in [qr_folder, pdf_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # 1. Generate QR Code
        verify_url = f"http://127.0.0.1:5000/verify/{od_id}" 
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(verify_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(qr_folder, f"{od_id}.png")
        qr_img.save(qr_path)

        # 2. Generate PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Use Helvetica (Built-in to FPDF)
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(200, 15, "OFFICIAL ON-DUTY APPROVAL FORM", ln=True, align='C')
        pdf.ln(5)
        pdf.line(10, 35, 200, 35)
        pdf.ln(10)

        pdf.set_text_color(0, 0, 0)
        def safe_text(text): return str(text).encode('latin-1', 'ignore').decode('latin-1')

        # Add Details
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(45, 10, "Student Name:", ln=0)
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 10, safe_text(student_data.get('name')), ln=1)

        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(45, 10, "Roll Number:", ln=0)
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 10, safe_text(student_data.get('roll_no')), ln=1)

        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(45, 10, "OD Date:", ln=0)
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 10, safe_text(student_data.get('date')), ln=1)

        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "AI Generated Reason Summary:", ln=1)
        pdf.set_font("Helvetica", 'I', 11)
        pdf.multi_cell(0, 10, safe_text(student_data.get('summary')))

        # QR Code Image
        pdf.ln(10)
        if os.path.exists(qr_path):
            pdf.image(qr_path, x=80, y=pdf.get_y(), w=45)

        # 3. Save with Error Catching for "File Open"
        pdf_path = os.path.join(pdf_folder, f"OD_{od_id}.pdf")
        try:
            pdf.output(pdf_path)
        except PermissionError:
            print(f"Permission Error: Close the file OD_{od_id}.pdf if it is open!")
            raise Exception("Please close the PDF file before re-approving.")

        return pdf_path

    except Exception as e:
        print(f"CRITICAL ERROR in utils.py: {str(e)}")
        raise e
