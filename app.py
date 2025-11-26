import os
import shutil
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from pypdf import PdfWriter
from main import gradingAlgorithm, generate_csv_report, generate_pdf_report

app = Flask(__name__, template_folder='frontend', static_folder='frontend')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORT_FOLDER'] = 'report'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

def generate_combined_pdf_fixed(finalData, output_file, config_file):
    # Group data by student
    students = {}
    for row in finalData:
        # Create a unique key for student
        name = row.get('name', 'Unknown')
        student_id = row.get('id', 'Unknown')
        key = (name, student_id)
        if key not in students:
            students[key] = []
        students[key].append(row)
    
    pdf_files = []
    # Generate individual PDFs
    for key, data in students.items():
        name, student_id = key
        # Sanitize filename - handle None values
        name_str = str(name) if name is not None else 'Unknown'
        id_str = str(student_id) if student_id is not None else 'Unknown'
        
        safe_name = "".join([c for c in name_str if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_id = "".join([c for c in id_str if c.isalpha() or c.isdigit()]).rstrip()
        
        # Fallback if sanitization results in empty string
        safe_name = safe_name if safe_name else 'Unknown'
        safe_id = safe_id if safe_id else 'Unknown'
        
        filename = f"{safe_name}_{safe_id}_report.pdf"
        
        # generate_pdf_report writes to report/filename
        generate_pdf_report(data, filename, config_file)
        pdf_files.append(os.path.join('report', filename))
    
    # Merge PDFs
    merger = PdfWriter()
    for pdf in pdf_files:
        if os.path.exists(pdf):
            merger.append(pdf)
    
    merger.write(output_file)
    merger.close()
    
    # Cleanup individual PDFs
    for pdf in pdf_files:
        if os.path.exists(pdf):
            os.remove(pdf)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
