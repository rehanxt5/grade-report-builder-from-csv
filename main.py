import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Process a CSV file.")
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to the CSV file to process."
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"CSV file path: {args.csv_file}")



