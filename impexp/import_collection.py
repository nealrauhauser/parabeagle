#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
import json
import zipfile
import sqlite3
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

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

def import_collection(data_dir, archive_path, collection_name=None, pdf_dir=None, force=False):
    """Import a Chroma collection from a zip archive."""
    try:
        if not os.path.exists(archive_path):
            print(f"Error: Archive file not found: {archive_path}")
            return 1

        if not zipfile.is_zipfile(archive_path):
            print(f"Error: File is not a valid zip archive: {archive_path}")
            return 1

        print(f"Reading archive: {archive_path}")

        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(temp_dir)

            # Find the collection directory (top-level directory in archive)
            extracted_items = os.listdir(temp_dir)
            if not extracted_items:
                print("Error: Archive is empty")
                return 1

            # Get the collection directory name (should be the only top-level item)
            collection_dir = os.path.join(temp_dir, extracted_items[0])

            # Read manifest
            manifest_path = os.path.join(collection_dir, "manifest.json")
            if not os.path.exists(manifest_path):
                print("Error: Invalid archive - missing manifest.json")
                return 1

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Read collection metadata
            collection_metadata_path = os.path.join(collection_dir, "collection_metadata.json")
            collection_metadata = {}
            if os.path.exists(collection_metadata_path):
                with open(collection_metadata_path, 'r') as f:
                    collection_metadata = json.load(f)

            # Read documents data
            documents_path = os.path.join(collection_dir, "documents.json")
            if not os.path.exists(documents_path):
                print("Error: Invalid archive - missing documents.json")
                return 1

            with open(documents_path, 'r') as f:
                export_data = json.load(f)

            # Use collection name from argument or manifest
            target_collection_name = collection_name or manifest['collection_name']

            print(f"\nArchive Information:")
            print(f"  Format version: {manifest['archive_format_version']}")
            print(f"  Created: {manifest['created_at']}")
            print(f"  Original collection: {manifest['collection_name']}")
            print(f"  Target collection: {target_collection_name}")
            print(f"  Documents: {manifest['document_count']}")
            print(f"  Chunks: {manifest['chunk_count']}")
            print(f"  PDFs: {manifest['pdf_count']}")
            print(f"  Embedding function: {manifest['embedding_function']}")
            print(f"  Distance metric: {manifest['distance_metric']}")

            # Check if collection already exists
            client = chromadb.PersistentClient(path=data_dir)
            collection_exists = False
            try:
                existing = client.get_collection(target_collection_name)
                collection_exists = True
                print(f"\n⚠ Warning: Collection '{target_collection_name}' already exists with {existing.count()} documents")

                if not force:
                    print("Use --force to overwrite the existing collection")
                    return 1

                print("Deleting existing collection...")
                client.delete_collection(target_collection_name)
            except Exception:
                pass

            # Create collection with proper configuration
            from chromadb.utils.embedding_functions import (
                DefaultEmbeddingFunction,
                SentenceTransformerEmbeddingFunction,
            )
            from chromadb.api.collection_configuration import CreateCollectionConfiguration

            def create_local_embedding_functions():
                """Create embedding functions for local models only."""
                return {
                    "default": DefaultEmbeddingFunction,
                    "mpnet-768": lambda: SentenceTransformerEmbeddingFunction(
                        model_name="sentence-transformers/all-mpnet-base-v2"
                    ),
                    "minilm-384": lambda: SentenceTransformerEmbeddingFunction(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    ),
                }

            mcp_known_embedding_functions = create_local_embedding_functions()
            embedding_fn_name = manifest.get('embedding_function', 'mpnet-768')

            if embedding_fn_name not in mcp_known_embedding_functions:
                print(f"Warning: Unknown embedding function '{embedding_fn_name}', using 'mpnet-768'")
                embedding_fn_name = 'mpnet-768'

            embedding_function = mcp_known_embedding_functions[embedding_fn_name]
            configuration = CreateCollectionConfiguration(embedding_function=embedding_function())

            # Prepare collection metadata
            coll_metadata = collection_metadata.get('metadata', {})
            coll_metadata['hnsw:space'] = manifest.get('distance_metric', 'cosine')
            coll_metadata['imported_from'] = os.path.basename(archive_path)
            coll_metadata['imported_at'] = datetime.utcnow().isoformat()

            print(f"\nCreating collection '{target_collection_name}'...")
            collection = client.create_collection(
                name=target_collection_name,
                configuration=configuration,
                metadata=coll_metadata
            )

            # Import documents in batches
            ids = export_data['ids']
            documents = export_data['documents']
            metadatas = export_data['metadatas']

            print(f"Importing {len(documents)} chunks...")

            # Update metadata paths if PDFs are being extracted
            if pdf_dir and manifest['pdf_count'] > 0:
                print(f"Extracting PDFs to: {pdf_dir}")
                os.makedirs(pdf_dir, exist_ok=True)

                # Extract PDFs
                pdf_path_mapping = {}
                pdfs_dir = os.path.join(collection_dir, "pdfs")
                if os.path.exists(pdfs_dir):
                    for pdf_info in manifest['pdfs']:
                        src = os.path.join(collection_dir, pdf_info['path'])
                        dst = os.path.join(pdf_dir, pdf_info['filename'])

                        if os.path.exists(src):
                            shutil.copy2(src, dst)
                            pdf_path_mapping[pdf_info['original_path']] = dst
                            print(f"  + {pdf_info['filename']}")

                # Update metadata with new paths
                for metadata in metadatas:
                    if metadata and 'source' in metadata:
                        old_path = metadata['source']
                        if old_path in pdf_path_mapping:
                            metadata['source'] = pdf_path_mapping[old_path]

            # Add documents in batches
            batch_size = 100
            total_added = 0

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]

                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                total_added += len(batch_docs)
                print(f"  Progress: {total_added}/{len(documents)} chunks")

            print(f"\n✓ Successfully imported collection '{target_collection_name}'")
            print(f"  Total documents: {collection.count()}")

            if pdf_dir and manifest['pdf_count'] > 0:
                print(f"  PDFs extracted to: {pdf_dir}")

            return 0

    except Exception as e:
        print(f"Error importing collection: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Import a Chroma collection from a portable zip archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import collection with original name
  python import_collection.py MyDocs.zip

  # Import with a different name
  python import_collection.py MyDocs.zip -c MyNewDocs

  # Import and extract PDFs to specific directory
  python import_collection.py MyDocs.zip --pdf-dir /path/to/pdfs/

  # Force overwrite existing collection
  python import_collection.py MyDocs.zip --force

  # With custom data directory
  python import_collection.py -d /Users/brain/work/chroma/ MyDocs.zip
        """
    )

    parser.add_argument("archive",
                       help="Path to the .zip archive file")
    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name",
                       help="Name for the imported collection (default: use original name from archive)")
    parser.add_argument("--pdf-dir",
                       help="Directory to extract PDF files to. If not specified, PDFs will be extracted to current directory's 'pdfs/' folder")
    parser.add_argument("--force", action="store_true",
                       help="Overwrite existing collection if it exists")

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

    # Default PDF directory if not specified
    pdf_dir = args.pdf_dir
    if pdf_dir is None:
        pdf_dir = os.path.join(os.getcwd(), "pdfs")

    exit_code = import_collection(
        data_dir,
        args.archive,
        collection_name=args.collection_name,
        pdf_dir=pdf_dir,
        force=args.force
    )
    sys.exit(exit_code)
