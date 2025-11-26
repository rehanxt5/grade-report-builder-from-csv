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



if __name__ == '__main__':
    app.run(debug=True, port=5000)
