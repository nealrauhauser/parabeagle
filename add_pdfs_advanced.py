#!/Users/brain/work/gits/chroma-mac/.venv/bin/python

import chromadb
import sys
import os
import uuid
from pathlib import Path
import re

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

def production_semantic_chunk_text(text, max_chunk_size=3000, min_chunk_size=100):
    """
    Production-grade semantic chunking with improved paragraph detection.
    Now includes smart paragraph detection for better handling of novels/prose.
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

def experimental_semantic_chunk_text(text, max_chunk_size=3000, min_chunk_size=100):
    """
    Experimental semantic chunking with advanced document structure awareness.
    
    EXPERIMENTAL FEATURES:
    - Section header detection and preservation
    - List structure awareness (bullets, numbered)
    - Table and figure caption grouping
    - Citation and reference clustering
    - Semantic similarity scoring between paragraphs
    - Dynamic chunk size adjustment based on content type
    
    WARNING: These are untested theories that may not work reliably!
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    # Phase 1: Advanced structure detection
    sections = detect_document_structure(text)
    
    chunks = []
    
    for section in sections:
        section_chunks = process_section_experimentally(
            section, max_chunk_size, min_chunk_size
        )
        chunks.extend(section_chunks)
    
    # Phase 2: Experimental post-processing
    chunks = apply_semantic_coherence_scoring(chunks, max_chunk_size)
    chunks = merge_orphaned_fragments(chunks, min_chunk_size, max_chunk_size)
    chunks = balance_chunk_sizes_dynamically(chunks, max_chunk_size)
    
    return [chunk for chunk in chunks if len(chunk.strip()) >= min_chunk_size]

def detect_document_structure(text):
    """
    EXPERIMENTAL: Detect document structure including headers, lists, tables, etc.
    """
    lines = text.split('\n')
    sections = []
    current_section = {"type": "text", "content": "", "metadata": {}}
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Detect section headers (various patterns)
        if is_section_header(line_stripped, i, lines):
            # Save current section if not empty
            if current_section["content"].strip():
                sections.append(current_section)
            
            # Start new section
            current_section = {
                "type": "header_section",
                "content": line_stripped + "\n",
                "metadata": {"header_level": detect_header_level(line_stripped)}
            }
        
        # Detect list items
        elif is_list_item(line_stripped):
            if current_section["type"] != "list":
                # Save previous section
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new list section
                current_section = {
                    "type": "list",
                    "content": line + "\n",
                    "metadata": {"list_type": detect_list_type(line_stripped)}
                }
            else:
                current_section["content"] += line + "\n"
        
        # Detect table or figure captions
        elif is_table_or_figure_caption(line_stripped):
            if current_section["content"].strip():
                sections.append(current_section)
            
            current_section = {
                "type": "caption",
                "content": line + "\n",
                "metadata": {"caption_type": "table" if "table" in line_stripped.lower() else "figure"}
            }
        
        # Detect citations/references section
        elif is_reference_line(line_stripped):
            if current_section["type"] != "references":
                if current_section["content"].strip():
                    sections.append(current_section)
                
                current_section = {
                    "type": "references",
                    "content": line + "\n",
                    "metadata": {}
                }
            else:
                current_section["content"] += line + "\n"
        
        # Regular text
        else:
            if current_section["type"] not in ["text", "header_section"]:
                # End special section, start text section
                if current_section["content"].strip():
                    sections.append(current_section)
                
                current_section = {
                    "type": "text",
                    "content": line + "\n",
                    "metadata": {}
                }
            else:
                current_section["content"] += line + "\n"
    
    # Add final section
    if current_section["content"].strip():
        sections.append(current_section)
    
    return sections

def is_section_header(line, line_num, all_lines):
    """EXPERIMENTAL: Detect if a line is a section header."""
    if not line:
        return False
    
    # Pattern 1: All caps short line
    if line.isupper() and len(line) < 100 and len(line) > 3:
        return True
    
    # Pattern 2: Numbered sections (1., 1.1, I., etc.)
    if re.match(r'^[0-9IVX]+\.?\s+[A-Z]', line):
        return True
    
    # Pattern 3: Short line followed by empty line
    if len(line) < 80 and line_num < len(all_lines) - 1:
        next_line = all_lines[line_num + 1].strip() if line_num + 1 < len(all_lines) else ""
        if not next_line:
            return True
    
    # Pattern 4: Title case short line
    if line.istitle() and len(line) < 100 and len(line.split()) <= 10:
        return True
    
    return False

def detect_header_level(line):
    """EXPERIMENTAL: Detect header hierarchy level."""
    # Count leading numbers/roman numerals
    if re.match(r'^[0-9]+\.', line):
        return 1
    elif re.match(r'^[0-9]+\.[0-9]+', line):
        return 2
    elif re.match(r'^[IVX]+\.', line):
        return 1
    elif line.isupper():
        return 1
    else:
        return 2

