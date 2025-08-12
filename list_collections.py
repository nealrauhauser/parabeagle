#!/Users/brain/work/gits/chroma-mac/.venv/bin/python

import chromadb
import sys
import os

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
    
    if not args.data_dir:
        print("Error: Data directory must be provided via --data-dir flag or CHROMADIR environment variable")
        sys.exit(1)
    
    exit_code = list_collections(args.data_dir)
    sys.exit(exit_code)