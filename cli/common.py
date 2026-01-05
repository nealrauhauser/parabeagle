#!/usr/bin/env python
"""
Shared utilities for Parabeagle CLI tools.

This module provides common functionality used across multiple CLI tools:
- Directory database management (SQLite-backed active directory tracking)
- Logging utilities
- SHA256 hashing for duplicate detection
- PDF text extraction
- Embedding function configuration
"""

import os
import sqlite3
import hashlib
from typing import Optional

# Database filename used across all tools
DB_FILENAME = 'chroma_directories.sqlite3'


# =============================================================================
# Directory Database Functions
# =============================================================================

def init_directory_db(db_path: str) -> None:
    """Initialize the directory management database if it doesn't exist.

    Args:
        db_path: Full path to the SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            path TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_db_path(base_dir: str) -> str:
    """Get the path to the directory database.

    Args:
        base_dir: The CHROMADIR base directory

    Returns:
        Full path to the SQLite database file
    """
    return os.path.join(base_dir, DB_FILENAME)


def get_active_directory(base_dir: str) -> Optional[str]:
    """Get the currently active directory from the directory database.

    Auto-initializes the database if it doesn't exist.

    Args:
        base_dir: The CHROMADIR base directory

    Returns:
        Path to the active directory, or None if no active directory is set
    """
    if not base_dir:
        return None

    db_path = get_db_path(base_dir)

    # Auto-initialize database if it doesn't exist
    if not os.path.exists(db_path):
        init_directory_db(db_path)
        return None  # No active directory yet

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


def get_directory_by_name(base_dir: str, name: str) -> Optional[str]:
    """Get a directory path by its name.

    Args:
        base_dir: The CHROMADIR base directory
        name: The name of the directory to look up

    Returns:
        Path to the named directory, or None if not found
    """
    if not base_dir:
        return None

    db_path = get_db_path(base_dir)
    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT path FROM directories WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
    except sqlite3.Error:
        pass

    return None


def resolve_data_directory(
    base_dir: str,
    directory_name: Optional[str] = None
) -> Optional[str]:
    """Resolve the data directory to use based on arguments.

    This implements the standard resolution logic used by all CLI tools:
    1. If directory_name is specified, look it up by name
    2. Otherwise, use the active directory if one is set
    3. Fall back to the base_dir itself

    Args:
        base_dir: The CHROMADIR base directory (from env or --data-dir)
        directory_name: Optional specific directory name to use

    Returns:
        The resolved data directory path, or None if base_dir is not set
    """
    if not base_dir:
        return None

    if directory_name:
        named_dir = get_directory_by_name(base_dir, directory_name)
        if named_dir:
            return named_dir
        return None  # Named directory not found

    # Try active directory, fall back to base_dir
    active_dir = get_active_directory(base_dir)
    return active_dir if active_dir else base_dir


# =============================================================================
# Logging Utilities
# =============================================================================

class Logger:
    """Simple logger that writes to both console and file."""

    def __init__(self, log_path: Optional[str] = None):
        """Initialize the logger.

        Args:
            log_path: Path to log file. If None, only prints to console.
        """
        self._file = None
        if log_path:
            self._file = open(log_path, 'a', encoding='utf-8')

    def log(self, message: str) -> None:
        """Print message to console and write to log file."""
        print(message)
        if self._file:
            self._file.write(f"{message}\n")
            self._file.flush()

    def close(self) -> None:
        """Close the log file."""
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# =============================================================================
# File Utilities
# =============================================================================

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract text from a PDF file using pypdf.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text, or None if extraction failed
    """
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
    except Exception:
        # Return None to signal error, let caller handle printing
        return None


# =============================================================================
# Embedding Functions
# =============================================================================

def get_embedding_function():
    """Get the mpnet-768 embedding function.

    Returns:
        SentenceTransformerEmbeddingFunction configured with all-mpnet-base-v2
    """
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    return SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )
