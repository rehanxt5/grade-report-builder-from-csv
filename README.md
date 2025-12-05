<div align="center">

# 📊 Student Grade Report Generator

### A powerful CLI and web-based tool to generate student grade reports from CSV data

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/Flask-Web%20Interface-red.svg)](https://flask.palletsprojects.com/)

*Supports weighted grading, configurable grade thresholds, and outputs reports in PDF or CSV format*

[Features](#-features) •
[Installation](#-installation) •
[Usage](#-usage) •
[Configuration](#-configuration) •
[Examples](#-examples)

</div>

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [📋 Requirements](#-requirements)
- [🚀 Installation](#-installation)
- [📁 Project Structure](#-project-structure)
- [⚙️ Configuration](#️-configuration)
  - [config.ini Sections](#configini-sections)
- [💻 Usage](#-usage)
  - [CLI Arguments](#cli-arguments)
  - [📝 Examples](#-examples)
  - [🌐 Web Interface](#-web-interface)
- [📄 Input CSV Format](#-input-csv-format)
- [📤 Output](#-output)
- [🔧 Troubleshooting](#-troubleshooting)


## ✨ Features

<table>
<tr>
<td>

- 🎯 **Weighted Grading** - Calculate grades based on configurable weightages for each component
- 📊 **Flexible Grade Thresholds** - Define custom grade boundaries (A+, A, B+, B, C+, C, D, F)
- 📁 **Multiple Output Formats** - Generate reports in PDF, CSV, or both
- 📋 **Report Modes**
  - Combined report for all students
  - Individual reports per student

</td>
<td>

- 🔄 **Batch Processing** - Process multiple CSV files with single or multiple config files
- ✅ **Data Validation** - Comprehensive validation of CSV data against config settings
- 🎨 **Beautiful PDF Reports** - Customizable colors and styling for PDF reports
- 🌐 **Web Interface** - Flask-based web UI for easy report generation

</td>
</tr>
</table>

---
## 📋 Requirements

### Core Dependencies

- **Python 3.7+**

### Required Packages
  - `flask` - Web framework for creating the web interface
  - `werkzeug` - WSGI utilities for secure filename handling and request processing
  - `pypdf` - PDF manipulation, merging multiple PDFs into a single file
  - `reportlab` - PDF generation with tables, styling, and custom layouts
  
- Built-in Python modules (no installation required):
  - `argparse` - Command-line argument parsing for CLI interface
  - `configparser` - Reading and parsing INI configuration files
  - `csv` - Reading CSV data files and writing CSV reports
  - `os` - File system operations (directory creation, path handling)
  - `shutil` - High-level file operations (directory removal, copying)
  - `zipfile` - Creating ZIP archives for per-student report downloads

---

## 🚀 Installation

### Step 1: Clone the Repository
   ```bash
   git clone <repository-url>
   cd gradecsv
   ```

### Step 2: Create a Virtual Environment (Recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

### Step 3: Install Dependencies
   ```bash
   pip install -r requirements.txt
   ```

---

## 📁 Project Structure

```
grade-report-builder-from-csv/
├── main.py               # Main CLI application
├── app.py                # Flask web application
├── requirements.txt      # Python dependencies
├── README.md             # Documentation 
├── frontend/             # Web interface templates
│   ├── index.html
│   └── index-old.html
├── sample/               # Sample data and config 
│   ├── config.ini
│   └── student_data.csv
```

---

## ⚙️ Configuration

> The application uses INI configuration files to define grading parameters, weights, thresholds, and report settings.

### 📝 config.ini Sections

#### 📌 `[TotalMarks]`

Defines the maximum marks for each grading component. These values are used to calculate the percentage score for each component.

```ini
[TotalMarks]
hw1 = 40        # Maximum marks for Homework 1
hw2 = 40        # Maximum marks for Homework 2
hw3 = 40        # Maximum marks for Homework 3
midterm = 80    # Maximum marks for Midterm exam
final = 80      # Maximum marks for Final exam
viva = 20       # Maximum marks for Viva
notebook = 10   # Maximum marks for Notebook
```
Defines the maximum marks for each grading component. These keys must match the columns in your CSV file, and can be any relevant assessment names (not limited to hw1, hw2, etc.).

Example:
```ini
[TotalMarks]
assignment1 = 50      # Maximum marks for Assignment 1
quiz = 20             # Maximum marks for Quiz
project = 100         # Maximum marks for Project
final_exam = 80       # Maximum marks for Final Exam
```
Or, for a typical homework/exam setup:
```ini
[TotalMarks]
hw1 = 40
hw2 = 40
hw3 = 40
midterm = 80
final = 80
viva = 20
notebook = 10
```

> **Note**: The keys here must match the column names in your CSV file.

---

#### ⚖️ `[Weights]`

Defines the weightage (percentage contribution) of each component to the final grade. The sum of all weights should typically equal 100.

```ini
[Weights]
hw1 = 10        # HW1 contributes 10% to final grade
hw2 = 10        # HW2 contributes 10% to final grade
hw3 = 10        # HW3 contributes 10% to final grade
midterm = 20    # Midterm contributes 20% to final grade
final = 30      # Final contributes 30% to final grade
viva = 5        # Viva contributes 5% to final grade
notebook = 5    # Notebook contributes 5% to final grade
```
Defines the weightage (percentage contribution) of each component to the final grade. The keys must match the columns in your CSV file and `[TotalMarks]` section, and can be any relevant assessment names (not limited to hw1, hw2, etc.). The sum of all weights should typically equal 100.

Example:
```ini
[Weights]
assignment1 = 20      # Assignment 1 contributes 20% to final grade
quiz = 10             # Quiz contributes 10% to final grade
project = 40          # Project contributes 40% to final grade
final_exam = 30       # Final Exam contributes 30% to final grade
```
Or, for a typical homework/exam setup:
```ini
[Weights]
hw1 = 10
hw2 = 10
hw3 = 10
midterm = 20
final = 30
viva = 5
notebook = 5
```

**Formula**: `weighted_score = (marks_obtained / total_marks) * weight`

---

#### 🎓 `[GradeThresholds]`

Defines the minimum percentage required for each grade. Grades are assigned from highest to lowest.

```ini
[GradeThresholds]
A+ = 95         # 95% and above = A+
A = 85          # 85% to 94.99% = A
B+ = 75         # 75% to 84.99% = B+
B = 65          # 65% to 74.99% = B
C+ = 55         # 55% to 64.99% = C+
C = 45          # 45% to 54.99% = C
D = 33          # 33% to 44.99% = D
F = 32          # Below 33% = F (anything below D threshold)
```

---

#### 🎨 `[ReportSettings]`

Controls report generation behavior and styling.

| Setting | Description | Example |
|---------|-------------|---------|
| `coloumns` | Comma-separated list of columns to include in the report | `name, subject, hw1, hw2, hw3, midterm, final, viva, notebook` |
| `report_title` | Title displayed on PDF reports | `Student Grade Report` |
| `_treat_missing_as_zero` | If `True`, missing values are treated as 0; if `False`, raises an error | `True` |
| `_include_overall_grade` | Include the calculated grade in the report | `True` |
| `_include_total_marks` | Include the total weighted score in the report | `True` |
| `header_bg_color` | Background color for table headers (hex) | `#2C3E50` |
| `header_text_color` | Text color for table headers (hex) | `#FFFFFF` |
| `table_bg_color` | Background color for table rows (hex) | `#ECF0F1` |
| `table_text_color` | Text color for table rows (hex) | `#2C3E50` |
| `primary_key` | Column used to group students (usually ID) | `id` |
| `secondary_key` | Secondary identifier (usually name) | `name` |

```ini
[ReportSettings]
coloumns = name, subject, hw1, hw2, hw3, midterm, final, viva, notebook
report_title = Student Grade Report
_treat_missing_as_zero = True
_include_overall_grade = True
_include_total_marks = True
header_bg_color = #2C3E50
header_text_color = #FFFFFF
table_bg_color = #ECF0F1
table_text_color = #2C3E50
primary_key = id
secondary_key = name
```

---

## 💻 Usage

### 🖥️ CLI Arguments

```bash
python main.py --csv_file <path> --config_file <path> --output_file <path> --output_format <format> --mode <mode>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--csv_file` | ✅ Yes | Path(s) to input CSV file(s). For multiple files, use comma-separated values. |
| `--config_file` | ✅ Yes | Path(s) to configuration file(s). Use 1 config for all CSVs, or provide equal number of configs (1:1 mapping). |
| `--output_file` | ⚠️ Conditional | Path for the output report. Required when mode is `report_for_all`. |
| `--output_format` | ✅ Yes | Output format: `pdf`, `csv`, or `both` |
| `--mode` | ✅ Yes | Report generation mode: `report_for_all` or `report_per_student` |

---

### 📝 Examples

#### 1️⃣ Generate a single PDF report for all students
```bash
python main.py \
  --csv_file student_data.csv \
  --config_file config.ini \
  --output_file grades_report.pdf \
  --output_format pdf \
  --mode report_for_all
```

#### 2️⃣ Generate a CSV report for all students
```bash
python main.py \
  --csv_file student_data.csv \
  --config_file config.ini \
  --output_file grades_report.csv \
  --output_format csv \
  --mode report_for_all
```

#### 3️⃣ Generate both PDF and CSV reports
```bash
python main.py \
  --csv_file student_data.csv \
  --config_file config.ini \
  --output_file grades_report.pdf \
  --output_format both \
  --mode report_for_all
```

#### 4️⃣ Generate individual PDF reports per student
```bash
python main.py \
  --csv_file student_data.csv \
  --config_file config.ini \
  --output_format pdf \
  --mode report_per_student
```
This creates separate PDF files for each student (e.g., `S001_report.pdf`, `S002_report.pdf`).

#### 5️⃣ Process multiple CSV files with a single config
```bash
python main.py \
  --csv_file "data1.csv, data2.csv, data3.csv" \
  --config_file config.ini \
  --output_file report.pdf \
  --output_format pdf \
  --mode report_for_all
```

#### 6️⃣ Process multiple CSV files with multiple configs (1:1 mapping)
```bash
python main.py \
  --csv_file "data1.csv, data2.csv, data3.csv" \
  --config_file "config1.ini, config2.ini, config3.ini" \
  --output_file report.pdf \
  --output_format pdf \
  --mode report_for_all
```
Each CSV file will be processed with its corresponding config file.

---

### 🌐 Web Interface

Start the Flask web server:

```bash
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

The web interface allows you to:
- Upload CSV and config files
- Select output format (PDF/CSV)
- Choose report mode (all students / per student)
- Download generated reports

---

## 📄 Input CSV Format

### Requirements

Your CSV file must include:
- A header row with column names
- Columns matching the keys defined in `[TotalMarks]` section of config
- Columns for `primary_key` and `secondary_key` (if defined)

### Example CSV Structure

```csv
name,id,subject,hw1,hw2,hw3,midterm,final,viva,notebook
Alice,S001,English,31,36,34,60,72,18,9
Alice,S001,Maths,30,32,31,55,68,17,8
Bob,S002,English,33,34,32,58,70,17,8
Bob,S002,Maths,29,31,30,53,66,16,7
```

### ✅ Validation Rules
- Marks cannot exceed the `TotalMarks` defined in config
- Marks cannot be negative
- Missing values are treated as 0 (if `_treat_missing_as_zero = True`)
- All columns in `[TotalMarks]` must exist in the CSV

---

## 📤 Output

### 📂 Report Directory
Generated reports are saved in the `report/` directory.

### 📄 PDF Report Features
- Student information header
- Subject-wise grade table
- Weighted scores for each component
- Total weighted score
- Final grade
- Pass/Fail status
- Customizable colors and styling

### 📊 CSV Report Features
- All selected columns from config
- Weighted scores
- Total and Grade columns (if enabled)

---

## 🔧 Troubleshooting

### ⚠️ Common Errors

#### 1. "Missing required section"
   - Ensure your config.ini has all four sections: `[TotalMarks]`, `[Weights]`, `[GradeThresholds]`, `[ReportSettings]`

#### 2. "Marks exceed total marks"
   - Check that no student has marks greater than the maximum defined in `[TotalMarks]`

#### 3. "Invalid config-to-CSV mapping"
   - When using multiple CSV files, provide either 1 config file (used for all) or exactly N config files for N CSV files

#### 4. "Column missing from CSV headers"
   - Ensure all columns listed in `coloumns` setting exist in your CSV file

---

<div align="center">

## 📄 License

[Add your license here]

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

[Add contribution guidelines here]

---

**Made with ❤️ for educators and students**

</div>
