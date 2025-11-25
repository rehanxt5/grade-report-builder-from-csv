import argparse
import configparser
import csv
import os
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
from pypdf import PdfWriter
def validate_files(file_list, type):
    for file in file_list:
        if not file.endswith(type):
            raise ValueError(f"Invalid file type for {file}. Expected a {type} file.")
    return True

def verify_config(config_file, csv_file):
    """
    Verifies that the config file has all required sections and settings,
    and that the columns match between config and CSV file.
    Also validates that marks in CSV don't exceed total marks defined in config.
    
    Args:
        config_file: Path to the configuration INI file
        csv_file: Path to CSV file
        
    Raises:
        ValueError: If any required section, setting, or column is missing,
                   or if marks exceed total marks
    """
    config = configparser.ConfigParser()
    # Preserve case for keys
    config.optionxform = str
    config.read(config_file)
    
    # Required sections
    required_sections = ['TotalMarks', 'Weights', 'GradeThresholds', 'ReportSettings']
    
    # 1. Verify all required sections exist
    for section in required_sections:
        if section not in config.sections():
            raise ValueError(f"[{config_file}] Missing required section '[{section}]' in config file.")
    
    # 2. Get TotalMarks columns
    if not config.has_section('TotalMarks'):
        raise ValueError(f"[{config_file}] Missing '[TotalMarks]' section in config file.")
    
    total_marks_columns = list(config['TotalMarks'].keys())
    if not total_marks_columns:
        raise ValueError(f"[{config_file}] '[TotalMarks]' section is empty. Please define total marks for columns.")
    
    # Store total marks as integers for validation
    total_marks = {}
    for col in total_marks_columns: #['hw1','hw2']
        try:
            total_marks[col] = int(config['TotalMarks'][col])
        except ValueError:
            raise ValueError(f"[{config_file}] Invalid total marks value for '{col}'. Must be an integer.")
    
    # 3. Verify Weights section has all columns from TotalMarks
    if not config.has_section('Weights'):
        raise ValueError(f"[{config_file}] Missing '[Weights]' section in config file.")
    
    weights_columns = list(config['Weights'].keys())
    for col in total_marks_columns:
        if col not in weights_columns:
            raise ValueError(f"[{config_file}] Missing weight for column '{col}' in '[Weights]' section.")
    
    # Check if there are extra weights not in TotalMarks
    for col in weights_columns:
        if col not in total_marks_columns:
            raise ValueError(f"[{config_file}] Weight defined for '{col}' but no total marks specified in '[TotalMarks]' section.")
    
    # 4. Verify GradeThresholds has required grade levels
    if not config.has_section('GradeThresholds'):
        raise ValueError(f"[{config_file}] Missing '[GradeThresholds]' section in config file.")
    
    required_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']
    grade_thresholds = dict(config['GradeThresholds'])
    
    for grade in required_grades:
        if grade not in grade_thresholds:
            raise ValueError(f"[{config_file}] Missing grade threshold for '{grade}' in '[GradeThresholds]' section.")
    
    # 5. Verify ReportSettings
    if not config.has_section('ReportSettings'):
        raise ValueError(f"[{config_file}] Missing '[ReportSettings]' section in config file.")
    
    # Check for report_title
    if not config.has_option('ReportSettings', 'report_title'):
        raise ValueError(f"[{config_file}] Missing 'report_title' in '[ReportSettings]' section.")
    
    # Check for _treat_missing_as_zero
    if not config.has_option('ReportSettings', '_treat_missing_as_zero'):
        raise ValueError(f"[{config_file}] Missing '_treat_missing_as_zero' in '[ReportSettings]' section.")
    
    # Check for columns setting
    if not config.has_option('ReportSettings', 'coloumns'):
        raise ValueError(f"[{config_file}] Missing 'coloumns' in '[ReportSettings]' section.")
    
    # Parse the columns from ReportSettings
    report_columns_str = config.get('ReportSettings', 'coloumns')
    report_columns = [col.strip() for col in report_columns_str.split(',')]
    
    # Verify that report columns include all TotalMarks and Weights columns
    for col in total_marks_columns:
        if col not in report_columns:
            raise ValueError(f"[{config_file}] Column '{col}' from '[TotalMarks]' is missing in '[ReportSettings]' coloumns.")
    
    # 6. Verify CSV file has all required columns and validate marks
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            csv_columns = reader.fieldnames
            
            if csv_columns is None:
                raise ValueError(f"[{csv_file}] CSV file is empty or has no header row.")
            
            # Check if all TotalMarks columns exist in CSV
            for col in total_marks_columns:
                if col not in csv_columns:
                    raise ValueError(f"[{csv_file}] Column '{col}' from '[TotalMarks]' is missing in CSV file.")
            
            # 7. Validate that marks don't exceed total marks
            row_num = 1  # Start from 1 (header is row 0)
            for row in reader:
                row_num += 1
                for col in total_marks_columns:
                    value = row.get(col, '').strip()
                    
                    # Skip empty values if treat_missing_as_zero is True
                    if not value:
                        continue
                    
                    try:
                        marks = float(value)
                        if marks > total_marks[col]:
                            student_name = row.get('name', 'Unknown')
                            student_id = row.get('id', 'Unknown')
                            subject = row.get('subject', 'Unknown')
                            raise ValueError(
                                f"[{csv_file}] Row {row_num}: Student '{student_name}' (ID: {student_id}, Subject: {subject}) "
                                f"has {marks} marks in '{col}' which exceeds total marks of {total_marks[col]}."
                            )
                    except ValueError as e:
                        if "exceeds total marks" in str(e):
                            raise
                        # Invalid number format
                        student_name = row.get('name', 'Unknown')
                        student_id = row.get('id', 'Unknown')
                        subject = row.get('subject', 'Unknown')
                        raise ValueError(
                            f"[{csv_file}] Row {row_num}: Invalid marks value '{value}' for column '{col}' "
                            f"(Student: {student_name}, ID: {student_id}, Subject: {subject}). Must be a number."
                        )
            
    except FileNotFoundError:
        raise ValueError(f"[{csv_file}] CSV file not found.")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"[{csv_file}] Error reading CSV file: {str(e)}")
    
    print(f"✓ Config '{config_file}' verification passed for CSV '{csv_file}'.")
    return True

