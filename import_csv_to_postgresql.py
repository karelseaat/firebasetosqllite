import subprocess
import argparse
import os
import sys
import glob
import gzip

def run_psql_command(command, db_config):
    """
    Executes a command using the psql tool.
    It uses the PGPASSWORD environment variable for the password.
    """
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    psql_command = [
        'psql',
        '--host', db_config['host'],
        '--port', db_config['port'],
        '--dbname', db_config['dbname'],
        '--username', db_config['user'],
        '--command', command
    ]

    try:
        process = subprocess.run(
            psql_command, 
            env=env, 
            check=True, 
            capture_output=True, 
            text=True
        )
        return process.stdout
    except FileNotFoundError:
        print("Error: 'psql' command not found. Please ensure the PostgreSQL client tools are installed and in your system's PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing psql command.", file=sys.stderr)
        print(f"Command: {command}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Import CSV or compressed CSV files into a PostgreSQL database.")
    parser.add_argument('--input-dir', required=True, help='Directory containing the .csv or .csv.gz files.')
    parser.add_argument('--dbname', required=True, help='PostgreSQL database name.')
    parser.add_argument('--user', required=True, help='PostgreSQL username.')
    parser.add_argument('--password', required=True, help='PostgreSQL password.')
    parser.add_argument('--host', default='localhost', help='PostgreSQL server host (default: localhost).')
    parser.add_argument('--port', default='5432', help='PostgreSQL server port (default: 5432).')
    args = parser.parse_args()

    db_config = {
        'dbname': args.dbname,
        'user': args.user,
        'password': args.password,
        'host': args.host,
        'port': args.port
    }

    # Search for both compressed and uncompressed files
    csv_files = glob.glob(os.path.join(args.input_dir, '*.csv'))
    gz_files = glob.glob(os.path.join(args.input_dir, '*.csv.gz'))
    all_files = csv_files + gz_files

    if not all_files:
        print(f"Error: No .csv or .csv.gz files found in '{args.input_dir}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(all_files)} files to import into PostgreSQL database '{args.dbname}'.")

    for file_path in all_files:
        is_compressed = file_path.endswith('.gz')
        table_name = os.path.basename(file_path).split('.')[0].lower()
        print(f"  - Processing '{os.path.basename(file_path)}' into table '{table_name}'...")

        try:
            # Reading the header is the same for both compressed and uncompressed files
            # thanks to Python's gzip and open modules having a similar interface.
            open_func = gzip.open if is_compressed else open
            with open_func(file_path, 'rt', encoding='utf-8') as f:
                header = f.readline().strip()
                if not header:
                    print(f"    - Warning: File '{file_path}' is empty or has no header. Skipping.")
                    continue
                columns = header.split('|')

            column_defs = ", ".join([f'\"{col}\" TEXT' for col in columns])
            create_table_sql = f'CREATE TABLE IF NOT EXISTS \"{table_name}\" ({column_defs});'
            
            if run_psql_command(create_table_sql, db_config) is None:
                print(f"    - Failed to create table '{table_name}'. Skipping import for this file.")
                continue

            # Use \copy FROM PROGRAM for compressed files, which is highly efficient.
            if is_compressed:
                # Note: 'gunzip -c' is standard on Linux/macOS. Requires gunzip to be in the PATH.
                copy_sql = f"\\copy \"{table_name}\" FROM PROGRAM 'gunzip -c \"{os.path.abspath(file_path)}\"'
 WITH (FORMAT csv, DELIMITER '|', HEADER true)"
            else:
                copy_sql = f"\\copy \"{table_name}\" FROM \'"{os.path.abspath(file_path)}\"\' WITH (FORMAT csv, DELIMITER '|', HEADER true)"
            
            if run_psql_command(copy_sql, db_config) is not None:
                print(f"    - Successfully imported data into table '{table_name}'.")
            else:
                print(f"    - Failed to import data for table '{table_name}'.")

        except Exception as e:
            print(f"    - An unexpected error occurred: {e}", file=sys.stderr)

    print("\nPostgreSQL import process complete.")

if __name__ == "__main__":
    main()