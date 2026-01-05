# CLI Tools Documentation

This directory contains command-line tools for managing Chroma vector databases and PDF document processing. All tools are designed to work with ChromaDB's persistent client for local vector storage.

## Collection Management Tools

### `lscol.py` - List Collections
Lists all collections in a Chroma database with document counts.

**Usage:**
```bash
./lscol.py /path/to/chroma/data
```

**Features:**
- Shows collection names and document counts
- Handles empty databases gracefully

### `mkcol.py` - Make Collection
Creates new Chroma collections with configurable embedding functions.

**Usage:**
```bash
./mkcol.py /path/to/chroma/data collection_name
```

**Embedding:**
- Uses mpnet-768 (all-mpnet-base-v2, 768 dimensions, best quality)

### `rmcol.py` - Remove Collection
Deletes collections from the Chroma database with safety confirmations.

**Usage:**
```bash
./rmcol.py /path/to/chroma/data collection_name [--confirm]
```

**Features:**
- Shows document count before deletion
- Requires confirmation unless `--confirm` flag is used
- Safe deletion with warnings

## PDF Document Tools

### `addpdf.py` - Add PDF to Collection
Adds PDF documents to Chroma collections using semantic chunking.

**Usage:**
```bash
./addpdf.py --collection collection_name /path/to/file.pdf
./addpdf.py -c collection_name /path/to/file.pdf
```

**Features:**
- Smart paragraph detection and chunking
- Automatic text extraction using pypdf
- Metadata preservation (filename, chunk index, source path)
- Duplicate detection and handling

### `rmpdf.py` - Remove PDF from Collection
Removes all documents from a specific PDF file from a collection.

**Usage:**
```bash
./rmpdf.py /path/to/chroma/data collection_name /path/to/file.pdf [--dry-run]
```

**Features:**
- Identifies documents by source file metadata
- Dry-run mode for testing
- Shows what will be removed before deletion

### `pdfstruct.py` - Analyze PDF Structure
Analyzes the internal structure of PDF files for debugging and optimization.

**Usage:**
```bash
./pdfstruct.py /path/to/file.pdf
```

**Features:**
- PDF structure analysis
- Text extraction debugging
- Dependency checking with helpful error messages

## File and Directory Management

### `colfiles.py` - List Collection Files
Lists all original files that have been added to a collection.

**Usage:**
```bash
./colfiles.py /path/to/chroma/data collection_name [--names-only]
```

**Features:**
- Shows source files in collections
- Groups by filename with chunk counts
- Optional names-only output mode

### `manage_dirs.py` - Directory Management
Manages multiple Chroma database directories with SQLite tracking.

**Usage:**
```bash
./manage_dirs.py --add name /path/to/directory
./manage_dirs.py --list
./manage_dirs.py --set-active name
./manage_dirs.py --remove name
```

**Features:**
- SQLite database for directory tracking
- Active directory management
- Directory validation and safety checks

## Dependencies

Most tools require:
- `chromadb` - Vector database functionality
- `pypdf` - PDF text extraction
- `pathlib` - Path handling
- `sqlite3` - Directory management (manage_dirs.py only)

For embedding functions requiring sentence-transformers:
```bash
pip install sentence-transformers
```

## Common Usage Patterns

1. **Create a collection:**
   ```bash
   ./mkcol.py /data/chroma my_collection
   ```

2. **Add PDFs to collection:**
   ```bash
   ./addpdf.py -c my_collection document1.pdf
   ./addpdf.py -c my_collection document2.pdf
   ```

3. **List collection contents:**
   ```bash
   ./lscol.py /data/chroma
   ./colfiles.py /data/chroma my_collection
   ```

4. **Remove specific content:**
   ```bash
   ./rmpdf.py /data/chroma my_collection document1.pdf
   ```

5. **Delete entire collection:**
   ```bash
   ./rmcol.py /data/chroma my_collection
   ```

All tools include built-in help via `--help` flag and provide descriptive error messages for common issues.