def validate_config_csv_mapping(csv_files, config_files):
    """
    Validates the mapping between CSV files and config files.
    
    Rules:
    - If 1 config file: Apply to all CSV files
    - If N config files for N CSV files: Map 1-to-1
    - Otherwise: Error
    
    Args:
        csv_files: List of CSV file paths
        config_files: List of config file paths
        
    Returns:
        List of tuples (csv_file, config_file) for verification
        
    Raises:
        ValueError: If config-to-CSV mapping is invalid
    """
    num_csv = len(csv_files)
    num_config = len(config_files)
    
    if num_config == 1:
        # Single config for all CSV files
        print(f"Using single config file '{config_files[0]}' for all {num_csv} CSV file(s).")
        return [(csv_file, config_files[0]) for csv_file in csv_files]
    
    elif num_config == num_csv:
        # One-to-one mapping
        print(f"Using 1-to-1 mapping: {num_csv} config file(s) for {num_csv} CSV file(s).")
        return list(zip(csv_files, config_files))
    
    else:
        raise ValueError(
            f"Invalid config-to-CSV mapping: {num_csv} CSV file(s) but {num_config} config file(s). "
            f"Either provide 1 config file for all CSV files, or provide exactly {num_csv} config file(s)."
        )
def line_break():
    print('+' + '-'*50 + '+')
    
def verify_all_configs(csv_files, config_files):
    """
    Verifies all config files against their respective CSV files.
    
    Args:
        csv_files: List of CSV file paths
        config_files: List of config file paths
    """
    mappings = validate_config_csv_mapping(csv_files, config_files)
    
    line_break()
    print("Starting config verification...")
    line_break()
    
    for csv_file, config_file in mappings:
        verify_config(config_file, csv_file)
    
    line_break()
    print("✓ All config verifications passed successfully!")
    line_break()
def grade(gradeThreshold, total):
    """
    gradeThreshold: mapping like {'A+':'95', 'A':'85', ...'}
    total: numeric score
    Returns grade string.
    """
    # parse thresholds into floats without mutating caller's dict
    try:
        gt = {k: float(v) for k, v in gradeThreshold.items()}
    except Exception as e:
        raise ValueError("Grade thresholds must be numeric") from e

    # Check from highest to lowest; only >= is needed
    if total >= gt['A+']:
        return 'A+'
    if total >= gt['A']:
        return 'A'
    if total >= gt['B+']:
        return 'B+'
    if total >= gt['B']:
        return 'B'
    if total >= gt['C+']:
        return 'C+'
    if total >= gt['C']:
        return 'C'
    if total >= gt['D']:
        return 'D'
    return 'F'
    
