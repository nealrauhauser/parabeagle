#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
from chromadb.api.collection_configuration import CreateCollectionConfiguration

from common import get_embedding_function, resolve_data_directory


def add_collection(data_dir, collection_name):
    """Create a new collection in the specified Chroma data directory."""
    try:
        client = chromadb.PersistentClient(path=data_dir)
        
        # Check if collection already exists
        try:
            existing = client.get_collection(collection_name)
            print(f"Collection '{collection_name}' already exists with {existing.count()} documents.")
            return 1
        except Exception:
            # Collection doesn't exist, which is what we want
            pass
        
        # Create collection with mpnet-768 embedding function and cosine distance
        embedding_function = get_embedding_function()
        configuration = CreateCollectionConfiguration(embedding_function=embedding_function)
        collection = client.create_collection(
            name=collection_name,
            configuration=configuration,
            metadata={'hnsw:space': 'cosine'}
        )
        
        print(f"Successfully created collection '{collection_name}' with mpnet-768 embeddings")
        return 0
            
    except Exception as e:
        print(f"Error creating collection: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create a new collection in a Chroma database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create collection in active directory
  python mkcol.py --collection-name MyDocs

  # Create collection in a specific directory by name
  python mkcol.py -n case-2024-001 --collection-name MyDocs

  # With custom data directory
  python mkcol.py -d /Users/brain/work/chroma/ --collection-name MyDocs
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", required=True,
                       help="Name of the collection to create")

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
    
    exit_code = add_collection(data_dir, args.collection_name)
    sys.exit(exit_code)