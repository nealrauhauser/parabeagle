#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

# Global log file handle
_log_file = None

def log_and_print(message):
    """Print to console and write to log file."""
    print(message)
    if _log_file:
        _log_file.write(f"{message}\n")
        _log_file.flush()

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

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using pypdf."""
    try:
        import pypdf
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        print("pypdf not installed. Install with: pip install pypdf")
        return None
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def remove_pdf_from_collection(data_dir, collection_name, pdf_path, dry_run=False):
    """Remove all documents from a PDF file from a Chroma collection."""
    try:
        client = chromadb.PersistentClient(path=data_dir)

        # Get the collection
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            log_and_print(f"Collection '{collection_name}' does not exist.")
            return 1

        if collection.count() == 0:
            log_and_print(f"Collection '{collection_name}' is empty.")
            return 0

        # Get absolute path for consistent matching
        pdf_path = os.path.abspath(pdf_path)
        pdf_name = Path(pdf_path).name

        log_and_print(f"Looking for documents from: {pdf_path}")

        # Get all documents with metadata to find matches
        all_docs = collection.get(include=['metadatas'])
        metadatas = all_docs['metadatas']
        ids = all_docs['ids']

        # Find IDs that match this PDF
        matching_ids = []
        for i, metadata in enumerate(metadatas):
            if metadata and 'source' in metadata:
                doc_source = os.path.abspath(metadata['source'])
                if doc_source == pdf_path:
                    matching_ids.append(ids[i])

        if not matching_ids:
            log_and_print(f"No chunks found from {pdf_name} in collection '{collection_name}'")
            return 0

        log_and_print(f"Found {len(matching_ids)} chunks from {pdf_name}")

        if dry_run:
            log_and_print("DRY RUN - would delete:")
            for doc_id in matching_ids:
                log_and_print(f"  - {doc_id}")
            log_and_print(f"Total: {len(matching_ids)} chunks from 1 file")
            return 0

        # Delete the matching documents
        collection.delete(ids=matching_ids)

        log_and_print(f"Successfully deleted {len(matching_ids)} chunks from 1 file in collection '{collection_name}'")
        return 0

    except Exception as e:
        log_and_print(f"Error removing PDF from collection: {e}")
        return 1

if __name__ == "__main__":
    import argparse

    # Open log file in append mode
    global _log_file
    log_path = os.path.join(os.getcwd(), "parabeagle.log")
    _log_file = open(log_path, "a", encoding="utf-8")

    try:
        parser = argparse.ArgumentParser(
            description="Remove all documents from a PDF file from a Chroma collection",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Remove documents from a PDF
  python remove_pdf_from_collection.py -c MyDocs document.pdf

  # Dry run to see what would be deleted
  python remove_pdf_from_collection.py -c MyDocs document.pdf --dry-run

  # With custom data directory
  python remove_pdf_from_collection.py -d /Users/brain/work/chroma/ -c MyDocs document.pdf
        """
        )

        parser.add_argument("-d", "--data-dir", "--data-directory",
                           default=os.getenv('CHROMADIR'),
                           help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
        parser.add_argument("-c", "--collection-name", required=True,
                           help="Name of the collection to remove documents from")
        parser.add_argument("pdf_path", help="PDF file to remove from collection")
        parser.add_argument("--dry-run", action="store_true",
                           help="Show what would be deleted without actually deleting")

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

        if not os.path.exists(args.pdf_path):
            print(f"Error: PDF file {args.pdf_path} does not exist")
            sys.exit(1)

        if not args.pdf_path.lower().endswith('.pdf'):
            print(f"Error: File {args.pdf_path} is not a PDF")
            sys.exit(1)

        exit_code = remove_pdf_from_collection(
            data_dir,
            args.collection_name,
            args.pdf_path,
            dry_run=args.dry_run
        )
        sys.exit(exit_code)
    finally:
        # Close log file
        if _log_file:
            _log_file.close()