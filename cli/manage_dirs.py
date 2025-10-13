#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import sqlite3
import sys
import os
import argparse
import re
import shutil
from pathlib import Path
import chromadb

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

def validate_directory_name(name: str) -> bool:
    """Validate directory name contains only alphanumeric chars, hyphens, and underscores."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

def add_directory(db_path: str, name: str, base_data_dir: str = None):
    """Add a new directory configuration using the name as both identifier and folder name."""
    # Validate name format
    if not validate_directory_name(name):
        print(f"Error: Directory name '{name}' contains invalid characters. Only letters, numbers, hyphens, and underscores are allowed.")
        return 1

    # Use name as the subdirectory path under base_data_dir
    if base_data_dir:
        full_path = os.path.join(base_data_dir, name)
    else:
        full_path = name

    # Create directory if it doesn't exist
    if not os.path.exists(full_path):
        try:
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error: Could not create directory {full_path}: {e}")
            return 1

    if not os.path.isdir(full_path):
        print(f"Error: Path is not a directory: {full_path}")
        return 1

    # Initialize ChromaDB in the new directory
    print(f"Initializing ChromaDB in {full_path}...")
    try:
        # Create a PersistentClient to initialize the ChromaDB database
        client = chromadb.PersistentClient(path=full_path)
        # Verify initialization by checking the heartbeat
        client.heartbeat()
        print(f"ChromaDB initialized successfully")
    except Exception as e:
        print(f"Error: Could not initialize ChromaDB in {full_path}: {e}")
        return 1

    # Initialize directory management DB if it doesn't exist
    if not os.path.exists(db_path):
        init_directory_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO directories (name, path)
            VALUES (?, ?)
        ''', (name, os.path.abspath(full_path)))
        conn.commit()
        print(f"Successfully added directory '{name}' -> {os.path.abspath(full_path)}")
        return 0
    except sqlite3.IntegrityError:
        print(f"Error: Directory name '{name}' already exists")
        return 1
    finally:
        conn.close()

def remove_directory(db_path: str, name: str, base_data_dir: str):
    """Remove a directory configuration and delete the physical directory."""
    if not os.path.exists(db_path):
        print("No directory database found.")
        return 1

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if it's the active directory and get the path
    cursor.execute('SELECT is_active, path FROM directories WHERE name = ?', (name,))
    result = cursor.fetchone()

    if not result:
        print(f"Error: Directory '{name}' not found")
        conn.close()
        return 1

    is_active, directory_path = result

    if is_active:
        # If it's the active directory, switch to the main directory first
        print(f"Directory '{name}' is active. Switching to main directory...")

        # Clear all active flags (makes main directory active by default)
        cursor.execute('UPDATE directories SET is_active = 0')
        conn.commit()

        print(f"Switched to main directory: {base_data_dir}")

    # Delete from database
    cursor.execute('DELETE FROM directories WHERE name = ?', (name,))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()

        # Delete the physical directory
        if os.path.exists(directory_path):
            try:
                shutil.rmtree(directory_path)
                print(f"Successfully removed directory '{name}' -> {directory_path}")
                print(f"  Physical directory deleted")
                return 0
            except Exception as e:
                print(f"Successfully removed directory '{name}' from database")
                print(f"  Warning: Could not delete physical directory {directory_path}: {e}")
                return 0
        else:
            print(f"Successfully removed directory '{name}'")
            print(f"  Physical directory was already deleted")
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
  
  # Add a new directory (creates subdirectory under main data directory)
  python manage_dirs.py --add case-2024-001
  
  # Remove a directory
  python manage_dirs.py --remove case-2024-001
  
  # Set active directory
  python manage_dirs.py --set-active case-2024-001
  
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
    action_group.add_argument("--add", nargs=1, metavar="NAME",
                             help="Add a new directory using NAME as both identifier and subdirectory name (created under main data directory)")
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
        name = args.add[0]
        sys.exit(add_directory(db_path, name, args.data_dir))
    elif args.remove:
        sys.exit(remove_directory(db_path, args.remove, args.data_dir))
    elif args.set_active:
        sys.exit(set_active_directory(db_path, args.set_active))
    elif args.show_active:
        sys.exit(get_active_directory(db_path))