import argparse
import configparser
import csv
import os
import shutil

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
