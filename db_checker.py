
import shutil
import sys
import os
import glob

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Dictionary of common, non-PATH locations for database tools
# This is the structure you requested.
SEARCH_PATHS = {
    'darwin': { # macOS
        'psql': ['/Applications/Postgres.app/Contents/Versions/latest/bin', '/usr/local/bin', '/opt/homebrew/bin'],
        'mysql': ['/usr/local/mysql/bin', '/usr/local/bin', '/opt/homebrew/bin'],
        'isql': ['/Library/Frameworks/Firebird.framework/Versions/Current/Resources/bin', '/usr/local/bin', '/opt/firebird/bin'],
        'sqlite3': ['/usr/bin']
    },
    'linux': { # Linux
        'psql': ['/usr/bin', '/usr/local/bin', '/opt/postgresql/bin'],
        'mysql': ['/usr/bin', '/usr/local/bin'],
        'isql': ['/opt/firebird/bin', '/usr/bin', '/usr/local/bin'],
        'sqlite3': ['/usr/bin']
    },
    'win32': { # Windows
        # Use glob to handle version numbers in paths
        'psql': glob.glob('C:\\Program Files\\PostgreSQL\\*\\bin'),
        'mysql': glob.glob('C:\\Program Files\\MySQL\\MySQL Server *\\bin'),
        'isql': glob.glob('C:\\Program Files\\Firebird\\Firebird_*'),
        'sqlite3': ['C:\\sqlite'] # sqlite3.exe is often manually placed
    }
}

def check_tool(tool_name, tool_description):
    """Checks for a tool using `which` and then searches common paths."""
    print(f"{Colors.BOLD}{Colors.BLUE}Checking for: {tool_description} ({tool_name}){Colors.RESET}")
    
    # 1. Check PATH first - the most reliable method
    path_from_which = shutil.which(tool_name)
    if path_from_which:
        print(f"  {Colors.GREEN}[ FOUND ]{Colors.RESET} Found at: {path_from_which}")
        return

    # 2. If not in PATH, check the predefined search paths for the current OS
    print(f"  {Colors.YELLOW}[ NOT IN PATH ]{Colors.RESET} Searching common directories...")
    platform = sys.platform
    if platform in SEARCH_PATHS and tool_name in SEARCH_PATHS[platform]:
        for path in SEARCH_PATHS[platform][tool_name]:
            # Handle glob paths for Windows
            if '*' in path or '?' in path:
                possible_paths = glob.glob(path)
                for p in possible_paths:
                    full_path = os.path.join(p, tool_name)
                    if os.path.isfile(full_path) or os.path.isfile(full_path + '.exe'):
                        print(f"  {Colors.GREEN}[ FOUND ]{Colors.RESET} Found at: {full_path}")
                        return
            else:
                full_path = os.path.join(path, tool_name)
                if os.path.isfile(full_path) or os.path.isfile(full_path + '.exe'):
                    print(f"  {Colors.GREEN}[ FOUND ]{Colors.RESET} Found at: {full_path}")
                    return

    print(f"  {Colors.RED}[ NOT FOUND ]{Colors.RESET} Could not find {tool_name} in PATH or common directories.")

def main():
    """Main function to run all checks."""
    print(f"{Colors.BOLD}Starting database tool checks...{Colors.RESET}")
    
    check_tool('psql', 'PostgreSQL Client')
    check_tool('mysql', 'MySQL Client')
    check_tool('isql', 'Firebird SQL Client')
    check_tool('sqlite3', 'SQLite3 Client')
    
    print(f"\n{Colors.BOLD}Checks complete.{Colors.RESET}")

if __name__ == "__main__":
    main()
