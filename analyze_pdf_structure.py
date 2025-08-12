#!/Users/brain/work/gits/chroma-mac/.venv/bin/python

# Smart dependency detection and helpful error messages
def check_dependencies():
    """Check if required dependencies are available and provide helpful error messages."""
    missing_deps = []
    
    try:
        import pypdf
    except ImportError:
        missing_deps.append("pypdf")
    
    if missing_deps:
        print("❌ Missing required dependencies:", ", ".join(missing_deps))
        print("\n🔧 To fix this:")
        
        # Check if we're in a venv
        import sys
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if in_venv:
            print("   You're in a virtual environment. Install with:")
            print(f"   pip install {' '.join(missing_deps)}")
        else:
            print("   Install system-wide with:")
            print(f"   pip install {' '.join(missing_deps)}")
            print("   Or run from within an activated virtual environment that has these packages.")
        
        print(f"\n   Currently using Python: {sys.executable}")
        sys.exit(1)

# Check dependencies before importing anything else
check_dependencies()

import sys
import os
from pathlib import Path
import re
import statistics

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
    """
    Smart paragraph detection for prose/novels using multiple heuristics.
    """
    if not text:
        return []
    
    lines = text.split('\n')
    paragraphs = []
    current_paragraph = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Skip completely empty lines
        if not line_stripped:
            continue
            
        # Detect paragraph breaks using multiple signals
        is_paragraph_break = False
        
        # Signal 1: Line starts with capital letter and previous line ended with sentence
        if (current_paragraph and 
            line_stripped and line_stripped[0].isupper() and 
            current_paragraph[-1].strip().endswith(('.', '!', '?', '"', "'"))):
            is_paragraph_break = True
            
        # Signal 2: Line starts with quotation mark (dialogue)
        if line_stripped.startswith(('"', "'", '"', '"')):
            is_paragraph_break = True
            
        # Signal 3: Line is indented (common in novels)
        if line.startswith(('    ', '\t')) and current_paragraph:
            is_paragraph_break = True
            
        # Signal 4: Dramatic line break patterns
        if (current_paragraph and 
            len(line_stripped) < 50 and 
            current_paragraph[-1].strip().endswith(('.', '!', '?'))):
            # Short line after sentence-ending might be paragraph break
            is_paragraph_break = True
            
        # Signal 5: All caps words (could be emphasis or scene breaks)
        caps_words = [word for word in line_stripped.split() if word.isupper() and len(word) > 2]
        if len(caps_words) > 2 and len(line_stripped) < 100:
            is_paragraph_break = True
            
        if is_paragraph_break and current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = [line_stripped]
        else:
            current_paragraph.append(line_stripped)
    
    # Add final paragraph
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    return paragraphs

def sentence_based_paragraph_detection(text):
    """
    Infer paragraph breaks by analyzing sentence patterns and flow.
    """
    if not text:
        return []
    
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) < 2:
        return [text]
    
    paragraphs = []
    current_paragraph = []
    
    for i, sentence in enumerate(sentences):
        current_paragraph.append(sentence)
        
        # Look for paragraph break signals
        should_break = False
        
        # Signal 1: Sentence followed by quoted dialogue
        if (i + 1 < len(sentences) and 
            sentences[i + 1].strip().startswith(('"', "'", '"', '"'))):
            should_break = True
            
        # Signal 2: Topic shift detection (simple lexical overlap)
        if i + 1 < len(sentences) and len(current_paragraph) > 2:
            overlap = calculate_sentence_overlap(sentence, sentences[i + 1])
            if overlap < 0.1:  # Very low overlap suggests topic shift
                should_break = True
                
        # Signal 3: Paragraph length heuristic
        current_length = sum(len(s) for s in current_paragraph)
        if current_length > 800:  # Force break after reasonable length
            should_break = True
            
        # Signal 4: Sentence starts with paragraph-starting words
        next_sentence = sentences[i + 1] if i + 1 < len(sentences) else ""
        paragraph_starters = ['However', 'Meanwhile', 'Later', 'Then', 'Suddenly', 'But', 'And then', 'Now', 'The next']
        if any(next_sentence.startswith(starter) for starter in paragraph_starters):
            should_break = True
        
        if should_break:
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    
    # Add final paragraph
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    return paragraphs

