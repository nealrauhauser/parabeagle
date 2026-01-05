#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os

from common import get_directory_by_name, resolve_data_directory


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
  # List collections in active directory
  python list_collections.py

  # List collections in a specific directory by name
  python list_collections.py -n case-2024-001

  # With custom data directory
  python list_collections.py -d /Users/brain/work/chroma/
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-n", "--directory-name",
                       help="Name of a specific directory to use (overrides active directory)")

    args = parser.parse_args()

    # Resolve the data directory
    data_dir = resolve_data_directory(args.data_dir, args.directory_name)

    if args.directory_name and not data_dir:
        print(f"Error: Directory '{args.directory_name}' not found")
        sys.exit(1)

    if not data_dir:
        print("Error: Data directory must be provided via --data-dir flag or CHROMADIR environment variable")
        sys.exit(1)
    
    exit_code = list_collections(data_dir)
    sys.exit(exit_code)