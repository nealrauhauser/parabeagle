#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
import json
import zipfile
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import shutil
from collections import defaultdict
import tempfile

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

def calculate_sha256(file_path):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_segment_ids(data_dir, collection_id):
    """Get all segment IDs for a collection from the ChromaDB database."""
    db_path = os.path.join(data_dir, "chroma.sqlite3")
    if not os.path.exists(db_path):
        return []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, scope FROM segments WHERE collection = ?
        """, (collection_id,))
        segments = [{"id": row[0], "scope": row[1]} for row in cursor.fetchall()]
        conn.close()
        return segments
    except sqlite3.Error:
        return []

def export_collection(data_dir, collection_name, output_path, include_pdfs=True):
    """Export a Chroma collection to a tar.gz archive."""
    try:
        client = chromadb.PersistentClient(path=data_dir)

        # Get the collection
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            print(f"Error: Collection '{collection_name}' does not exist.")
            return 1

        collection_id = str(collection.id)
        doc_count = collection.count()

        print(f"Exporting collection '{collection_name}' (ID: {collection_id})")
        print(f"  Documents: {doc_count}")

        # Get all documents with metadata
        results = collection.get(include=['metadatas', 'documents'])
        metadatas = results['metadatas']
        documents = results['documents']
        ids = results['ids']

        # Get collection metadata
        collection_metadata = {
            "name": collection_name,
            "metadata": collection.metadata or {},
            "chunking_params": {
                "chunk_type": "semantic"  # Can be extracted from metadata if available
            }
        }

        # Collect PDF information
        pdf_files = {}  # source_path -> {filename, chunks, size}
        chunk_count = 0

        for metadata in metadatas:
            if metadata and 'source' in metadata:
                source = metadata['source']
                filename = metadata.get('filename', Path(source).name)

                if source not in pdf_files:
                    pdf_files[source] = {
                        'filename': filename,
                        'chunks': 0,
                        'size_bytes': 0
                    }

                pdf_files[source]['chunks'] += 1
                chunk_count += 1

        print(f"  Chunks: {chunk_count}")
        print(f"  Source PDFs: {len(pdf_files)}")

        # Get segment IDs
        segments = get_segment_ids(data_dir, collection_id)
        print(f"  Segments: {len(segments)}")

        # Determine output path
        if not output_path:
            output_path = f"{collection_name}.zip"
        elif os.path.isdir(output_path):
            output_path = os.path.join(output_path, f"{collection_name}.zip")

        print(f"\nCreating archive: {output_path}")

        # Create temporary directory for staging files
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_root = os.path.join(temp_dir, collection_name)
            os.makedirs(archive_root, exist_ok=True)

            # Add PDFs if requested and available
            pdf_manifest = []
            if include_pdfs:
                print("Adding PDFs...")
                pdf_dir = os.path.join(archive_root, "pdfs")
                os.makedirs(pdf_dir, exist_ok=True)

                for source_path, info in pdf_files.items():
                    if os.path.exists(source_path):
                        filename = info['filename']
                        dest_path = os.path.join(pdf_dir, filename)

                        # Calculate hash
                        file_size = os.path.getsize(source_path)
                        file_hash = calculate_sha256(source_path)

                        shutil.copy2(source_path, dest_path)
                        print(f"  + {filename} ({file_size:,} bytes)")

                        pdf_manifest.append({
                            "filename": filename,
                            "path": f"pdfs/{filename}",
                            "original_path": source_path,
                            "size_bytes": file_size,
                            "chunks": info['chunks'],
                            "sha256": file_hash
                        })
                    else:
                        print(f"  ! Warning: PDF not found: {source_path}")

            # Add ChromaDB database
            print("Adding ChromaDB database...")
            chroma_dir = os.path.join(archive_root, "chroma")
            os.makedirs(chroma_dir, exist_ok=True)

            db_path = os.path.join(data_dir, "chroma.sqlite3")
            if os.path.exists(db_path):
                shutil.copy2(db_path, os.path.join(chroma_dir, "chroma.sqlite3"))
                print(f"  + chroma.sqlite3")

            # Add segment directories
            print("Adding vector segments...")
            for segment in segments:
                segment_id = segment['id']
                segment_src_dir = os.path.join(data_dir, segment_id)
                segment_dest_dir = os.path.join(chroma_dir, segment_id)

                if os.path.exists(segment_src_dir):
                    shutil.copytree(segment_src_dir, segment_dest_dir)
                    print(f"  + {segment_id}/ ({segment['scope']})")
                    segment['path'] = f"chroma/{segment_id}"

            # Create manifest
            embedding_fn = "mpnet-768"  # Default, could be extracted from collection metadata
            if collection.metadata and 'embedding_function' in collection.metadata:
                embedding_fn = collection.metadata['embedding_function']

            distance_metric = "cosine"  # Default
            if collection.metadata and 'hnsw:space' in collection.metadata:
                distance_metric = collection.metadata['hnsw:space']

            manifest = {
                "parabeagle_version": "1.0",
                "archive_format_version": "1.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "collection_name": collection_name,
                "collection_id": collection_id,
                "embedding_function": embedding_fn,
                "distance_metric": distance_metric,
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "pdf_count": len(pdf_manifest),
                "total_size_bytes": sum(p['size_bytes'] for p in pdf_manifest),
                "pdfs": pdf_manifest,
                "segments": segments
            }

            # Write manifest
            with open(os.path.join(archive_root, "manifest.json"), 'w') as f:
                json.dump(manifest, f, indent=2)
            print("  + manifest.json")

            # Write collection metadata
            with open(os.path.join(archive_root, "collection_metadata.json"), 'w') as f:
                json.dump(collection_metadata, f, indent=2)
            print("  + collection_metadata.json")

            # Write all documents and metadata for full recovery
            export_data = {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas
            }
            with open(os.path.join(archive_root, "documents.json"), 'w') as f:
                json.dump(export_data, f, indent=2)
            print("  + documents.json")

            # Create zip archive
            print(f"\nCompressing archive...")
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(archive_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)

        file_size = os.path.getsize(output_path)
        print(f"\n✓ Successfully created archive: {output_path}")
        print(f"  Archive size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")

        return 0

    except Exception as e:
        print(f"Error exporting collection: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Export a Chroma collection to a portable zip archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export collection to default location (CollectionName.zip)
  python export_collection.py -c MyDocs

  # Export to specific file
  python export_collection.py -c MyDocs -o /path/to/backup.zip

  # Export to directory (creates MyDocs.zip in that directory)
  python export_collection.py -c MyDocs -o /path/to/backups/

  # Export without including original PDFs (ChromaDB data only)
  python export_collection.py -c MyDocs --no-pdfs

  # With custom data directory
  python export_collection.py -d /Users/brain/work/chroma/ -c MyDocs -o backup.zip
        """
    )

    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", required=True,
                       help="Name of the collection to export")
    parser.add_argument("-o", "--output",
                       help="Output path (file or directory). Default: <collection_name>.zip in current directory")
    parser.add_argument("--no-pdfs", action="store_true",
                       help="Don't include original PDF files in the archive")

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

    exit_code = export_collection(
        data_dir,
        args.collection_name,
        args.output,
        include_pdfs=not args.no_pdfs
    )
    sys.exit(exit_code)
