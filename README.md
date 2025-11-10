 Title: Data Import Utilities for CSV Files

This repository contains three command-line utilities designed to import CSV files into popular databases. These tools are useful when dealing with large datasets in CSV format and aim to make the data migration process more efficient.

### Supported Databases
1. PostgreSQL
2. SQLite
3. MySQL (for MySQL, you will need the `mysql-cli` or `psql` command installed)

### Contents of this Repository

#### 1. Import CSV to PostgreSQL (`import_csv_to_postgres.py`)

This script imports CSV files into a specified PostgreSQL database table. It reads the header line from each CSV file and creates a new table if it does not exist, or uses an existing one if present. The utility supports both compressed (`.csv.gz`) and uncompressed (`.csv`) files.

#### 2. Import CSV to SQLite (`import_csv_to_sqlite.py`)

This script imports CSV files into a specified SQLite database table. Similar to the PostgreSQL tool, it reads the header line from each CSV file and creates a new table if it does not exist, or uses an existing one if present. The utility supports both compressed (`.csv.gz`) and uncompressed (`.csv`) files.

#### 3. Import CSV to MySQL (`import_csv_to_mysql.py`)

This script imports CSV files into a specified MySQL database table using the `LOAD DATA INFILE` command. You will need to have `mysql-cli` or `psql` installed to use this tool. It reads the header line from each CSV file and creates a new table if it does not exist, or uses an existing one if present. The utility supports both compressed (`.csv.gz`) and uncompressed (`.csv`) files.

### Usage

Each script requires only three command-line arguments: the input directory containing CSV files, the output database file/path for SQLite and MySQL, and the PostgreSQL database name for `import_csv_to_postgres.py`.

For example:
```bash
python import_csv_to_sqlite.py /path/to/csv/files mydatabase.db mydatabase.db # SQLite example
python import_csv_to_mysql.py /path/to/csv/files user password dbname csv_file.csv # MySQL example
python import_csv_to_postgres.py /path/to/csv/files dbname user password # PostgreSQL example
```

### Support and Contributions

Contributions, bug reports, and suggestions are welcome! If you encounter any issues or have ideas for new features, please open an issue in the repository.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.