def is_list_item(line):
    """EXPERIMENTAL: Detect list items."""
    if not line:
        return False
    
    # Bullet points
    if re.match(r'^[•\-\*]\s+', line):
        return True
    
    # Numbered lists
    if re.match(r'^[0-9]+\.\s+', line):
        return True
    
    # Lettered lists
    if re.match(r'^[a-zA-Z]\.\s+', line):
        return True
    
    return False

def detect_list_type(line):
    """EXPERIMENTAL: Detect type of list."""
    if re.match(r'^[•\-\*]\s+', line):
        return "bullet"
    elif re.match(r'^[0-9]+\.\s+', line):
        return "numbered"
    elif re.match(r'^[a-zA-Z]\.\s+', line):
        return "lettered"
    return "unknown"

def is_table_or_figure_caption(line):
    """EXPERIMENTAL: Detect table/figure captions."""
    line_lower = line.lower()
    return (
        re.match(r'^(table|figure|fig\.?)\s*[0-9]', line_lower) or
        "caption:" in line_lower or
        line_lower.startswith("source:")
    )

def is_reference_line(line):
    """EXPERIMENTAL: Detect reference/citation lines."""
    line_lower = line.lower()
    return (
        re.match(r'^\[[0-9]+\]', line) or
        re.match(r'^[0-9]+\.', line) and len(line) > 50 or
        any(word in line_lower for word in ["doi:", "arxiv:", "http://", "https://"])
    )

def process_section_experimentally(section, max_chunk_size, min_chunk_size):
    """EXPERIMENTAL: Process different section types with specialized logic."""
    content = section["content"]
    section_type = section["type"]
    
    if section_type == "header_section":
        # Keep headers with following content
        return smart_header_chunking(content, max_chunk_size, min_chunk_size)
    
    elif section_type == "list":
        # Keep list items together when possible
        return smart_list_chunking(content, max_chunk_size, min_chunk_size)
    
    elif section_type == "references":
        # Chunk references by groups
        return smart_reference_chunking(content, max_chunk_size, min_chunk_size)
    
    elif section_type == "caption":
        # Keep captions as single units if possible
        if len(content) <= max_chunk_size:
            return [content]
        else:
            # Fall back to sentence chunking
            return production_semantic_chunk_text(content, max_chunk_size, min_chunk_size)
    
    else:
        # Regular text - use enhanced paragraph logic
        return enhanced_paragraph_chunking(content, max_chunk_size, min_chunk_size)

def smart_header_chunking(content, max_chunk_size, min_chunk_size):
    """EXPERIMENTAL: Intelligent header-aware chunking."""
    # Try to keep header with following paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    if not paragraphs:
        return [content] if content.strip() else []
    
    # Header is likely the first paragraph
    header = paragraphs[0]
    remaining = paragraphs[1:] if len(paragraphs) > 1 else []
    
    chunks = []
    current_chunk = header
    
    for para in remaining:
        if len(current_chunk) + len(para) + 2 <= max_chunk_size:
            current_chunk += "\n\n" + para
        else:
            chunks.append(current_chunk)
            current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def smart_list_chunking(content, max_chunk_size, min_chunk_size):
    """EXPERIMENTAL: Keep related list items together."""
    lines = content.split('\n')
    chunks = []
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_chunk_size:
            current_chunk += line + "\n" if current_chunk else line + "\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def smart_reference_chunking(content, max_chunk_size, min_chunk_size):
    """EXPERIMENTAL: Group references intelligently."""
    # Split by reference patterns
    refs = re.split(r'\n(?=\[[0-9]+\]|\n[0-9]+\.)', content)
    
    chunks = []
    current_chunk = ""
    
    for ref in refs:
        ref = ref.strip()
        if not ref:
            continue
            
        if len(current_chunk) + len(ref) + 2 <= max_chunk_size:
            current_chunk += "\n\n" + ref if current_chunk else ref
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = ref
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def enhanced_paragraph_chunking(content, max_chunk_size, min_chunk_size):
    """EXPERIMENTAL: Enhanced paragraph chunking with semantic awareness."""
    paragraphs = re.split(r'\n\s*\n', content)
    
    # Calculate semantic similarity between adjacent paragraphs (simplified)
    paragraph_scores = []
    for i in range(len(paragraphs) - 1):
        score = calculate_paragraph_similarity(paragraphs[i], paragraphs[i + 1])
        paragraph_scores.append(score)
    
    # Group paragraphs based on similarity scores
    chunks = []
    current_chunk = ""
    
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue
        
        # Decide whether to continue current chunk or start new one
        should_continue = True
        
        if current_chunk:
            # Check size constraint
            if len(current_chunk) + len(para) + 2 > max_chunk_size:
                should_continue = False
            # Check semantic similarity (if we have scores)
            elif i > 0 and i - 1 < len(paragraph_scores):
                if paragraph_scores[i - 1] < 0.3:  # Low similarity threshold
                    should_continue = False
        
        if should_continue:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)
            current_chunk = para
    
    # Add final chunk
    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk)
    
    return chunks

