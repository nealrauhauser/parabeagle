# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chroma MCP (Model Context Protocol) Server that provides vector database integration for LLM applications. It's a Python package that allows AI models to create collections, store documents with embeddings, and perform vector search, full text search, and metadata filtering using ChromaDB.

## Development Commands

### Testing
- Run all tests: `pytest`
- Run tests with coverage: `pytest --cov=src`
- Run specific test file: `pytest tests/test_server.py`
- Run tests in verbose mode: `pytest -v`

### Code Quality  
- Lint code: `ruff check src/ tests/`
- Format code: `ruff format src/ tests/`
- Type checking: Not configured (no mypy or similar)

### Installation & Setup
- Install package in development mode: `pip install -e .`
- Install with optional dependencies: `pip install -e .[sentence-transformers]`
- **For embeddings**: `pip install sentence-transformers` (required for mpnet-768)
- Run the server: `parabeagle` or `python -m chroma_mcp`

## Architecture

### Core Structure
- **Entry Point**: `src/chroma_mcp/__init__.py` exports the main function
- **Main Server**: `src/chroma_mcp/server.py` contains all MCP tools and client logic
- **CLI Tools**: `cli/` directory with standalone tools for PDF ingestion and collection management
- **Import/Export**: `impexp/` directory for collection portability (backup/restore/sharing)
- **Substack Pipeline**: `Substack/` directory for web scraping Substack publications to PDFs
- **Package**: Single Python package using FastMCP framework for MCP protocol

### Related Documentation
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Onboarding guide with terminology and workflows
- **[CLI_TOOLS.md](CLI_TOOLS.md)** - Complete CLI tools reference
- **[impexp/EXPORT_IMPORT.md](impexp/EXPORT_IMPORT.md)** - Import/export system documentation

### Key Components

#### Client Management (`server.py:72-141`)
- Global `_chroma_client` singleton pattern
- Support for 4 client types: ephemeral, persistent, http, cloud  
- Environment variable and command-line argument parsing
- Automatic SSL/TLS configuration for cloud/http clients

#### MCP Tools Architecture
The server exposes tools in two main categories:

**Collection Tools** (`server.py:143-309`):
- `chroma_list_collections` - List collections with pagination
- `chroma_create_collection` - Create with configurable embedding functions
- `chroma_peek_collection` - Sample documents from collection
- `chroma_get_collection_info` - Collection metadata and stats
- `chroma_modify_collection` - Update name/metadata
- `chroma_delete_collection` - Remove collections

**Document Tools** (`server.py:736+`):
- `chroma_add_documents` - **DISABLED** (use CLI `addpdf.py` instead)
- `chroma_query_documents` - Semantic search with metadata filtering  
- `chroma_get_documents` - Retrieve by ID or filter with pagination
- `chroma_update_documents` - Update existing document content/metadata
- `chroma_delete_documents` - Remove documents by ID

#### Embedding Functions (`server.py:419-423`)
Uses mpnet-768 (768 dimensions) for best quality semantic search:
- `mpnet-768`: all-mpnet-base-v2 model (768 dimensions) - **Best quality, only option**

This model runs locally without API keys and automatically downloads on first use.

### Error Handling Pattern
- All tools use consistent error handling that wraps ChromaDB exceptions
- Input validation with descriptive ValueError messages
- Global client initialization with connection retry logic

## Configuration

### Client Types & Environment Variables
- **Ephemeral**: In-memory (default, no config needed)
- **Persistent**: `CHROMA_DATA_DIR` for local file storage
- **HTTP**: `CHROMA_HOST`, `CHROMA_PORT`, optional `CHROMA_SSL`, `CHROMA_CUSTOM_AUTH_CREDENTIALS`
- **Cloud**: `CHROMA_TENANT`, `CHROMA_DATABASE`, `CHROMA_API_KEY` (connects to api.trychroma.com)

### Environment Files
- Default `.chroma_env` file loaded automatically
- Custom path via `CHROMA_DOTENV_PATH` or `--dotenv-path`

## Testing Strategy

