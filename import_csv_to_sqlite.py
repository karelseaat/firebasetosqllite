import subprocess
import argparse
import os
import sys
import glob
import gzip
import tempfile
import shutil

def main():
    parser = argparse.ArgumentParser(description="Import CSV or compressed CSV files into a SQLite database.")
    parser.add_argument('--input-dir', required=True, help='Directory containing the .csv or .csv.gz files.')
    parser.add_argument('--sqlite-db', required=True, help='Path to the output SQLite database file.')
    args = parser.parse_args()

    # Search for both compressed and uncompressed files
    csv_files = glob.glob(os.path.join(args.input_dir, '*.csv'))
    gz_files = glob.glob(os.path.join(args.input_dir, '*.csv.gz'))
    all_files = csv_files + gz_files

    if not all_files:
        print(f"Error: No .csv or .csv.gz files found in '{args.input_dir}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(all_files)} files to import into '{args.sqlite_db}'.")

    for file_path in all_files:
        is_compressed = file_path.endswith('.gz')
        table_name = os.path.basename(file_path).split('.')[0]
        print(f"  - Processing '{os.path.basename(file_path)}' into table '{table_name}'...")

        temp_csv_path = None
        try:
            open_func = gzip.open if is_compressed else open
            with open_func(file_path, 'rt', encoding='utf-8') as f:
                header = f.readline().strip()
                if not header:
                    print(f"    - Warning: File '{file_path}' is empty or has no header. Skipping.")
                    continue
                columns = header.split('|')

            column_defs = ", ".join([f'\"{col}\" TEXT' for col in columns])
            create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({column_defs});'
            
            subprocess.run(['sqlite3', args.sqlite_db, create_table_sql], check=True, capture_output=True, text=True)

            # For SQLite, we decompress to a temporary file if needed, then import.
            if is_compressed:
                # Create a temporary file to hold the decompressed CSV
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', newline='') as temp_f:
                    temp_csv_path = temp_f.name
                    # Decompress the gzipped file into the temporary file
                    with gzip.open(file_path, 'rt', encoding='utf-8') as gz_f:
                        shutil.copyfileobj(gz_f, temp_f)
                import_file_path = temp_csv_path
            else:
                import_file_path = file_path

            import_commands = f""".separator |\n.import --csv --skip 1 '{import_file_path}' \"{table_name}\"\n"""
            subprocess.run(['sqlite3', args.sqlite_db], input=import_commands, check=True, capture_output=True, text=True)
            print(f"    - Successfully imported data into table '{table_name}'.")

        except FileNotFoundError:
            print("Error: 'sqlite3' command not found. Please ensure SQLite3 is installed and in your system's PATH.", file=sys.stderr)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"    - An error occurred while processing '{os.path.basename(file_path)}'.", file=sys.stderr)
            print(f"    - Stderr: {e.stderr.strip()}", file=sys.stderr)
        except Exception as e:
            print(f"    - An unexpected error occurred: {e}", file=sys.stderr)
        finally:
            # Clean up the temporary file if one was created
            if temp_csv_path and os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)

    print("\nSQLite import process complete.")

if __name__ == "__main__":
    main()