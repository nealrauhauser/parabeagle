#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
from pathlib import Path
from collections import defaultdict

from common import get_active_directory


def list_files_in_collection(data_dir, collection_name, names_only=False):
    """List all original files in a collection."""
    try:
        client = chromadb.PersistentClient(path=data_dir)
        
        # Get the collection
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            print(f"Collection '{collection_name}' does not exist.")
            return 1
        
        if collection.count() == 0:
            print(f"Collection '{collection_name}' is empty.")
            return 0
        
        # Get all documents with metadata
        results = collection.get(include=['metadatas'])
        metadatas = results['metadatas']
        
        if not metadatas:
            print(f"No metadata found in collection '{collection_name}'.")
            return 0
        
        # Collect file information
        files = {}  # source_path -> {filename, chunk_count, total_size}
        
        for metadata in metadatas:
            if metadata and 'source' in metadata:
                source = metadata['source']
                filename = metadata.get('filename', Path(source).name)
                char_count = metadata.get('char_count', 0)
                
                if source not in files:
                    files[source] = {
                        'filename': filename,
                        'chunk_count': 0,
                        'total_chars': 0
                    }
                
                files[source]['chunk_count'] += 1
                files[source]['total_chars'] += char_count
        
        if not files:
            print(f"No source files found in collection '{collection_name}'.")
            return 0
        
        # Display results - clean output for Unix chains
        for source_path, info in sorted(files.items()):
            if names_only:
                print(info['filename'])
            else:
                print(source_path)
        
        return 0
        
    except Exception as e:
        print(f"Error listing files: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="List all original files in a Chroma collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List files with full paths
  python list_collection_files.py -c MyDocs
  
  # List just filenames
  python list_collection_files.py -c MyDocs --names-only
  
  # With custom data directory
  python list_collection_files.py -d /Users/brain/work/chroma/ -c MyDocs
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", required=True,
                       help="Name of the collection to list files from")
    parser.add_argument("-n", "--names-only", action="store_true",
                       help="Show only filenames, not full paths")
    
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
    
    exit_code = list_files_in_collection(
        data_dir, 
        args.collection_name, 
        names_only=args.names_only
    )
    sys.exit(exit_code)