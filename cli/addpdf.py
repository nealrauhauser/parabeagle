#!/Users/brain/work/gits/parabeagle/.venv/bin/python

import chromadb
import sys
import os
import uuid
from pathlib import Path
import re

from common import (
    get_active_directory,
    calculate_sha256,
    extract_text_from_pdf,
    Logger,
)

# Global logger
_logger = None


def smart_paragraph_detection(text):
    """Smart paragraph detection using multiple heuristics."""
    if not text:
        return []
    
    lines = text.split('\n')
    paragraphs = []
    current_paragraph = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if not line_stripped:
            continue
            
        is_paragraph_break = False
        
        # Signal 1: Line starts with capital and previous ended with sentence
        if (current_paragraph and 
            line_stripped and line_stripped[0].isupper() and 
            current_paragraph[-1].strip().endswith(('.', '!', '?', '"', "'"))):
            is_paragraph_break = True
            
        # Signal 2: Dialogue
        if line_stripped.startswith(('"', "'", '"', '"')):
            is_paragraph_break = True
            
        # Signal 3: Indentation
        if line.startswith(('    ', '\t')) and current_paragraph:
            is_paragraph_break = True
        
        if is_paragraph_break and current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = [line_stripped]
        else:
            current_paragraph.append(line_stripped)
    
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    return paragraphs