def calculate_paragraph_similarity(para1, para2):
    """EXPERIMENTAL: Simple lexical similarity between paragraphs."""
    words1 = set(para1.lower().split())
    words2 = set(para2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def apply_semantic_coherence_scoring(chunks, max_chunk_size):
    """EXPERIMENTAL: Rescore and potentially merge chunks based on semantic coherence."""
    if len(chunks) < 2:
        return chunks
    
    # Calculate coherence scores between adjacent chunks
    improved_chunks = []
    i = 0
    
    while i < len(chunks):
        current_chunk = chunks[i]
        
        # Try to merge with next chunk if coherent and size allows
        if i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            similarity = calculate_paragraph_similarity(current_chunk, next_chunk)
            combined_size = len(current_chunk) + len(next_chunk) + 2
            
            if similarity > 0.4 and combined_size <= max_chunk_size:
                # Merge chunks
                merged_chunk = current_chunk + "\n\n" + next_chunk
                improved_chunks.append(merged_chunk)
                i += 2  # Skip next chunk since we merged it
            else:
                improved_chunks.append(current_chunk)
                i += 1
        else:
            improved_chunks.append(current_chunk)
            i += 1
    
    return improved_chunks

def merge_orphaned_fragments(chunks, min_chunk_size, max_chunk_size):
    """EXPERIMENTAL: Merge very small chunks with neighbors."""
    if len(chunks) < 2:
        return chunks
    
    improved_chunks = []
    i = 0
    
    while i < len(chunks):
        chunk = chunks[i]
        
        # If chunk is too small, try to merge with previous or next
        if len(chunk) < min_chunk_size:
            merged = False
            
            # Try merging with previous chunk
            if improved_chunks and len(improved_chunks[-1]) + len(chunk) + 2 <= max_chunk_size:
                improved_chunks[-1] += "\n\n" + chunk
                merged = True
            
            # Try merging with next chunk
            elif i + 1 < len(chunks) and len(chunk) + len(chunks[i + 1]) + 2 <= max_chunk_size:
                merged_chunk = chunk + "\n\n" + chunks[i + 1]
                improved_chunks.append(merged_chunk)
                i += 1  # Skip next chunk
                merged = True
            
            if not merged:
                improved_chunks.append(chunk)
        else:
            improved_chunks.append(chunk)
        
        i += 1
    
    return improved_chunks

def balance_chunk_sizes_dynamically(chunks, max_chunk_size):
    """EXPERIMENTAL: Dynamically balance chunk sizes for optimal retrieval."""
    # Target size is 70% of max to allow for some variation
    target_size = int(max_chunk_size * 0.7)
    balanced_chunks = []
    
    for chunk in chunks:
        if len(chunk) <= target_size * 1.5:
            # Chunk is reasonably sized
            balanced_chunks.append(chunk)
        else:
            # Chunk is too large, try to split more intelligently
            # Split at sentence boundaries near the middle
            sentences = split_by_sentences(chunk)
            
            if len(sentences) > 1:
                mid_point = len(chunk) // 2
                best_split = 0
                best_distance = float('inf')
                current_pos = 0
                
                for i, sentence in enumerate(sentences):
                    current_pos += len(sentence)
                    distance = abs(current_pos - mid_point)
                    if distance < best_distance:
                        best_distance = distance
                        best_split = i
                
                # Split at best position
                first_part = ' '.join(sentences[:best_split + 1])
                second_part = ' '.join(sentences[best_split + 1:])
                
                balanced_chunks.append(first_part)
                if second_part:
                    balanced_chunks.append(second_part)
            else:
                # Can't split intelligently, keep as is
                balanced_chunks.append(chunk)
    
    return balanced_chunks

def split_by_sentences(text):
    """Split text into sentences using improved regex."""
    # Enhanced sentence splitting that handles more cases
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]

