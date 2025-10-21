import subprocess
import argparse
import os
import sys
import gzip

def _is_junk_line(line):
    """Checks if a line from isql output is a header, separator, or empty."""
    stripped = line.strip()
    if not stripped:
        return True  # Is junk (empty)
    # Check if the line is composed only of '=' characters.
    if all(c == '=' for c in stripped):
        return True  # Is junk (separator)
    if stripped in {'RDB$RELATION_NAME', 'RDB$FIELD_NAME'}:
        return True  # Is junk (header)
    return False

def run_isql_command(isql_path, uri, username, password, command, encoding='utf-8'):
    """
    Executes a command or query using the isql tool and cleans the output.
    """
    try:
        process = subprocess.run(
            [isql_path, uri, "-u", username, "-p", password, "-q"],
            input=command,
            text=True,
            capture_output=True,
            check=True,
            encoding=encoding
        )
        lines = process.stdout.strip().split('\n')
        cleaned_lines = [line.strip() for line in lines if not _is_junk_line(line)]
        return cleaned_lines
    except UnicodeDecodeError as e:
        print(f"A character encoding error occurred. The database output is not valid '{encoding}'.", file=sys.stderr)
        print(f"Try using a different encoding with the --encoding flag, such as 'latin-1' or 'cp1252'.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing isql command.", file=sys.stderr)
        print(f"Command: {command}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: The isql executable was not found at '{isql_path}'. Please check the path.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Export tables from a Firebird database to CSV files.")
    parser.add_argument('--uri', required=True, help='URI for the Firebird database.')
    parser.add_argument('--username', required=True, help='Firebird username.')
    parser.add_argument('--password', required=True, help='Firebird password.')
    parser.add_argument('--isql-path', required=True, help='Full path to the isql executable.')
    parser.add_argument('--output-dir', required=True, help='Directory to save the output files.')
    parser.add_argument('--encoding', default='utf-8', help='Character encoding of the Firebird output (e.g., latin-1, cp1252).')
    parser.add_argument('--compress', action='store_true', help='Compress the output files using gzip (.csv.gz).')
    args = parser.parse_args()

    try:
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"Output files will be saved in: {args.output_dir}")
    except OSError as e:
        print(f"Error creating output directory '{args.output_dir}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching table list from Firebird database (using {args.encoding} encoding)...")
    get_tables_sql = "SELECT rdb$relation_name FROM rdb$relations WHERE rdb$system_flag = 0 AND rdb$view_blr IS NULL;"
    tables = run_isql_command(args.isql_path, args.uri, args.username, args.password, get_tables_sql, encoding=args.encoding)
    print(f"Found {len(tables)} tables.")

    for table_name in tables:
        print(f"  - Processing table: {table_name}...")

        columns = run_isql_command(args.isql_path, args.uri, args.username, args.password, 
            f"SELECT rdb$field_name FROM rdb$relation_fields WHERE rdb$relation_name = '{table_name}' ORDER BY rdb$field_position;",
            encoding=args.encoding
        )
        
        if not columns:
            print(f"    - Warning: Could not find columns for table '{table_name}'. Skipping.")
            continue

        file_extension = '.csv.gz' if args.compress else '.csv'
        csv_file_path = os.path.join(args.output_dir, f"{table_name}{file_extension}")
        
        open_func = gzip.open if args.compress else open

        try:
            with open_func(csv_file_path, 'wt', newline='', encoding='utf-8') as f:
                f.write('|'.join(columns) + '\n')

            select_parts = [f"COALESCE(CAST(\"{col}\" AS VARCHAR(1024)), '')" for col in columns]
            data_export_sql = f"SET HEADING OFF; SELECT { ' || \'|\' || '.join(select_parts) } FROM \"{table_name}\";"

            process = subprocess.Popen(
                [args.isql_path, args.uri, "-u", args.username, "-p", args.password, "-q"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding=args.encoding
            )

            process.stdin.write(data_export_sql)
            process.stdin.close()

            rows_exported = 0
            # The streaming part of the script no longer needs to do its own cleaning,
            # as the SET HEADING OFF command should prevent headers and separators.
            # We write the raw line directly.
            with open_func(csv_file_path, 'at', newline='', encoding='utf-8') as f:
                for line in process.stdout:
                    f.write(line)
                    if line.strip(): # Count non-empty rows
                        rows_exported += 1
            
            return_code = process.wait()
            if return_code != 0:
                stderr_output = process.stderr.read()
                print(f"    - Error streaming data for table '{table_name}'.", file=sys.stderr)
                print(f"    - Stderr: {stderr_output}", file=sys.stderr)
                continue

            print(f"    - Successfully exported {rows_exported} rows to {os.path.basename(csv_file_path)}")

        except (IOError, subprocess.SubprocessError, UnicodeDecodeError) as e:
            print(f"    - An error occurred while processing table '{table_name}': {e}", file=sys.stderr)
            if isinstance(e, UnicodeDecodeError):
                 print(f"    - Try using a different encoding with the --encoding flag, such as 'latin-1' or 'cp1252'.", file=sys.stderr)

    print("\nExport process complete.")

if __name__ == "__main__":
    main()