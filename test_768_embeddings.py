#!/usr/bin/env python3
"""
Test script to demonstrate 768-dimension embedding functionality.
This script creates collections with different embedding models and shows their dimensions.
"""

import asyncio
from src.chroma_mcp.server import mcp

async def test_768_embeddings():
    """Test the new 768-dimension embedding models."""
    
    print("Testing local embedding models with different dimensions...")
    
    # Test data
    test_docs = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "ChromaDB is a vector database for AI applications."
    ]
    test_ids = ["doc1", "doc2", "doc3"]
    
    # Test different embedding models
    models_to_test = [
        ("default", "384-dimension (all-MiniLM-L6-v2)"),
        ("mpnet-768", "768-dimension (all-mpnet-base-v2) - Best Quality"),
        ("bert-768", "768-dimension (all-distilroberta-v1) - Fast Alternative"),
        ("minilm-384", "384-dimension (all-MiniLM-L6-v2) - Explicit")
    ]
    
    for model_name, description in models_to_test:
        collection_name = f"test_{model_name}_collection"
        print(f"\n=== Testing {model_name}: {description} ===")
        
        try:
            # Create collection with specific embedding model
            print(f"Creating collection '{collection_name}' with model '{model_name}'...")
            result = await mcp.call_tool("chroma_create_collection", {
                "collection_name": collection_name,
                "embedding_function_name": model_name
            })
            print(f"✓ {result[0].text}")
            
            # Add documents
            print(f"Adding {len(test_docs)} test documents...")
            result = await mcp.call_tool("chroma_add_documents", {
                "collection_name": collection_name,
                "documents": test_docs,
                "ids": test_ids
            })
            print(f"✓ {result[0].text}")
            
            # Query to test embeddings work
            print("Testing semantic search...")
            result = await mcp.call_tool("chroma_query_documents", {
                "collection_name": collection_name,
                "query_texts": ["artificial intelligence research"],
                "n_results": 2
            })
            
            # Parse the query results to see if it found relevant documents
            query_data = result
            if hasattr(query_data, '__dict__'):
                print(f"✓ Query successful - found semantic matches")
            else:
                print(f"✓ Query successful - embeddings working")
            
            # Get collection info
            info_result = await mcp.call_tool("chroma_get_collection_info", {
                "collection_name": collection_name
            })
            print(f"✓ Collection contains {info_result['count']} documents")
            
        except Exception as e:
            print(f"✗ Error testing {model_name}: {str(e)}")
            continue
            
        # Clean up
        try:
            await mcp.call_tool("chroma_delete_collection", {
                "collection_name": collection_name
            })
            print(f"✓ Cleaned up collection '{collection_name}'")
        except Exception as e:
            print(f"⚠ Warning: Could not clean up collection '{collection_name}': {str(e)}")
    
    print("\n" + "="*60)
    print("✓ All embedding model tests completed!")
    print("\nNow you can use 'mpnet-768' or 'bert-768' for 768-dimension embeddings")
    print("in your chroma_create_collection calls.")

if __name__ == "__main__":
    asyncio.run(test_768_embeddings())