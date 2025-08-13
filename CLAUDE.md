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
- **For 768-dimension embeddings**: `pip install sentence-transformers` (required for mpnet-768, bert-768, minilm-384)
- Run the server: `chroma-mcp` or `python -m chroma_mcp`

## Architecture

### Core Structure
- **Entry Point**: `src/chroma_mcp/__init__.py` exports the main function
- **Main Server**: `src/chroma_mcp/server.py` contains all MCP tools and client logic
- **Package**: Single Python package using FastMCP framework for MCP protocol

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

**Document Tools** (`server.py:311-571`):
- `chroma_add_documents` - Bulk document insertion with validation
- `chroma_query_documents` - Semantic search with metadata filtering  
- `chroma_get_documents` - Retrieve by ID or filter with pagination
- `chroma_update_documents` - Update existing document content/metadata
- `chroma_delete_documents` - Remove documents by ID

#### Embedding Functions (`server.py:167-182`)
Supports local embedding models only via ChromaDB's SentenceTransformer integration:
- `default`: DefaultEmbeddingFunction (all-MiniLM-L6-v2, 384 dimensions)
- `mpnet-768`: all-mpnet-base-v2 model (768 dimensions) - **Best quality for 768-dim**
- `bert-768`: all-distilroberta-v1 model (768 dimensions) - **Fast 768-dim alternative**
- `minilm-384`: all-MiniLM-L6-v2 model (384 dimensions) - **Explicit 384-dim option**

All models run locally without API keys and automatically download on first use.

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