def add_pdfs_to_collection(data_dir, collection_name, pdf_paths, max_chunk_size=3000, min_chunk_size=100, embedding_function_name="default", use_experimental=False):
    """Add PDF documents to a Chroma collection with choice of chunking strategy."""
    try:
        client = chromadb.PersistentClient(path=data_dir)
        
        # Get or create the collection
        try:
            collection = client.get_collection(collection_name)
            print(f"Using existing collection '{collection_name}' with {collection.count()} documents.")
        except Exception:
            # Import embedding functions (same as MCP server)
            from chromadb.utils.embedding_functions import (
                DefaultEmbeddingFunction,
                SentenceTransformerEmbeddingFunction,
            )
            from chromadb.api.collection_configuration import CreateCollectionConfiguration
            
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
            
            if embedding_function_name not in mcp_known_embedding_functions:
                print(f"Error: Unknown embedding function '{embedding_function_name}'")
                print(f"Available options: {', '.join(mcp_known_embedding_functions.keys())}")
                return 1
            
            embedding_function = mcp_known_embedding_functions[embedding_function_name]
            configuration = CreateCollectionConfiguration(
                embedding_function=embedding_function()
            )
            collection = client.create_collection(name=collection_name, configuration=configuration)
            chunking_method = "EXPERIMENTAL" if use_experimental else "production"
            print(f"Created new collection '{collection_name}' with '{embedding_function_name}' embeddings ({chunking_method} chunking).")
        
        # Choose chunking function
        chunk_function = experimental_semantic_chunk_text if use_experimental else production_semantic_chunk_text
        chunk_type = "experimental" if use_experimental else "production"
        
        documents = []
        metadatas = []
        ids = []
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"Warning: File {pdf_path} does not exist, skipping.")
                continue
            
            if not pdf_path.lower().endswith('.pdf'):
                print(f"Warning: File {pdf_path} is not a PDF, skipping.")
                continue
            
            print(f"Processing {pdf_path} with {chunk_type} chunking...")
            text = extract_text_from_pdf(pdf_path)
            
            if not text:
                print(f"Warning: No text extracted from {pdf_path}, skipping.")
                continue
            
            # Use selected chunking strategy
            chunks = chunk_function(text, max_chunk_size, min_chunk_size)
            
            pdf_name = Path(pdf_path).stem
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": pdf_path,
                    "filename": Path(pdf_path).name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_type": chunk_type,
                    "char_count": len(chunk)
                })
                ids.append(f"{pdf_name}_{chunk_type}_chunk_{i}_{str(uuid.uuid4())[:8]}")
            
            print(f"  Split into {len(chunks)} {chunk_type} chunks (avg: {sum(len(c) for c in chunks) // len(chunks)} chars)")
        
        if not documents:
            print("No documents to add.")
            return 1
        
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
            print(f"  Added batch {i//batch_size + 1}: {total_added}/{len(documents)} chunks")
        
        print(f"Successfully added {len(documents)} {chunk_type} chunks from {len(pdf_paths)} PDFs to collection '{collection_name}'")
        print(f"Collection now has {collection.count()} total documents")
        return 0
        
    except Exception as e:
        print(f"Error adding PDFs to collection: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Add PDFs to a Chroma collection with production or experimental chunking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Production chunking (recommended)
  python add_pdfs_advanced.py -c MyDocs document.pdf
  
  # Experimental chunking (untested theories)
  python add_pdfs_advanced.py -c MyDocs document.pdf --experimental
  
  # With specific data directory and experimental features
  python add_pdfs_advanced.py -d /Users/brain/work/chroma/ -c MyDocs document.pdf --experimental
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
    parser.add_argument("--embedding-function", 
                       choices=["default", "mpnet-768", "bert-768", "minilm-384"],
                       default="default",
                       help="Embedding function to use: default (384-dim), mpnet-768 (768-dim best quality), bert-768 (768-dim fast), minilm-384 (384-dim explicit)")
    parser.add_argument("--experimental", action="store_true",
                       help="Use experimental advanced chunking (WARNING: untested theories!)")
    
    args = parser.parse_args()
    
    if not args.data_dir:
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
    
    chunking_mode = "EXPERIMENTAL" if args.experimental else "production"
    print(f"Using embedding function: {args.embedding_function}")
    print(f"Chunking strategy: {chunking_mode}")
    
    if args.experimental:
        print("⚠️  WARNING: Using experimental chunking with untested theories!")
        print("   Features: section headers, lists, captions, semantic scoring, dynamic balancing")
    
    data_dir = args.data_dir
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
    
    print(f"Found {len(pdf_paths)} PDF file(s) to process:")
    for pdf_path in pdf_paths[:5]:  # Show first 5
        print(f"  - {pdf_path}")
    if len(pdf_paths) > 5:
        print(f"  ... and {len(pdf_paths) - 5} more")
    
    exit_code = add_pdfs_to_collection(
        data_dir, 
        collection_name, 
        pdf_paths, 
        max_chunk_size=args.max_chunk_size,
        min_chunk_size=args.min_chunk_size,
        embedding_function_name=args.embedding_function,
        use_experimental=args.experimental
    )
    sys.exit(exit_code)