def semantic_chunk_text(text, max_chunk_size=3000, min_chunk_size=100):
    """
    Split text into semantic chunks based on paragraphs, sentences, and sections.
    Uses improved paragraph detection for better results with novels/prose.
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    
    # Use smart paragraph detection instead of simple double newlines
    paragraphs = smart_paragraph_detection(text)
    
    # Fall back to simple method if smart detection fails
    if len(paragraphs) <= 2:
        paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If adding this paragraph would exceed max size, finalize current chunk
        if current_chunk and len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            if len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                # Current chunk too small, try to split the large paragraph
                if len(paragraph) > max_chunk_size:
                    # Split large paragraph by sentences
                    sentences = split_by_sentences(paragraph)
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                            current_chunk += " " + sentence if current_chunk else sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                else:
                    current_chunk += "\n\n" + paragraph
        else:
            # Add paragraph to current chunk
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
    
    # Add final chunk
    if current_chunk and len(current_chunk.strip()) >= min_chunk_size:
        chunks.append(current_chunk.strip())
    
    # Handle case where we have very large paragraphs that need sentence-level splitting
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split by sentences and recombine
            sentences = split_by_sentences(chunk)
            current_subchunk = ""
            for sentence in sentences:
                if len(current_subchunk) + len(sentence) + 1 <= max_chunk_size:
                    current_subchunk += " " + sentence if current_subchunk else sentence
                else:
                    if current_subchunk:
                        final_chunks.append(current_subchunk.strip())
                    current_subchunk = sentence
            if current_subchunk:
                final_chunks.append(current_subchunk.strip())
    
    return [chunk for chunk in final_chunks if len(chunk.strip()) >= min_chunk_size]

def split_by_sentences(text):
    """Split text into sentences using simple regex."""
    # Split on sentence endings, but keep the punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def add_pdfs_to_collection(data_dir, collection_name, pdf_paths, max_chunk_size=3000, min_chunk_size=100, show_chunks=False, verbose=False, logger=None):
    """Add PDF documents to a Chroma collection using semantic chunking."""
    from common import get_embedding_function
    from chromadb.api.collection_configuration import CreateCollectionConfiguration
    import time

    def log(msg):
        if logger:
            logger.log(msg)
        else:
            print(msg)

    start_time = time.time()

    try:
        client = chromadb.PersistentClient(path=data_dir)

        # Get or create the collection
        try:
            collection = client.get_collection(collection_name)
            if verbose:
                log(f"Using existing collection '{collection_name}'")
        except Exception:
            # Use mpnet-768 embedding function from common
            embedding_function = get_embedding_function()
            configuration = CreateCollectionConfiguration(embedding_function=embedding_function)
            collection = client.create_collection(
                name=collection_name,
                configuration=configuration,
                metadata={'hnsw:space': 'cosine'}
            )
            if verbose:
                log(f"Created new collection '{collection_name}'")
        
        documents = []
        metadatas = []
        ids = []

        # Get existing hashes from collection to detect duplicates
        existing_hashes = set()
        if collection.count() > 0:
            all_docs = collection.get(include=['metadatas'])
            for metadata in all_docs['metadatas']:
                if metadata and 'sha256' in metadata:
                    existing_hashes.add(metadata['sha256'])

        for pdf_path in pdf_paths:
            # Always use absolute path
            pdf_path = os.path.abspath(pdf_path)

            if not os.path.exists(pdf_path):
                log(f"Warning: File {pdf_path} does not exist, skipping.")
                continue

            if not pdf_path.lower().endswith('.pdf'):
                log(f"Warning: File {pdf_path} is not a PDF, skipping.")
                continue

            # Calculate SHA256 hash of the PDF file
            pdf_hash = calculate_sha256(pdf_path)

            # Check if this hash already exists in the collection
            if pdf_hash in existing_hashes:
                if verbose:
                    log(f"dup: {pdf_path}")
                else:
                    log(pdf_path)
                continue

            text = extract_text_from_pdf(pdf_path)

            if not text:
                log(f"error: {pdf_path}")
                continue

            log(pdf_path)

            if verbose:
                log(f"  SHA256: {pdf_hash}")

            # Use semantic chunking
            chunks = semantic_chunk_text(text, max_chunk_size, min_chunk_size)

            pdf_name = Path(pdf_path).stem
            for i, chunk in enumerate(chunks):
                if show_chunks:
                    print(f"{'='*60}")
                    print(f"CHUNK {i+1}/{len(chunks)} from {Path(pdf_path).name}")
                    print(f"{'='*60}")
                    print(chunk)
                    print()

                documents.append(chunk)
                metadatas.append({
                    "source": pdf_path,
                    "filename": Path(pdf_path).name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_type": "semantic",
                    "char_count": len(chunk),
                    "sha256": pdf_hash
                })
                ids.append(f"{pdf_name}_semantic_chunk_{i}_{str(uuid.uuid4())[:8]}")

            if verbose:
                log(f"  Split into {len(chunks)} semantic chunks (avg: {sum(len(c) for c in chunks) // len(chunks)} chars)")

        if not documents:
            return 0

        # Add documents to collection in batches to avoid memory issues
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
            if verbose:
                log(f"  Added batch {i//batch_size + 1}: {total_added}/{len(documents)} chunks")

        elapsed_time = time.time() - start_time
        if verbose:
            log(f"Successfully added {len(documents)} chunks from {len(pdf_paths)} file(s) to collection '{collection_name}'")
            log(f"Execution time: {elapsed_time:.2f} seconds")
        return 0

    except Exception as e:
        log(f"Error adding PDFs to collection: {e}")
        return 1

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add PDFs to a Chroma collection using semantic chunking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python add_pdfs_semantic.py --collection-name MyDocs document.pdf
  python add_pdfs_semantic.py -d /Users/brain/work/chroma/ -c MyDocs document.pdf
  python add_pdfs_semantic.py -c MyDocs doc1.pdf doc2.pdf doc3.pdf
  python add_pdfs_semantic.py -c MyDocs /path/to/pdf/directory/
  python add_pdfs_semantic.py -c MyDocs document.pdf --max-chunk-size 2000
        """
    )

    parser.add_argument("-d", "--data-dir", "--data-directory",
                       default=os.getenv('CHROMADIR'),
                       help="Directory for Chroma database storage (default: CHROMADIR environment variable)")
    parser.add_argument("-c", "--collection-name", required=True,
                       help="Name of the collection to add documents to")
    parser.add_argument("pdf_inputs", nargs="+", help="PDF files or directories containing PDFs")
    parser.add_argument("--max-chunk-size", "--chunk-size", type=int, default=3000,
                       help="Maximum size of each chunk in characters (default: 3000)")
    parser.add_argument("--min-chunk-size", "--min-size", type=int, default=100,
                       help="Minimum size of each chunk in characters (default: 100)")
    parser.add_argument("--batch-size", type=int, default=100,
                       help="Number of chunks to process in each batch (default: 100)")

    parser.add_argument("--show-chunks", action="store_true",
                       help="Print each chunk as it's processed with separator lines")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed progress including chunk counts, batch progress, and execution time")

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

    # Validate chunk sizes
    if args.max_chunk_size < args.min_chunk_size:
        print("Error: max-chunk-size must be greater than min-chunk-size")
        sys.exit(1)

    if args.max_chunk_size < 50:
        print("Warning: Very small chunk size may result in poor semantic quality")
    elif args.max_chunk_size > 8000:
        print("Warning: Very large chunk size may cause performance issues and semantic dilution")

    collection_name = args.collection_name
    pdf_inputs = args.pdf_inputs

    # Collect all PDF paths
    pdf_paths = []
    for input_path in pdf_inputs:
        if os.path.isfile(input_path):
            pdf_paths.append(input_path)
        elif os.path.isdir(input_path):
            # Find all PDF files in directory
            for file in Path(input_path).glob("*.pdf"):
                pdf_paths.append(str(file))
            for file in Path(input_path).glob("*.PDF"):
                pdf_paths.append(str(file))
        else:
            print(f"Warning: {input_path} is neither a file nor a directory, skipping.")

    if not pdf_paths:
        print("No PDF files found to process.")
        sys.exit(1)

    # Use context manager for logger
    log_path = os.path.join(os.getcwd(), "parabeagle.log")
    with Logger(log_path) as logger:
        exit_code = add_pdfs_to_collection(
            data_dir,
            collection_name,
            pdf_paths,
            max_chunk_size=args.max_chunk_size,
            min_chunk_size=args.min_chunk_size,
            show_chunks=args.show_chunks,
            verbose=args.verbose,
            logger=logger
        )
    sys.exit(exit_code)