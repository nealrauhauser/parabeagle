#!/usr/bin/env python3

"""
Quick test to verify 768-dimension embeddings are working correctly.
Shows the actual embedding dimensions for each model.
"""

import tempfile
import shutil
from add_collection import add_collection, create_local_embedding_functions
import chromadb

def test_embedding_dimensions():
    """Test and show the actual embedding dimensions for each model."""
    print("Testing Actual Embedding Dimensions")
    print("=" * 45)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        client = chromadb.PersistentClient(path=temp_dir)
        
        # Test each embedding function
        embedding_functions = create_local_embedding_functions()
        
        for name, func_factory in embedding_functions.items():
            print(f"\nTesting {name}:")
            
            try:
                # Create the embedding function
                embedding_func = func_factory()
                
                # Test with a simple document
                test_text = "The quick brown fox jumps over the lazy dog."
                embeddings = embedding_func([test_text])
                
                # Check dimensions
                if embeddings and len(embeddings) > 0:
                    dimensions = len(embeddings[0])
                    expected_dims = 768 if "768" in name else 384
                    
                    print(f"  ✓ Embedding dimensions: {dimensions}")
                    print(f"  ✓ Expected dimensions: {expected_dims}")
                    
                    if dimensions == expected_dims:
                        print(f"  PASS: Correct dimensions!")
                    else:
                        print(f"  FAIL: Expected {expected_dims}, got {dimensions}")
                else:
                    print(f"  FAIL: No embeddings generated")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
        
        print(f"\nSummary:")
        print(f"  - default: Should be 384 dimensions (all-MiniLM-L6-v2)")
        print(f"  - mpnet-768: Should be 768 dimensions (all-mpnet-base-v2)")
        print(f"  - bert-768: Should be 768 dimensions (all-distilroberta-v1)")  
        print(f"  - minilm-384: Should be 384 dimensions (all-MiniLM-L6-v2)")
        
    finally:
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory")

if __name__ == "__main__":
    test_embedding_dimensions()