The test suite (`tests/test_server.py`) uses pytest with async support and covers:
- All MCP tool functions with success/error cases
- Client type initialization and argument parsing
- Environment variable precedence and validation
- Collection and document CRUD operations
- Edge cases like duplicate IDs, empty collections, non-existent resources
- Testing strategy verifies all MCP tool functions.

## CLI Tools Ecosystem

The `cli/` directory contains standalone tools for document management. See [CLI_TOOLS.md](CLI_TOOLS.md) for full documentation.

### Directory Management
- **`manage_dirs.py`** - SQLite-backed directory tracking (`chroma_directories.sqlite3`)
  - `--add NAME` creates subdirectory under CHROMADIR and registers it
  - `--set-active NAME` switches active directory for all CLI tools
  - `--list` shows all directories with active status
  - `--remove NAME` deletes directory and physical files

### Collection Management
- **`lscol.py`** - List collections with document counts
- **`mkcol.py`** - Create collections (uses mpnet-768 embedding)
- **`rmcol.py`** - Delete collections with confirmation
- **`colfiles.py`** - List files in a collection with chunk counts

### Document Management
- **`addpdf.py`** - PDF ingestion with smart chunking
  - SHA256 duplicate detection
  - 5 heuristics for paragraph detection
  - Configurable chunk sizes (default 100-3000 chars)
  - Batch processing (100 chunks per batch)
  - Logging to `parabeagle.log`
- **`rmpdf.py`** - Remove PDFs by source file metadata
- **`pdfstruct.py`** - PDF structure analysis for debugging

## Import/Export System

The `impexp/` directory provides collection portability. See [impexp/EXPORT_IMPORT.md](impexp/EXPORT_IMPORT.md) for details.

### Archive Format
```
collection_name.zip
├── manifest.json              # Metadata, document counts, PDFs list
├── collection_metadata.json   # Configuration (embedding, distance metric)
├── documents.json             # All chunks with IDs, text, metadata
├── pdfs/                      # Original source PDFs (optional)
└── chroma/                    # ChromaDB database files
```

### Tools
- **`export_collection.py`** - Export to ZIP archive
  - `--no-pdfs` for ChromaDB-only export
  - Includes SHA256 verification hashes
- **`import_collection.py`** - Import from archive
  - `--name` to override collection name
  - `--force` to overwrite existing collections
  - `--pdf-dir` to specify PDF extraction location

### Use Cases
- Backup and restore workflows
- Sharing collections across machines/teams
- Migration between environments

## Substack Pipeline

The `Substack/` directory contains tools for scraping Substack publications into PDFs for ingestion.

### Tools
- **`SubstackCollector.py`** - Playwright-based scraper
  - Reads sitemap XML for URL discovery
  - Removes modals, headers, footers via DOM manipulation
  - High-quality PDF generation (2x DPI, letter format)
  - Skips already-downloaded PDFs
  - Usage: `python SubstackCollector.py https://publication.substack.com/sitemap.xml`
- **`pdfwords.py`** - Word count utility for PDFs

### Workflow
```bash
# 1. Scrape Substack to PDFs
python Substack/SubstackCollector.py https://example.substack.com/sitemap.xml

# 2. Ingest PDFs into collection
./cli/addpdf.py -c my-collection ./pdfs/*.pdf
```

## Architectural Patterns

### Distance Metric
- Uses **cosine distance** (changed from L2) for MindsDB compatibility

### Duplicate Detection
- SHA256 hashing of PDF files prevents re-processing
- Hash stored in document metadata for verification

### Logging
- CLI tools log to `parabeagle.log` in current working directory
- Use `-v` or `--verbose` flags for detailed output

### Code Patterns
- All CLI tools import shared utilities from `cli/common.py`:
  - Directory management functions (`get_active_directory`, `resolve_data_directory`)
  - `Logger` class for dual console/file logging
  - `calculate_sha256` for duplicate detection
  - `extract_text_from_pdf` for PDF processing
  - `get_embedding_function` for mpnet-768 embeddings