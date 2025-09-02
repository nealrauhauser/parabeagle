#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
import sqlite3

def get_active_directory(base_dir):
    """Get the currently active directory from the directory database."""
    if not base_dir:
        return None
        
    db_path = os.path.join(base_dir, 'chroma_directories.sqlite3')
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT path FROM directories WHERE is_active = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
    except sqlite3.Error:
        pass
    
    return None

def list_collections(data_dir):
    """List all collections in the specified Chroma data directory."""
    try:
        client = chromadb.PersistentClient(path=data_dir)
        collections = client.list_collections()
        
        if not collections:
            print("No collections found in the database.")
            return
        
        print(f"Found {len(collections)} collection(s):")
        for collection in collections:
            count = collection.count()
            print(f"  - {collection.name} ({count} documents)")
            
    except Exception as e:
        print(f"Error accessing Chroma database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="List all collections in a Chroma database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python list_collections.py
  python list_collections.py -d /Users/brain/work/chroma/
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    
    args = parser.parse_args()
    
    # Try to get active directory first, fall back to provided/env directory
    data_dir = args.data_dir
    if data_dir:
        active_dir = get_active_directory(data_dir)
        if active_dir:
            data_dir = active_dir
    
    if not data_dir:
        print("Error: Data directory must be provided via --data-dir flag or CHROMADIR environment variable")
        sys.exit(1)
    
    exit_code = list_collections(data_dir)
    sys.exit(exit_code)