def calculate_sentence_overlap(sent1, sent2):
    """Calculate lexical overlap between two sentences."""
    words1 = set(sent1.lower().split())
    words2 = set(sent2.lower().split())
    
    if not words1 or not words2:
        return 0.0
        
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def score_paragraph_detection(paragraphs):
    """
    Score the quality of paragraph detection based on multiple factors.
    Higher score = better paragraph detection.
    """
    if not paragraphs:
        return 0.0
    
    # Filter out very short paragraphs
    meaningful_paragraphs = [p for p in paragraphs if len(p.strip()) > 50]
    
    if not meaningful_paragraphs:
        return 0.0
    
    # Factor 1: Number of paragraphs (more is generally better for prose)
    paragraph_count_score = min(len(meaningful_paragraphs) / 10.0, 1.0)
    
    # Factor 2: Paragraph length distribution (prefer reasonable variance)
    lengths = [len(p) for p in meaningful_paragraphs]
    mean_length = sum(lengths) / len(lengths)
    
    # Ideal paragraph length for prose: 200-800 characters
    length_score = 0.0
    for length in lengths:
        if 200 <= length <= 800:
            length_score += 1.0
        elif 100 <= length <= 1200:  # Acceptable range
            length_score += 0.5
        else:
            length_score += 0.1
    length_score /= len(lengths)
    
    # Factor 3: Variance in paragraph lengths (some variation is good)
    if len(lengths) > 1:
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        variance_score = min(std_dev / mean_length, 1.0) if mean_length > 0 else 0.0
    else:
        variance_score = 0.0
    
    # Combine scores
    total_score = (paragraph_count_score * 0.4 + 
                   length_score * 0.4 + 
                   variance_score * 0.2)
    
    return total_score

