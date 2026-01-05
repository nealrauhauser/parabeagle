#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
from pathlib import Path

from common import get_active_directory, Logger

# Global logger
_logger = None


def remove_pdf_from_collection(data_dir, collection_name, pdf_path, dry_run=False, logger=None):
    """Remove all documents from a PDF file from a Chroma collection."""
    def log(msg):
        if logger:
            logger.log(msg)
        else:
            print(msg)

    try:
        client = chromadb.PersistentClient(path=data_dir)

        # Get the collection
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            log(f"Collection '{collection_name}' does not exist.")
            return 1

        if collection.count() == 0:
            log(f"Collection '{collection_name}' is empty.")
            return 0

        # Get absolute path for consistent matching
        pdf_path = os.path.abspath(pdf_path)
        pdf_name = Path(pdf_path).name

        log(f"Looking for documents from: {pdf_path}")

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
            log(f"No chunks found from {pdf_name} in collection '{collection_name}'")
            return 0

        log(f"Found {len(matching_ids)} chunks from {pdf_name}")

        if dry_run:
            log("DRY RUN - would delete:")
            for doc_id in matching_ids:
                log(f"  - {doc_id}")
            log(f"Total: {len(matching_ids)} chunks from 1 file")
            return 0

        # Delete the matching documents
        collection.delete(ids=matching_ids)

        log(f"Successfully deleted {len(matching_ids)} chunks from 1 file in collection '{collection_name}'")
        return 0

    except Exception as e:
        log(f"Error removing PDF from collection: {e}")
        return 1

if __name__ == "__main__":
    import argparse

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

    # Use context manager for logger
    log_path = os.path.join(os.getcwd(), "parabeagle.log")
    with Logger(log_path) as logger:
        exit_code = remove_pdf_from_collection(
            data_dir,
            args.collection_name,
            args.pdf_path,
            dry_run=args.dry_run,
            logger=logger
        )
    sys.exit(exit_code)