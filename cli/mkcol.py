#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
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
        "bert-768": lambda: SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-distilroberta-v1"
        ),
        "minilm-384": lambda: SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        ),
    }

mcp_known_embedding_functions = create_local_embedding_functions()

def add_collection(data_dir, collection_name, embedding_function_name="default"):
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
        
        # Create collection with embedding function
        configuration = CreateCollectionConfiguration(
            embedding_function=embedding_function()
        )
        collection = client.create_collection(
            name=collection_name, 
            configuration=configuration
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
  python add_collection.py --collection-name MyDocs
  python add_collection.py -d /Users/brain/work/chroma/ --collection-name MyDocs
  python add_collection.py --collection-name MyDocs --embedding-function mpnet-768
        """
    )
    
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", required=True,
                       help="Name of the collection to create")
    parser.add_argument("-e", "--embedding-function", 
                       choices=["default", "mpnet-768", "bert-768", "minilm-384"],
                       default="default",
                       help="Embedding function to use: default (384-dim), mpnet-768 (768-dim best quality), bert-768 (768-dim fast), minilm-384 (384-dim explicit)")
    
    args = parser.parse_args()
    
    if not args.data_dir:
        print("Error: Data directory must be provided via --data-dir flag or CHROMADIR environment variable")
        sys.exit(1)
    
    exit_code = add_collection(args.data_dir, args.collection_name, args.embedding_function)
    sys.exit(exit_code)