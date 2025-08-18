#!/Users/brain/work/gits/chroma-mac/.venv/bin/python

import sqlite3
import sys
import os
import argparse
from pathlib import Path

def get_directory_db_path(base_dir: str) -> str:
    """Get the path to the directory management database."""
    return os.path.join(base_dir, 'chroma_directories.sqlite3')

def init_directory_db(db_path: str):
    """Initialize the directory management database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create directories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            path TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def list_directories(db_path: str):
    """List all configured directories."""
    if not os.path.exists(db_path):
        print("No directory database found. Initialize with --init first.")
        return 1
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, path, is_active, created_at 
        FROM directories 
        ORDER BY name
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No directories configured")
        return 0
    
    print("Configured directories:")
    for row in rows:
        name, path, is_active, created_at = row
        status = " (ACTIVE)" if is_active else ""
        print(f"  {name}: {path}{status}")
        print(f"    Created: {created_at}")
    
    return 0

def add_directory(db_path: str, name: str, path: str):
    """Add a new directory configuration."""
    # Validate path exists
    if not os.path.exists(path):
        print(f"Error: Directory does not exist: {path}")
        return 1
    
    if not os.path.isdir(path):
        print(f"Error: Path is not a directory: {path}")
        return 1
    
    # Initialize DB if it doesn't exist
    if not os.path.exists(db_path):
        init_directory_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO directories (name, path) 
            VALUES (?, ?)
        ''', (name, os.path.abspath(path)))
        conn.commit()
        print(f"Successfully added directory '{name}' -> {os.path.abspath(path)}")
        return 0
    except sqlite3.IntegrityError:
        print(f"Error: Directory name '{name}' already exists")
        return 1
    finally:
        conn.close()

def remove_directory(db_path: str, name: str):
    """Remove a directory configuration."""
    if not os.path.exists(db_path):
        print("No directory database found.")
        return 1
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if it's the active directory
    cursor.execute('SELECT is_active FROM directories WHERE name = ?', (name,))
    result = cursor.fetchone()
    
    if not result:
        print(f"Error: Directory '{name}' not found")
        conn.close()
        return 1
    
    if result[0]:  # is_active
        print(f"Error: Cannot remove active directory '{name}'. Set another directory as active first.")
        conn.close()
        return 1
    
    cursor.execute('DELETE FROM directories WHERE name = ?', (name,))
    if cursor.rowcount > 0:
        conn.commit()
        print(f"Successfully removed directory '{name}'")
        conn.close()
        return 0
    else:
        print(f"Directory '{name}' not found")
        conn.close()
        return 1

def set_active_directory(db_path: str, name: str):
    """Set the active directory."""
    if not os.path.exists(db_path):
        print("No directory database found.")
        return 1
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if directory exists
    cursor.execute('SELECT path FROM directories WHERE name = ?', (name,))
    result = cursor.fetchone()
    
    if not result:
        print(f"Error: Directory '{name}' not found")
        conn.close()
        return 1
    
    directory_path = result[0]
    
    # Verify directory still exists on filesystem
    if not os.path.exists(directory_path):
        print(f"Error: Directory path no longer exists: {directory_path}")
        conn.close()
        return 1
    
    # Clear all active flags
    cursor.execute('UPDATE directories SET is_active = 0')
    
    # Set new active directory
    cursor.execute('UPDATE directories SET is_active = 1 WHERE name = ?', (name,))
    
    conn.commit()
    conn.close()
    
    print(f"Successfully set active directory to '{name}' -> {directory_path}")
    return 0

def get_active_directory(db_path: str):
    """Get the currently active directory."""
    if not os.path.exists(db_path):
        print("No directory database found.")
        return 1
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, path FROM directories WHERE is_active = 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        name, path = result
        print(f"Active directory: {name} -> {path}")
        return 0
    else:
        print("No active directory set")
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage Chroma directory configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize directory database
  python manage_dirs.py --init
  
  # List all directories
  python manage_dirs.py --list
  
  # Add a new directory
  python manage_dirs.py --add mydata /path/to/data
  
  # Remove a directory
  python manage_dirs.py --remove mydata
  
  # Set active directory
  python manage_dirs.py --set-active mydata
  
  # Show active directory
  python manage_dirs.py --show-active
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Base directory for Chroma database storage (default: CHROMADIR environment variable)")
    
    # Actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--init", action="store_true",
                             help="Initialize directory management database")
    action_group.add_argument("--list", action="store_true",
                             help="List all configured directories")
    action_group.add_argument("--add", nargs=2, metavar=("NAME", "PATH"),
                             help="Add a new directory with symbolic name and path")
    action_group.add_argument("--remove", metavar="NAME",
                             help="Remove a directory configuration by name")
    action_group.add_argument("--set-active", metavar="NAME",
                             help="Set the active directory by name")
    action_group.add_argument("--show-active", action="store_true",
                             help="Show the currently active directory")
    
    args = parser.parse_args()
    
    if not args.data_dir:
        print("Error: Data directory must be provided via --data-dir flag or CHROMADIR environment variable")
        sys.exit(1)
    
    db_path = get_directory_db_path(args.data_dir)
    
    if args.init:
        init_directory_db(db_path)
        print(f"Initialized directory database: {db_path}")
        sys.exit(0)
    elif args.list:
        sys.exit(list_directories(db_path))
    elif args.add:
        name, path = args.add
        sys.exit(add_directory(db_path, name, path))
    elif args.remove:
        sys.exit(remove_directory(db_path, args.remove))
    elif args.set_active:
        sys.exit(set_active_directory(db_path, args.set_active))
    elif args.show_active:
        sys.exit(get_active_directory(db_path))