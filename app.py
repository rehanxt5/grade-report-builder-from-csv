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
            
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/generate', methods=['POST'])
def generate():
    if 'csv_file' not in request.files or 'config_file' not in request.files:
        return "Missing files", 400
    
    csv_file = request.files['csv_file']
    config_file = request.files['config_file']
    output_filename = request.form.get('output_file')
    output_format = request.form.get('output_format')

    if csv_file.filename == '' or config_file.filename == '':
        return "No selected file", 400

    if not csv_file.filename.endswith('.csv') or not config_file.filename.endswith('.ini'):
        return "Invalid file type", 400

    # Save files
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(csv_file.filename))
    config_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(config_file.filename))
    csv_file.save(csv_path)
    config_file.save(config_path)

    try:
        # Run grading algorithm
        final_data = gradingAlgorithm(config_path, csv_path)

        # Generate report
        if output_format == 'csv':
            if not output_filename.endswith('.csv'):
                output_filename += '.csv'
            generate_csv_report(final_data, output_filename)
            report_path = os.path.join('report', output_filename)
        else:
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            report_path = os.path.join('report', output_filename)
            generate_combined_pdf_fixed(final_data, report_path, config_path)

        return send_file(report_path, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)
