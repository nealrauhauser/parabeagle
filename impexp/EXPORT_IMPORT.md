# Parabeagle Collection Export/Import

## Overview

Parabeagle now supports exporting and importing collections as portable `.zip` archives. These archives contain everything needed to fully restore a collection, including:

1. **Original PDF files** - All source PDFs that were added to the collection
2. **ChromaDB data** - Vector embeddings, HNSW index, and SQLite database
3. **Metadata** - Collection configuration, chunking parameters, and document metadata
4. **Manifest** - Complete archive information for verification and restoration

## Archive Format

### File Structure

```
collection_name.zip
├── manifest.json              # Archive metadata and file inventory
├── collection_metadata.json   # Collection configuration
├── documents.json             # All document chunks and metadata
├── pdfs/                      # Original PDF files
│   ├── document1.pdf
│   ├── document2.pdf
│   └── ...
└── chroma/                    # ChromaDB data
    ├── chroma.sqlite3         # Main database
    └── {segment-uuid}/        # Vector segment directories
        ├── header.bin
        ├── length.bin
        ├── link_lists.bin
        └── data_level0.bin
```

### Metadata Schema

#### manifest.json
```json
{
  "parabeagle_version": "1.0",
  "archive_format_version": "1.0",
  "created_at": "2025-10-12T18:45:00Z",
  "collection_name": "MyDocs",
  "collection_id": "uuid-here",
  "embedding_function": "mpnet-768",
  "distance_metric": "cosine",
  "document_count": 150,
  "chunk_count": 1250,
  "pdf_count": 10,
  "total_size_bytes": 52428800,
  "pdfs": [
    {
      "filename": "document1.pdf",
      "path": "pdfs/document1.pdf",
      "original_path": "/path/to/original/document1.pdf",
      "size_bytes": 1048576,
      "chunks": 45,
      "sha256": "abc123..."
    }
  ],
  "segments": [
    {
      "id": "segment-uuid",
      "scope": "VECTOR",
      "path": "chroma/segment-uuid"
    }
  ]
}
```

#### collection_metadata.json
```json
{
  "name": "MyDocs",
  "metadata": {
    "hnsw:space": "cosine",
    "created_by": "parabeagle_cli"
  },
  "chunking_params": {
    "chunk_type": "semantic"
  }
}
```

## Usage

### Exporting a Collection

```bash
# Basic export (creates MyDocs.zip in current directory)
./cli/export_collection.py -c MyDocs

# Export to specific file
./cli/export_collection.py -c MyDocs -o /backups/mydocs_backup.zip

# Export to directory (creates MyDocs.zip in that directory)
./cli/export_collection.py -c MyDocs -o /backups/

# Export without PDFs (ChromaDB data only, smaller file)
./cli/export_collection.py -c MyDocs --no-pdfs

# With custom ChromaDB directory
./cli/export_collection.py -d /path/to/chroma/ -c MyDocs
```

**Export Options:**
- `-c, --collection-name`: Name of the collection to export (required)
- `-o, --output`: Output path (file or directory). Default: `<collection_name>.zip`
- `--no-pdfs`: Don't include original PDF files (reduces archive size)
- `-d, --data-dir`: ChromaDB data directory (default: `$CHROMADIR`)

### Importing a Collection

```bash
# Basic import (uses original collection name)
./cli/import_collection.py MyDocs.zip

# Import with different name
./cli/import_collection.py MyDocs.zip -c RestoredDocs

# Extract PDFs to specific directory
./cli/import_collection.py MyDocs.zip --pdf-dir /documents/pdfs/

# Force overwrite existing collection
./cli/import_collection.py MyDocs.zip --force

# With custom ChromaDB directory
./cli/import_collection.py -d /path/to/chroma/ MyDocs.zip
```

**Import Options:**
- `archive`: Path to the `.zip` archive file (required)
- `-c, --collection-name`: Name for imported collection (default: original name)
- `--pdf-dir`: Directory to extract PDFs to (default: `./pdfs/`)
- `--force`: Overwrite existing collection with same name
- `-d, --data-dir`: ChromaDB data directory (default: `$CHROMADIR`)

## Use Cases

### 1. Backup and Restore

```bash
# Create backup
./cli/export_collection.py -c ProductDocs -o /backups/

# Restore from backup
./cli/import_collection.py /backups/ProductDocs.zip --force
```

### 2. Sharing Collections

```bash
# Export for sharing (with PDFs)
./cli/export_collection.py -c ResearchPapers -o research_papers.zip

# Import on another machine
./cli/import_collection.py research_papers.zip --pdf-dir ~/Documents/research/
```

### 3. Migration Between Environments

```bash
# Export from development
CHROMADIR=/dev/chroma ./cli/export_collection.py -c TestData

# Import to production
CHROMADIR=/prod/chroma ./cli/import_collection.py TestData.zip --force
```

### 4. Archival (ChromaDB Only)

```bash
# Export just the vector database (smaller, faster)
./cli/export_collection.py -c OldProject --no-pdfs -o archive/
```

## Technical Details

### What Gets Exported

1. **PDFs** (optional):
   - All original PDF files referenced in the collection
   - SHA256 checksums for verification
   - Original file paths preserved in metadata

2. **ChromaDB Data**:
   - `chroma.sqlite3` - Collection metadata, document IDs, text content
   - Vector segments - HNSW index files (`.bin` files)
   - All embeddings and vector data

3. **Documents**:
   - Complete document chunks with text content
   - All metadata (source paths, filenames, chunk indices, etc.)
   - Document IDs

4. **Collection Configuration**:
   - Embedding function name (mpnet-768, etc.)
   - Distance metric (cosine, l2, ip)
   - HNSW configuration
   - Custom metadata

### What Gets Restored

On import, the following is reconstructed:

1. **New Collection** - Created with exact same configuration
2. **All Documents** - Re-added with original IDs and metadata
3. **PDF Files** - Extracted to specified directory with updated paths
4. **Import Metadata** - Added to collection metadata for traceability

### Limitations

- **Embedding Function Must Match**: The same embedding model must be available on the import system
- **Python Dependencies**: `sentence-transformers` required for 768-dim models
- **File Paths**: PDF paths are updated during import to new locations
- **No Incremental Updates**: Import replaces entire collection (with `--force`)

## Best Practices

### For Backups

```bash
# Regular automated backups
./cli/export_collection.py -c Production -o /backups/$(date +%Y%m%d)_production.zip
```

### For Distribution

```bash
# Include PDFs for complete portability
./cli/export_collection.py -c Dataset --output dataset_v1.0.zip

# Verify archive before sharing
unzip -l dataset_v1.0.zip | head -20
```

### For Version Control

```bash
# Export without PDFs to track just the processed data
./cli/export_collection.py -c Analysis --no-pdfs -o snapshots/analysis_$(git rev-parse --short HEAD).zip
```

## Troubleshooting

### "Collection already exists"
Use `--force` to overwrite:
```bash
./cli/import_collection.py archive.zip --force
```

### "PDF not found"
If original PDFs have been moved/deleted:
- Export will warn but continue
- Archive will be created without those PDFs
- Import will work but metadata will reference old paths

### "Unknown embedding function"
If the embedding function isn't available:
- Import will fall back to `mpnet-768`
- You may need to install `sentence-transformers`

### Archive Corruption
Verify archive integrity:
```bash
unzip -t archive.zip
python -m zipfile -l archive.zip
```

## File Format Versioning

Current format version: **1.0**

Future versions may add:
- Compression options
- Incremental exports
- Differential imports
- External embedding support
- Multi-collection archives
