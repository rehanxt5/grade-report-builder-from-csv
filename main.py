import argparse
import configparser
import csv
import os
import shutil


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