def getStudentWiseData(finalData,primary_key='id'):
    getStudentWiseData =[]   #[ [{stu1,sub1 ...},{stu2, sub2 ...},{sub3}] , [{stu3,..sub1},{sub2}]... ]
    data=[]
    i = 0
    unique = []
    while i <len(finalData):
        if not unique:
            unique.append(finalData[i][primary_key])
        if finalData[i][primary_key] in unique:
            data.append(finalData[i])
        else:
            getStudentWiseData.append(data)
            data=[]
            unique=[]
        i+=1
    getStudentWiseData.append(data)
    return getStudentWiseData
def generate_csv_report(data , output_file):
    if not os.path.exists('report'):
        os.mkdir('report')
    with open(os.path.join('report',output_file),'w') as f:
        writer = csv.DictWriter(f,list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
def gradingAlgorithm(config_file, csv_file):

    # reading the config file
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(config_file)

    totalMarks = dict(config['TotalMarks'])
    weights = dict(config['Weights'])
    gradeThresholds = dict(config['GradeThresholds'])
    reportSettings = dict(config['ReportSettings'])

    # reading the csv file and applying grading
    ModifiedData =[]

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
    
        for row in reader:
            total=0
            for weight in weights:
                val=(float(row[weight])/float(totalMarks[weight]))*float(weights[weight]) #round of the coloumn to iits weightage
                row[weight]=val
                total +=val
            row['Total'] = total
            row['Grade'] = grade(gradeThresholds,total)
            ModifiedData.append(row)
    # cleaning the data
    finalData = []
    clean=reportSettings['coloumns'].replace(' ','') #[]
    coloumns = clean.split(',')
    if reportSettings['_include_total_marks'] =='True':
        coloumns.append('Total')
    if reportSettings['_include_overall_grade'] =='True':
        coloumns.append('Grade')

    for row in ModifiedData:
        data = {}
        for key in coloumns:
            data[key]=row[key]
        finalData.append(data)
    return finalData


def generate_combined_pdf(finalData, output_file,config_file):

    # generating temporary folder
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    else:
        shutil.rmtree('tmp')
        os.mkdir('tmp')
    i = 0

    #config file
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(config_file)
    
    reportSettings = dict(config['ReportSettings'])
    primary_key = reportSettings.get('primary_key', 'id')
    secondary_key = reportSettings.get('secondary_key', None)
    studentWiseData = getStudentWiseData(finalData, primary_key)
    
    for data in studentWiseData:
        if not secondary_key:
            fileName = f"{data[0][primary_key]}_{data[0][secondary_key]}_report.pdf"
        else:
            fileName = f"{data[0][primary_key]}_{data[0][secondary_key]}_report.pdf"

        generate_pdf_report(data, fileName, config_file)
    # Combining them into one
    files = os.listdir('tmp') #file1.pdf ,file2.pdf 
    pdf_files = [os.path.join('tmp',file) for file in files] # tmp/file1.pdf , tmp/file2.pdf
    # 2. Create a PdfWriter object (the "merger")
    merger = PdfWriter()

    # 3. Loop through the list and append them
    for pdf in pdf_files:
        merger.append(pdf)

    # 4. Write the combined result to a new file
    merger.write(output_file)
    merger.close()

    print("PDFs merged successfully!")
        


def generate_pdf_report(data, output_file, config_file):
    """
    Generates a beautiful PDF report for a single student with all their subjects.
    
    Args:
        data: List of dictionaries containing student data (one dict per subject for the same student)
        output_file: Path to save the PDF file
        config_file: Path to config.ini to read report settings
    """

    
    if not os.path.exists('report'):
        os.mkdir('report')
    
    # Read config for styling
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(config_file)
    
    reportSettings = dict(config['ReportSettings'])
    
    # Get colors from config
    header_bg = reportSettings.get('header_bg_color', '#2C3E50')
    header_text = reportSettings.get('header_text_color', '#FFFFFF')
    table_bg = reportSettings.get('table_bg_color', '#ECF0F1')
    table_text = reportSettings.get('table_text_color', '#2C3E50')
    report_title = reportSettings.get('report_title', 'Student Grade Report')
    
    # Convert hex to ReportLab colors
    def hex_to_color(hex_str):
        hex_str = hex_str.lstrip('#')
        return colors.HexColor('#' + hex_str)
    
    header_bg_color = hex_to_color(header_bg)
    header_text_color = hex_to_color(header_text)
    table_bg_color = hex_to_color(table_bg)
    table_text_color = hex_to_color(table_text)
    
    # Create PDF
    pdf_path = os.path.join('report', output_file)
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    
    # Get available width
    available_width = A4[0] - 80  # Total width minus margins
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=header_bg_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Add title
    title = Paragraph(report_title, title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Student info style
    info_style = ParagraphStyle(
        'StudentInfo',
        parent=styles['Normal'],
        fontSize=12,
        textColor=table_text_color,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Get student name and ID from first record
    first_record = data[0] if isinstance(data, list) else data
    student_name = first_record.get('name', 'Unknown')
    student_id = first_record.get('id', 'Unknown')
    
    elements.append(Paragraph(f"<b>Name:</b> {student_name}", info_style))
    elements.append(Paragraph(f"<b>Student ID:</b> {student_id}", info_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Convert single dict to list for uniform processing
    if not isinstance(data, list):
        data = [data]
    
    # Prepare table data - get columns from first record, excluding name and id
    exclude_keys = {'name', 'id'}
    table_columns = [key for key in first_record.keys() if key not in exclude_keys]
    
    # Create table with header row
    table_data = []
    
    # Header row
    header_row = [col.upper() for col in table_columns]
    table_data.append(header_row)
    
    # Add data rows (one per subject)
    for record in data:
        data_row = [str(record.get(col, '')) for col in table_columns]
        table_data.append(data_row)
    
    # Calculate intelligent column widths based on content length
    num_cols = len(table_columns)
    
    # Estimate width needed for each column (based on max content length)
    col_char_widths = []
    for i, col in enumerate(table_columns):
        max_len = len(col.upper())  # Start with header length
        for record in data:
            content = str(record.get(col, ''))
            max_len = max(max_len, len(content))
        col_char_widths.append(max_len)
    
    # Calculate proportional widths (with min/max constraints)
    total_chars = sum(col_char_widths)
    col_widths = []
    min_width = 0.5 * inch  # Minimum column width
    max_width = 2.5 * inch  # Maximum column width
    
    for char_width in col_char_widths:
        # Proportional width based on content
        prop_width = (char_width / total_chars) * available_width
        # Apply min/max constraints
        final_width = max(min_width, min(max_width, prop_width))
        col_widths.append(final_width)
    
    # Normalize to fit available width if total exceeds
    total_width = sum(col_widths)
    if total_width > available_width:
        scale_factor = available_width / total_width
        col_widths = [w * scale_factor for w in col_widths]
    
    # Create table
    table = Table(table_data, colWidths=col_widths)
    
    # Style the table
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), header_bg_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), header_text_color),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), table_bg_color),
        ('TEXTCOLOR', (0, 1), (-1, -1), table_text_color),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('BOX', (0, 0), (-1, -1), 1.5, header_bg_color),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Result section - check if any subject failed
    all_grades = [record.get('Grade', record.get('grade', '')) for record in data]
    has_fail = 'F' in all_grades
    result = 'FAIL' if has_fail else 'PASS'
    
    result_style = ParagraphStyle(
        'Result',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.red if has_fail else colors.green,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    result_text = Paragraph(f"<b>Result: {result}</b>", result_style)
    elements.append(result_text)
    
    # Build PDF
    doc.build(elements)
    print(f"✓ PDF report generated: {pdf_path}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple app to generate reports.")
    parser.add_argument("--csv_file", type=str, required=True, help="Path(s) to the input CSV file(s), comma-separated.")
    parser.add_argument("--config_file", type=str, required=True, help="Path(s) to the configuration file(s), comma-separated. Use 1 config for all CSVs, or provide equal number of configs.")
    parser.add_argument("--output_file", type=str, help="Path to save the generated report.")
    parser.add_argument("--output_format", type=str, choices=["pdf", "csv", "both"], required=True, help="Format of the output report.")
    parser.add_argument("--mode", type=str, choices=["report_per_student", "report_for_all"], required=True, help="Mode of report generation.")

    args = parser.parse_args()

    if args.mode != "report_per_student" and args.output_file is None:
        raise ValueError("Output file must be specified when mode is not 'report_per_student'.")
        
    # Parse comma-separated files
    csv_files = [f.strip() for f in args.csv_file.split(",")] 
    config_files = [f.strip() for f in args.config_file.split(",")]
    
    # Validate file extensions
    validate_files(csv_files, ".csv")
    validate_files(config_files, ".ini")
    
    # Verify config file structure and CSV compatibility
    verify_all_configs(csv_files, config_files)
    
    if args.output_file:
        validate_files([args.output_file], f".{args.output_format}")
    
    print("All files validated successfully.")
    line_break()
    print("CSV file(s):", ", ".join(csv_files))
    print("Config file(s):", ", ".join(config_files))
    print("Output file:", args.output_file)
    print("Output format:", args.output_format)
    print("Mode:", args.mode)
    line_break()

    # Read primary and secondary keys from the first config file
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(config_files[0])    
    reportSettings = dict(config['ReportSettings']) 

    primary_key = reportSettings.get('primary_key')
    secondary_key = reportSettings.get('secondary_key', None)
    
    # Grading algorithm
    if args.mode == 'report_for_all' :

        if args.output_format == "csv" or args.output_format == "both":
            # Build csv-config mappings (supports single config for all CSVs or 1:1 mapping)
            mappings = validate_config_csv_mapping(csv_files, config_files)

            # Prepare output naming
            base_name, ext = os.path.splitext(args.output_file)
            multiple = len(mappings) > 1

            for idx, (csv_file, config_file) in enumerate(mappings, start=1):
                finalData = gradingAlgorithm(config_file=config_file, csv_file=csv_file)

                if multiple:
                    out_name = f"{base_name}_{idx}{ext}"
                else:
                    out_name = args.output_file

                generate_csv_report(finalData, out_name)

        if args.output_format == "pdf" or args.output_format == "both":
            if len(config_files)==1:
                count =''
                for csv_file in csv_files:
                    finalData = gradingAlgorithm(config_files[0],csv_file)
                    os.makedirs('tmp',exist_ok=True)
                    generate_pdf_report(finalData,str(count)+args.output_file , config_files[0])
                    if count=='':
                        count=1
                    else:
                        count+=1
            else:
                count =''
            mappings = validate_config_csv_mapping(csv_files, config_files)

            # Prepare output naming
            base_name, ext = os.path.splitext(args.output_file)
            multiple = len(mappings) > 1

            for idx, (csv_file, config_file) in enumerate(mappings, start=1):
                finalData = gradingAlgorithm(config_file=config_file, csv_file=csv_file)

                if multiple:
                    out_name = f"{base_name}_{idx}{ext}"
                else:
                    out_name = args.output_file

                generate_combined_pdf(finalData,out_name,config_file)
    
    if args.mode == 'report_per_student':
        if args.output_format == "csv" or args.output_format == "both":
            mappings = validate_config_csv_mapping(csv_files, config_files)

            for csv_file, config_file in mappings:
                finalData = gradingAlgorithm(config_file=config_file, csv_file=csv_file)
                studentWiseData = getStudentWiseData(finalData,primary_key)
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(config_file)
                reportSettings = dict(config['ReportSettings'])
                primary_key = reportSettings.get('primary_key', 'id')
                secondary_key = reportSettings.get('secondary_key', 'name')
                for data in studentWiseData:
                    if not secondary_key:
                        fileName = f"{data[0][primary_key]}_{data[0][secondary_key]}_report.pdf"
                    else:
                        fileName = f"{data[0][primary_key]}_report.pdf"
                    generate_csv_report(data, fileName)
        if args.output_format == "pdf" or args.output_format == "both":
            mappings = validate_config_csv_mapping(csv_files, config_files)

            for csv_file, config_file in mappings:
                finalData = gradingAlgorithm(config_file=config_file, csv_file=csv_file)
                studentWiseData = getStudentWiseData(finalData,primary_key)
                for data in studentWiseData:
                    if not secondary_key:
                        fileName = f"{data[0][primary_key]}_{data[0][secondary_key]}_report.pdf"
                    else:
                        fileName = f"{data[0][primary_key]}_report.pdf"
                    generate_pdf_report(data, fileName, config_file)
