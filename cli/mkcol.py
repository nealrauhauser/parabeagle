#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
import sqlite3
from chromadb.api.collection_configuration import CreateCollectionConfiguration
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    SentenceTransformerEmbeddingFunction,
)

# Same local embedding functions as MCP server
def create_local_embedding_functions():
    """Create embedding functions for local models only."""
    return {
        "default": DefaultEmbeddingFunction,  # all-MiniLM-L6-v2 (384 dims)
        "mpnet-768": lambda: SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-mpnet-base-v2"
        ),
        "minilm-384": lambda: SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        ),
    }

mcp_known_embedding_functions = create_local_embedding_functions()

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

def get_directory_by_name(base_dir, name):
    """Get a directory path by its name."""
    if not base_dir:
        return None

    db_path = os.path.join(base_dir, 'chroma_directories.sqlite3')
    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT path FROM directories WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
    except sqlite3.Error:
        pass

    return None

def add_collection(data_dir, collection_name, embedding_function_name="mpnet-768"):
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
        
        # Validate embedding function
        if embedding_function_name not in mcp_known_embedding_functions:
            print(f"Error: Unknown embedding function '{embedding_function_name}'")
            print(f"Available options: {', '.join(mcp_known_embedding_functions.keys())}")
            return 1
        
        # Get the embedding function class
        embedding_function = mcp_known_embedding_functions[embedding_function_name]
        
        # Create collection with embedding function and cosine distance
        configuration = CreateCollectionConfiguration(embedding_function=embedding_function())
        collection = client.create_collection(
            name=collection_name,
            configuration=configuration,
            metadata={'hnsw:space': 'cosine'}
        )
        
        print(f"Successfully created collection '{collection_name}' with '{embedding_function_name}' embeddings")
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
  python add_collection.py --collection-name MyDocs

  # Create collection in a specific directory by name
  python add_collection.py -n case-2024-001 --collection-name MyDocs

  # With custom embedding function
  python add_collection.py --collection-name MyDocs --embedding-function mpnet-768

  # With custom data directory
  python add_collection.py -d /Users/brain/work/chroma/ --collection-name MyDocs
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", required=True,
                       help="Name of the collection to create")
    parser.add_argument("-e", "--embedding-function",
                       choices=["default", "mpnet-768", "minilm-384"],
                       default="mpnet-768",
                       help="Embedding function to use (default: mpnet-768): default (384-dim), mpnet-768 (768-dim best quality), minilm-384 (384-dim explicit)")
    parser.add_argument("-n", "--directory-name",
                       help="Name of a specific directory to use (overrides active directory)")

    args = parser.parse_args()

    # Determine which directory to use
    data_dir = args.data_dir
    if data_dir:
        # If --directory-name is specified, use that directory by name
        if args.directory_name:
            named_dir = get_directory_by_name(data_dir, args.directory_name)
            if named_dir:
                data_dir = named_dir
            else:
                print(f"Error: Directory '{args.directory_name}' not found")
                sys.exit(1)
        else:
            # Otherwise, use active directory if available
            active_dir = get_active_directory(data_dir)
            if active_dir:
                data_dir = active_dir
    
    if not data_dir:
        print("Error: Data directory must be provided via --data-dir flag or CHROMADIR environment variable")
        sys.exit(1)
    
    exit_code = add_collection(data_dir, args.collection_name, args.embedding_function)
    sys.exit(exit_code)