def analyze_paragraph_structure(text):
    """Analyze paragraph structure in the text using multiple detection methods."""
    if not text:
        return {}
    
    # Method 1: Try double newlines first
    paragraphs_method1 = re.split(r'\n\s*\n', text)
    
    # Method 2: Smart paragraph detection for novels/prose
    paragraphs_method2 = smart_paragraph_detection(text)
    
    # Method 3: Sentence-based paragraph inference
    paragraphs_method3 = sentence_based_paragraph_detection(text)
    
    # Choose the best method based on results
    all_methods = [
        ("Double newlines", paragraphs_method1),
        ("Smart detection", paragraphs_method2), 
        ("Sentence-based", paragraphs_method3)
    ]
    
    # Score each method and pick the best one
    best_method = None
    best_score = -1
    best_paragraphs = []
    
    for method_name, paragraphs in all_methods:
        score = score_paragraph_detection(paragraphs)
        print(f"   {method_name}: {len(paragraphs)} paragraphs (score: {score:.2f})")
        if score > best_score:
            best_score = score
            best_method = method_name
            best_paragraphs = paragraphs
    
    print(f"   → Using {best_method} method")
    
    # Clean up paragraphs and filter out very short ones (likely formatting artifacts)
    clean_paragraphs = []
    for para in best_paragraphs:
        para = para.strip()
        # Filter out very short "paragraphs" that are likely headers, page numbers, etc.
        if len(para) > 20:  # Minimum 20 characters to be considered a real paragraph
            # Clean up excessive whitespace
            para = re.sub(r'\s+', ' ', para)
            clean_paragraphs.append(para)
    
    if not clean_paragraphs:
        return {
            "total_paragraphs": 0,
            "paragraph_lengths": [],
            "statistics": {}
        }
    
    # Calculate lengths
    paragraph_lengths = [len(para) for para in clean_paragraphs]
    
    # Calculate statistics
    stats = {
        "count": len(paragraph_lengths),
        "total_characters": sum(paragraph_lengths),
        "min_length": min(paragraph_lengths),
        "max_length": max(paragraph_lengths),
        "mean_length": statistics.mean(paragraph_lengths),
        "median_length": statistics.median(paragraph_lengths),
        "std_dev": statistics.stdev(paragraph_lengths) if len(paragraph_lengths) > 1 else 0
    }
    
    # Calculate percentiles
    sorted_lengths = sorted(paragraph_lengths)
    stats["percentile_25"] = sorted_lengths[len(sorted_lengths) // 4] if sorted_lengths else 0
    stats["percentile_75"] = sorted_lengths[3 * len(sorted_lengths) // 4] if sorted_lengths else 0
    stats["percentile_90"] = sorted_lengths[9 * len(sorted_lengths) // 10] if sorted_lengths else 0
    
    return {
        "total_paragraphs": len(clean_paragraphs),
        "paragraph_lengths": paragraph_lengths,
        "paragraphs": clean_paragraphs,
        "statistics": stats
    }

def analyze_sentence_structure(text):
    """Analyze sentence structure in the text."""
    if not text:
        return {}
    
    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Clean up sentences
    clean_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        # Filter out very short sentences (likely artifacts)
        if len(sentence) > 10:
            # Clean up excessive whitespace
            sentence = re.sub(r'\s+', ' ', sentence)
            clean_sentences.append(sentence)
    
    if not clean_sentences:
        return {
            "total_sentences": 0,
            "sentence_lengths": [],
            "statistics": {}
        }
    
    sentence_lengths = [len(sent) for sent in clean_sentences]
    
    stats = {
        "count": len(sentence_lengths),
        "total_characters": sum(sentence_lengths),
        "min_length": min(sentence_lengths),
        "max_length": max(sentence_lengths),
        "mean_length": statistics.mean(sentence_lengths),
        "median_length": statistics.median(sentence_lengths),
        "std_dev": statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
    }
    
    return {
        "total_sentences": len(clean_sentences),
        "sentence_lengths": sentence_lengths,
        "sentences": clean_sentences,
        "statistics": stats
    }

def detect_document_sections(text):
    """Detect potential document sections and their characteristics."""
    if not text:
        return {}
    
    lines = text.split('\n')
    sections = {
        "headers": [],
        "lists": [],
        "references": [],
        "captions": []
    }
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Detect headers (various patterns)
        if is_potential_header(line_stripped, i, lines):
            sections["headers"].append({
                "text": line_stripped,
                "length": len(line_stripped),
                "line_number": i
            })
        
        # Detect list items
        elif is_list_item(line_stripped):
            sections["lists"].append({
                "text": line_stripped,
                "length": len(line_stripped),
                "line_number": i
            })
        
        # Detect references
        elif is_reference_line(line_stripped):
            sections["references"].append({
                "text": line_stripped,
                "length": len(line_stripped),
                "line_number": i
            })
        
        # Detect captions
        elif is_caption_line(line_stripped):
            sections["captions"].append({
                "text": line_stripped,
                "length": len(line_stripped),
                "line_number": i
            })
    
    return sections

def is_potential_header(line, line_num, all_lines):
    """Detect potential headers."""
    if len(line) < 5 or len(line) > 200:
        return False
    
    # All caps and relatively short
    if line.isupper() and len(line) < 100:
        return True
    
    # Numbered sections
    if re.match(r'^[0-9IVX]+\.?\s+[A-Z]', line):
        return True
    
    # Title case and short
    if line.istitle() and len(line) < 80 and len(line.split()) <= 12:
        return True
    
    return False

def is_list_item(line):
    """Detect list items."""
    return bool(
        re.match(r'^[•\-\*]\s+', line) or
        re.match(r'^[0-9]+\.\s+', line) or
        re.match(r'^[a-zA-Z]\.\s+', line)
    )

def is_reference_line(line):
    """Detect reference lines."""
    line_lower = line.lower()
    return bool(
        re.match(r'^\[[0-9]+\]', line) or
        (re.match(r'^[0-9]+\.', line) and len(line) > 50) or
        any(word in line_lower for word in ["doi:", "arxiv:", "http://", "https://"])
    )

def is_caption_line(line):
    """Detect figure/table captions."""
    line_lower = line.lower()
    return bool(
        re.match(r'^(table|figure|fig\.?)\s*[0-9]', line_lower) or
        "caption:" in line_lower
    )

def print_analysis_report(pdf_path, analysis, show_examples=False):
    """Print a comprehensive analysis report."""
    print(f"\n{'='*80}")
    print(f"PDF STRUCTURE ANALYSIS: {Path(pdf_path).name}")
    print(f"{'='*80}")
    
    # Overall document stats
    para_stats = analysis.get("paragraph_analysis", {}).get("statistics", {})
    sent_stats = analysis.get("sentence_analysis", {}).get("statistics", {})
    
    print(f"\n📄 DOCUMENT OVERVIEW")
    print(f"   Total characters: {para_stats.get('total_characters', 0):,}")
    print(f"   Total paragraphs: {para_stats.get('count', 0):,}")
    print(f"   Total sentences:  {sent_stats.get('count', 0):,}")
    
    # Paragraph analysis
    if para_stats:
        print(f"\n📝 PARAGRAPH ANALYSIS")
        print(f"   Average length:   {para_stats['mean_length']:.0f} characters")
        print(f"   Median length:    {para_stats['median_length']:.0f} characters")
        print(f"   Standard dev:     {para_stats['std_dev']:.0f} characters")
        print(f"   Min length:       {para_stats['min_length']} characters")
        print(f"   Max length:       {para_stats['max_length']} characters")
        print(f"   25th percentile:  {para_stats['percentile_25']} characters")
        print(f"   75th percentile:  {para_stats['percentile_75']} characters")
        print(f"   90th percentile:  {para_stats['percentile_90']} characters")
    
    # Sentence analysis
    if sent_stats:
        print(f"\n💬 SENTENCE ANALYSIS")
        print(f"   Average length:   {sent_stats['mean_length']:.0f} characters")
        print(f"   Median length:    {sent_stats['median_length']:.0f} characters")
        print(f"   Standard dev:     {sent_stats['std_dev']:.0f} characters")
        print(f"   Min length:       {sent_stats['min_length']} characters")
        print(f"   Max length:       {sent_stats['max_length']} characters")
    
    # Document structure
    sections = analysis.get("document_sections", {})
    if sections:
        print(f"\n🏗️  DOCUMENT STRUCTURE")
        print(f"   Headers detected:    {len(sections.get('headers', []))}")
        print(f"   List items:          {len(sections.get('lists', []))}")
        print(f"   References:          {len(sections.get('references', []))}")
        print(f"   Captions:            {len(sections.get('captions', []))}")
    
    # Chunking recommendations
    print(f"\n🎯 CHUNKING RECOMMENDATIONS")
    if para_stats:
        avg_para = para_stats['mean_length']
        p75_para = para_stats['percentile_75']
        p90_para = para_stats['percentile_90']
        
        # Recommend chunk sizes based on paragraph distribution
        if avg_para < 500:
            recommended_chunk = max(1500, p75_para * 3)
            print(f"   Document has short paragraphs (avg: {avg_para:.0f} chars)")
        elif avg_para < 1000:
            recommended_chunk = max(2000, p75_para * 2)
            print(f"   Document has medium paragraphs (avg: {avg_para:.0f} chars)")
        else:
            recommended_chunk = max(2500, p75_para * 1.5)
            print(f"   Document has long paragraphs (avg: {avg_para:.0f} chars)")
        
        print(f"   Recommended chunk size: {recommended_chunk:.0f} characters")
        print(f"   Alternative (conservative): {p90_para * 1.2:.0f} characters")
        print(f"   Alternative (aggressive):   {avg_para * 4:.0f} characters")
    
    # Show examples if requested
    if show_examples:
        paragraphs = analysis.get("paragraph_analysis", {}).get("paragraphs", [])
        if paragraphs:
            print(f"\n📋 PARAGRAPH EXAMPLES")
            
            # Show shortest paragraph
            shortest_para = min(paragraphs, key=len)
            print(f"\n   Shortest paragraph ({len(shortest_para)} chars):")
            print(f"   \"{shortest_para[:200]}{'...' if len(shortest_para) > 200 else ''}\"")
            
            # Show median length paragraph
            sorted_paras = sorted(paragraphs, key=len)
            median_para = sorted_paras[len(sorted_paras) // 2]
            print(f"\n   Median paragraph ({len(median_para)} chars):")
            print(f"   \"{median_para[:200]}{'...' if len(median_para) > 200 else ''}\"")
            
            # Show longest paragraph
            longest_para = max(paragraphs, key=len)
            print(f"\n   Longest paragraph ({len(longest_para)} chars):")
            print(f"   \"{longest_para[:200]}{'...' if len(longest_para) > 200 else ''}\"")

def analyze_multiple_pdfs(pdf_paths, show_examples=False):
    """Analyze multiple PDFs and show aggregate statistics."""
    all_para_lengths = []
    all_sent_lengths = []
    successful_analyses = []
    
    for pdf_path in pdf_paths:
        print(f"Processing {Path(pdf_path).name}...")
        
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  ⚠️  Could not extract text from {pdf_path}")
            continue
        
        analysis = {
            "pdf_path": pdf_path,
            "paragraph_analysis": analyze_paragraph_structure(text),
            "sentence_analysis": analyze_sentence_structure(text),
            "document_sections": detect_document_sections(text)
        }
        
        successful_analyses.append(analysis)
        
        # Collect lengths for aggregate analysis
        para_lengths = analysis["paragraph_analysis"].get("paragraph_lengths", [])
        sent_lengths = analysis["sentence_analysis"].get("sentence_lengths", [])
        
        all_para_lengths.extend(para_lengths)
        all_sent_lengths.extend(sent_lengths)
        
        # Print individual report
        print_analysis_report(pdf_path, analysis, show_examples)
    
    # Print aggregate analysis if multiple files
    if len(successful_analyses) > 1:
        print(f"\n{'='*80}")
        print(f"AGGREGATE ANALYSIS ({len(successful_analyses)} PDFs)")
        print(f"{'='*80}")
        
        if all_para_lengths:
            avg_para = statistics.mean(all_para_lengths)
            median_para = statistics.median(all_para_lengths)
            std_para = statistics.stdev(all_para_lengths) if len(all_para_lengths) > 1 else 0
            
            print(f"\n📊 COMBINED PARAGRAPH STATISTICS")
            print(f"   Total paragraphs: {len(all_para_lengths):,}")
            print(f"   Average length:   {avg_para:.0f} characters")
            print(f"   Median length:    {median_para:.0f} characters")
            print(f"   Standard dev:     {std_para:.0f} characters")
            print(f"   Min length:       {min(all_para_lengths)} characters")
            print(f"   Max length:       {max(all_para_lengths)} characters")
            
            # Overall chunking recommendation
            print(f"\n🎯 OVERALL CHUNKING RECOMMENDATION")
            recommended = max(2000, avg_para * 3)
            print(f"   For this document set: {recommended:.0f} characters")
            print(f"   Conservative approach: {median_para * 4:.0f} characters")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze PDF paragraph structure and provide chunking recommendations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_pdf_structure.py document.pdf
  python analyze_pdf_structure.py doc1.pdf doc2.pdf doc3.pdf --examples
  python analyze_pdf_structure.py /path/to/pdf/directory/ --examples
        """
    )
    
    parser.add_argument("pdf_inputs", nargs="+", 
                       help="PDF files or directories containing PDFs to analyze")
    parser.add_argument("--examples", "--show-examples", action="store_true",
                       help="Show example paragraphs (shortest, median, longest)")
    
    args = parser.parse_args()
    
    # Collect all PDF paths
    pdf_paths = []
    for input_path in args.pdf_inputs:
        if os.path.isfile(input_path):
            if input_path.lower().endswith('.pdf'):
                pdf_paths.append(input_path)
            else:
                print(f"Warning: {input_path} is not a PDF file, skipping.")
        elif os.path.isdir(input_path):
            # Find all PDF files in directory
            for file in Path(input_path).glob("*.pdf"):
                pdf_paths.append(str(file))
            for file in Path(input_path).glob("*.PDF"):
                pdf_paths.append(str(file))
        else:
            print(f"Warning: {input_path} is neither a file nor a directory, skipping.")
    
    if not pdf_paths:
        print("No PDF files found to analyze.")
        sys.exit(1)
    
    print(f"Found {len(pdf_paths)} PDF file(s) to analyze")
    
    # Analyze all PDFs
    analyze_multiple_pdfs(pdf_paths, args.examples)