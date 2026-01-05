#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
from pathlib import Path

from common import resolve_data_directory


def delete_collection(data_dir, collection_name, confirm=False):
    """Delete a collection from the Chroma database."""
    try:
        client = chromadb.PersistentClient(path=data_dir)
        
        # Check if collection exists
        try:
            collection = client.get_collection(collection_name)
            document_count = collection.count()
        except Exception:
            print(f"Collection '{collection_name}' does not exist.")
            return 1
        
        # Show collection info
        print(f"Collection '{collection_name}' contains {document_count:,} documents.")
        
        # Confirmation prompt
        if not confirm:
            print(f"\nWARNING: This will permanently delete collection '{collection_name}' and all its documents!")
            response = input("Type 'yes' to confirm deletion: ").strip().lower()
            if response != 'yes':
                print("Deletion cancelled.")
                return 0
        
        # Delete the collection
        client.delete_collection(collection_name)
        print(f"Collection '{collection_name}' has been deleted successfully.")
        return 0
        
    except Exception as e:
        print(f"Error deleting collection: {e}")
        return 1

def list_all_collections(data_dir):
    """List all collections for reference."""
    try:
        client = chromadb.PersistentClient(path=data_dir)
        collections = client.list_collections()
        
        if not collections:
            print("No collections found in database.")
            return
        
        print(f"Found {len(collections)} collection(s):")
        for collection in collections:
            try:
                doc_count = collection.count()
                print(f"  - {collection.name} ({doc_count:,} documents)")
            except Exception as e:
                print(f"  - {collection.name} (error counting: {e})")
                
    except Exception as e:
        print(f"Error listing collections: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Delete a collection from Chroma database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all collections first
  python delete_collection.py --list

  # Delete a collection from active directory (with confirmation prompt)
  python delete_collection.py -c MyCollection

  # Delete a collection from a specific directory by name
  python delete_collection.py -n case-2024-001 -c MyCollection

  # Force delete without confirmation (dangerous!)
  python delete_collection.py -c MyCollection --force

  # With specific data directory
  python delete_collection.py -d /Users/brain/work/chroma/ -c MyCollection
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", 
                       help="Name of the collection to delete")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List all collections and exit")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Delete without confirmation prompt (dangerous!)")
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
    
    # Validate data directory
    if not os.path.exists(data_dir):
        print(f"Error: Directory {data_dir} does not exist")
        sys.exit(1)
    
    if not os.path.isdir(data_dir):
        print(f"Error: {data_dir} is not a directory")
        sys.exit(1)
    
    # List collections mode
    if args.list:
        list_all_collections(data_dir)
        sys.exit(0)
    
    # Delete collection mode
    if not args.collection_name:
        print("Error: Collection name is required unless using --list")
        print("Use --help for usage information")
        sys.exit(1)
    
    if args.force:
        print("FORCE MODE: Deleting without confirmation!")
    
    exit_code = delete_collection(data_dir, args.collection_name, confirm=args.force)
    sys.exit(exit_code)