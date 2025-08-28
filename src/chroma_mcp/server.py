from typing import Dict, List, TypedDict, Union
from enum import Enum
import chromadb
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import argparse
from chromadb.config import Settings
import ssl
import uuid
import time
import json
import sqlite3
from typing_extensions import TypedDict


from chromadb.api.collection_configuration import CreateCollectionConfiguration
from chromadb.api import EmbeddingFunction
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    SentenceTransformerEmbeddingFunction,
    CohereEmbeddingFunction,
    OpenAIEmbeddingFunction,
    JinaEmbeddingFunction,
    VoyageAIEmbeddingFunction,
    RoboflowEmbeddingFunction,
)

# Initialize FastMCP server
mcp = FastMCP("chroma")

# Global variables
_chroma_client = None
_active_directory = None
_directory_db_path = None


def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description="FastMCP server for Chroma DB")
    parser.add_argument(
        "--client-type",
        choices=["http", "cloud", "persistent", "ephemeral"],
        default=os.getenv("CHROMA_CLIENT_TYPE", "ephemeral"),
        help="Type of Chroma client to use",
    )
    parser.add_argument(
        "--data-dir",
        default=os.getenv("CHROMA_DATA_DIR"),
        help="Directory for persistent client data (only used with persistent client)",
    )
    parser.add_argument(
        "--host", help="Chroma host (required for http client)", default=os.getenv("CHROMA_HOST")
    )
    parser.add_argument(
        "--port", help="Chroma port (optional for http client)", default=os.getenv("CHROMA_PORT")
    )
    parser.add_argument(
        "--custom-auth-credentials",
        help="Custom auth credentials (optional for http client)",
        default=os.getenv("CHROMA_CUSTOM_AUTH_CREDENTIALS"),
    )
    parser.add_argument(
        "--tenant",
        help="Chroma tenant (optional for http client)",
        default=os.getenv("CHROMA_TENANT"),
    )
    parser.add_argument(
        "--database",
        help="Chroma database (required if tenant is provided)",
        default=os.getenv("CHROMA_DATABASE"),
    )
    parser.add_argument(
        "--api-key",
        help="Chroma API key (required if tenant is provided)",
        default=os.getenv("CHROMA_API_KEY"),
    )
    parser.add_argument(
        "--ssl",
        help="Use SSL (optional for http client)",
        type=lambda x: x.lower() in ["true", "yes", "1", "t", "y"],
        default=os.getenv("CHROMA_SSL", "true").lower() in ["true", "yes", "1", "t", "y"],
    )
    parser.add_argument(
        "--dotenv-path",
        help="Path to .env file",
        default=os.getenv("CHROMA_DOTENV_PATH", ".chroma_env"),
    )
    return parser


def init_directory_db(db_path: str):
    """Initialize the directory management database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create directories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            path TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_directory_db_path(base_dir: str) -> str:
    """Get the path to the directory management database."""
    return os.path.join(base_dir, "chroma_directories.sqlite3")


def list_directories() -> List[Dict]:
    """List all configured directories."""
    if not _directory_db_path or not os.path.exists(_directory_db_path):
        return []

    conn = sqlite3.connect(_directory_db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, path, is_active, created_at 
        FROM directories 
        ORDER BY name
    """)

    directories = []
    for row in cursor.fetchall():
        directories.append(
            {"name": row[0], "path": row[1], "is_active": bool(row[2]), "created_at": row[3]}
        )

    conn.close()
    return directories


def add_directory(name: str, path: str) -> bool:
    """Add a new directory configuration."""
    if not _directory_db_path:
        return False

    # Validate path exists
    if not os.path.exists(path):
        raise ValueError(f"Directory does not exist: {path}")

    if not os.path.isdir(path):
        raise ValueError(f"Path is not a directory: {path}")

    conn = sqlite3.connect(_directory_db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO directories (name, path) 
            VALUES (?, ?)
        """,
            (name, os.path.abspath(path)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        raise ValueError(f"Directory name '{name}' already exists")
    finally:
        conn.close()


def remove_directory(name: str) -> bool:
    """Remove a directory configuration."""
    if not _directory_db_path:
        return False

    conn = sqlite3.connect(_directory_db_path)
    cursor = conn.cursor()

    # Check if it's the active directory
    cursor.execute("SELECT is_active FROM directories WHERE name = ?", (name,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        raise ValueError(f"Directory '{name}' not found")

    if result[0]:  # is_active
        conn.close()
        raise ValueError(
            f"Cannot remove active directory '{name}'. Set another directory as active first."
        )

    cursor.execute("DELETE FROM directories WHERE name = ?", (name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return deleted


def set_active_directory(name: str) -> str:
    """Set the active directory and return its path."""
    global _active_directory, _chroma_client

    if not _directory_db_path:
        raise ValueError("Directory database not initialized")

    conn = sqlite3.connect(_directory_db_path)
    cursor = conn.cursor()

    # Check if directory exists
    cursor.execute("SELECT path FROM directories WHERE name = ?", (name,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        raise ValueError(f"Directory '{name}' not found")

    directory_path = result[0]

    # Verify directory still exists on filesystem
    if not os.path.exists(directory_path):
        conn.close()
        raise ValueError(f"Directory path no longer exists: {directory_path}")

    # Clear all active flags
    cursor.execute("UPDATE directories SET is_active = 0")

    # Set new active directory
    cursor.execute("UPDATE directories SET is_active = 1 WHERE name = ?", (name,))

    conn.commit()
    conn.close()

    # Reset the chroma client to use new directory
    _chroma_client = None
    _active_directory = directory_path

    return directory_path


def get_active_directory() -> str:
    """Get the currently active directory path."""
    global _active_directory

    if _active_directory:
        return _active_directory

    if not _directory_db_path or not os.path.exists(_directory_db_path):
        return None

    conn = sqlite3.connect(_directory_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT path FROM directories WHERE is_active = 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        _active_directory = result[0]
        return _active_directory

    return None


def get_chroma_client(args=None):
    """Get or create the global Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        if args is None:
            # Create parser and parse args if not provided
            parser = create_parser()
            args = parser.parse_args()

        # Load environment variables from .env file if it exists
        load_dotenv(dotenv_path=args.dotenv_path)
        if args.client_type == "http":
            if not args.host:
                raise ValueError(
                    "Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client"
                )

            settings = Settings()
            if args.custom_auth_credentials:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=args.custom_auth_credentials,
                )

            # Handle SSL configuration
            try:
                _chroma_client = chromadb.HttpClient(
                    host=args.host,
                    port=args.port if args.port else None,
                    ssl=args.ssl,
                    settings=settings,
                )
            except ssl.SSLError as e:
                import sys

                print(f"SSL connection failed: {str(e)}", file=sys.stderr)
                raise
            except Exception as e:
                import sys

                print(f"Error connecting to HTTP client: {str(e)}", file=sys.stderr)
                raise

        elif args.client_type == "cloud":
            if not args.tenant:
                raise ValueError(
                    "Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client"
                )
            if not args.database:
                raise ValueError(
                    "Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client"
                )
            if not args.api_key:
                raise ValueError(
                    "API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client"
                )

            try:
                _chroma_client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,  # Always use SSL for cloud
                    tenant=args.tenant,
                    database=args.database,
                    headers={"x-chroma-token": args.api_key},
                )
            except ssl.SSLError as e:
                import sys

                print(f"SSL connection failed: {str(e)}", file=sys.stderr)
                raise
            except Exception as e:
                import sys

                print(f"Error connecting to cloud client: {str(e)}", file=sys.stderr)
                raise

        elif args.client_type == "persistent":
            # Use active directory if available, otherwise fall back to args.data_dir
            active_dir = get_active_directory()
            data_dir = active_dir if active_dir else args.data_dir

            if not data_dir:
                raise ValueError(
                    "Data directory must be provided via --data-dir flag when using persistent client"
                )
            _chroma_client = chromadb.PersistentClient(path=data_dir)
        else:  # ephemeral
            _chroma_client = chromadb.EphemeralClient()

    return _chroma_client


##### Collection Tools #####


@mcp.tool()
async def chroma_list_collections(limit: int | None = None, offset: int | None = None) -> str:
    """List all collection names in the Chroma database with pagination support.

    Args:
        limit: Optional maximum number of collections to return
        offset: Optional number of collections to skip before returning results

    Returns:
        Directory path followed by newline-separated list of collection names, or "No collections found" if database is empty
    """
    client = get_chroma_client()
    try:
        colls = client.list_collections(limit=limit, offset=offset)
        # Safe handling: If colls is None or empty, return a special marker
        if not colls:
            return "No collections found"
        
        # Get the active directory to display above collection list
        active_dir = get_active_directory()
        
        # Return collection names with directory shown once at top
        names = [coll.name for coll in colls]
        if active_dir:
            return f"{active_dir}\n" + "\n".join(names)
        else:
            return "\n".join(names)

    except Exception as e:
        raise Exception(f"Failed to list collections: {str(e)}") from e


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


# Combined embedding functions: local models + cloud APIs
mcp_known_embedding_functions: Dict[str, EmbeddingFunction] = {
    # Local embedding functions (recommended for privacy and cost)
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
    # Cloud-based embedding functions (require API keys)
    "cohere": CohereEmbeddingFunction,
    "openai": OpenAIEmbeddingFunction,
    "jina": JinaEmbeddingFunction,
    "voyageai": VoyageAIEmbeddingFunction,
    "roboflow": RoboflowEmbeddingFunction,
}


@mcp.tool()
async def chroma_create_collection(
    collection_name: str,
    embedding_function_name: str = "default",
    metadata: Dict | None = None,
) -> str:
    """Create a new Chroma collection with configurable embedding functions.

    Args:
        collection_name: Name of the collection to create
        embedding_function_name: Name of the embedding function to use.
                                 Local options: 'default' (384-dim), 'mpnet-768' (768-dim), 'bert-768' (768-dim), 'minilm-384' (384-dim)
                                 Cloud options: 'cohere', 'openai', 'jina', 'voyageai', 'roboflow' (require API keys)
        metadata: Optional metadata dict to add to the collection
    """
    client = get_chroma_client()

    embedding_function = mcp_known_embedding_functions[embedding_function_name]

    configuration = CreateCollectionConfiguration(embedding_function=embedding_function())

    try:
        client.create_collection(
            name=collection_name, configuration=configuration, metadata=metadata
        )
        config_msg = f" with configuration: {configuration}"
        return f"Successfully created collection {collection_name}{config_msg}"
    except Exception as e:
        raise Exception(f"Failed to create collection '{collection_name}': {str(e)}") from e


@mcp.tool()
async def chroma_peek_collection(collection_name: str, limit: int = 5) -> Dict:
    """Peek at documents in a Chroma collection.

    Args:
        collection_name: Name of the collection to peek into
        limit: Number of documents to peek at
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.peek(limit=limit)
        return results
    except Exception as e:
        raise Exception(f"Failed to peek collection '{collection_name}': {str(e)}") from e


@mcp.tool()
async def chroma_get_collection_info(collection_name: str) -> Dict:
    """Get information about a Chroma collection.

    Args:
        collection_name: Name of the collection to get info about
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)

        # Get collection count
        count = collection.count()

        # Peek at a few documents
        peek_results = collection.peek(limit=3)

        return {"name": collection_name, "count": count, "sample_documents": peek_results}
    except Exception as e:
        raise Exception(f"Failed to get collection info for '{collection_name}': {str(e)}") from e


@mcp.tool()
async def chroma_get_collection_count(collection_name: str) -> int:
    """Get the number of documents in a Chroma collection.

    Args:
        collection_name: Name of the collection to count
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.count()
    except Exception as e:
        raise Exception(f"Failed to get collection count for '{collection_name}': {str(e)}") from e


@mcp.tool()
async def chroma_modify_collection(
    collection_name: str,
    new_name: str | None = None,
    new_metadata: Dict | None = None,
) -> str:
    """Modify a Chroma collection's name or metadata.

    Args:
        collection_name: Name of the collection to modify
        new_name: Optional new name for the collection
        new_metadata: Optional new metadata for the collection
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        collection.modify(name=new_name, metadata=new_metadata)

        modified_aspects = []
        if new_name:
            modified_aspects.append("name")
        if new_metadata:
            modified_aspects.append("metadata")

        return f"Successfully modified collection {collection_name}: updated {' and '.join(modified_aspects)}"
    except Exception as e:
        raise Exception(f"Failed to modify collection '{collection_name}': {str(e)}") from e


@mcp.tool()
async def chroma_fork_collection(
    collection_name: str,
    new_collection_name: str,
) -> str:
    """Fork a Chroma collection.

    Args:
        collection_name: Name of the collection to fork
        new_collection_name: Name of the new collection to create
        metadata: Optional metadata dict to add to the new collection
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        collection.fork(new_collection_name)
        return f"Successfully forked collection {collection_name} to {new_collection_name}"
    except Exception as e:
        raise Exception(f"Failed to fork collection '{collection_name}': {str(e)}") from e


@mcp.tool()
async def chroma_delete_collection(collection_name: str) -> str:
    """Delete a Chroma collection.

    Args:
        collection_name: Name of the collection to delete
    """
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        return f"Successfully deleted collection {collection_name}"
    except Exception as e:
        raise Exception(f"Failed to delete collection '{collection_name}': {str(e)}") from e


##### Directory Management Tools #####


@mcp.tool()
async def chroma_list_directories() -> str:
    """List all configured Chroma directories.

    Returns:
        Formatted string showing directory name, path, and active status
    """
    try:
        directories = list_directories()

        if not directories:
            return "No directories configured"

        lines = ["Configured directories:"]
        for dir_info in directories:
            status = " (ACTIVE)" if dir_info["is_active"] else ""
            lines.append(f"  {dir_info['name']}: {dir_info['path']}{status}")

        return "\n".join(lines)

    except Exception as e:
        raise Exception(f"Failed to list directories: {str(e)}") from e


@mcp.tool()
async def chroma_add_directory(name: str, path: str) -> str:
    """Add a new Chroma directory configuration.

    Args:
        name: Symbolic name for the directory
        path: Filesystem path to the directory

    Returns:
        Success message
    """
    try:
        add_directory(name, path)
        return f"Successfully added directory '{name}' -> {path}"

    except Exception as e:
        raise Exception(f"Failed to add directory: {str(e)}") from e


@mcp.tool()
async def chroma_remove_directory(name: str) -> str:
    """Remove a Chroma directory configuration.

    Args:
        name: Symbolic name of the directory to remove

    Returns:
        Success message
    """
    try:
        if remove_directory(name):
            return f"Successfully removed directory '{name}'"
        else:
            return f"Directory '{name}' not found"

    except Exception as e:
        raise Exception(f"Failed to remove directory: {str(e)}") from e


@mcp.tool()
async def chroma_set_active_directory(name: str) -> str:
    """Set the active Chroma directory.

    Args:
        name: Symbolic name of the directory to make active

    Returns:
        Success message with new active directory path
    """
    try:
        directory_path = set_active_directory(name)
        return f"Successfully set active directory to '{name}' -> {directory_path}"

    except Exception as e:
        raise Exception(f"Failed to set active directory: {str(e)}") from e


@mcp.tool()
async def chroma_get_active_directory() -> str:
    """Get the currently active Chroma directory.

    Returns:
        Current active directory information
    """
    try:
        directories = list_directories()
        active_dirs = [d for d in directories if d["is_active"]]

        if not active_dirs:
            return "No active directory set"

        active_dir = active_dirs[0]
        return f"Active directory: {active_dir['name']} -> {active_dir['path']}"

    except Exception as e:
        raise Exception(f"Failed to get active directory: {str(e)}") from e


##### Document Tools #####
@mcp.tool()
async def chroma_add_documents(
    collection_name: str, documents: List[str], ids: List[str], metadatas: List[Dict] | None = None
) -> str:
    """Add documents to a Chroma collection.

    Args:
        collection_name: Name of the collection to add documents to
        documents: List of text documents to add
        ids: List of IDs for the documents (required)
        metadatas: Optional list of metadata dictionaries for each document
    """
    if not documents:
        raise ValueError("The 'documents' list cannot be empty.")

    if not ids:
        raise ValueError("The 'ids' list is required and cannot be empty.")

    # Check if there are empty strings in the ids list
    if any(not id.strip() for id in ids):
        raise ValueError("IDs cannot be empty strings.")

    if len(ids) != len(documents):
        raise ValueError(
            f"Number of ids ({len(ids)}) must match number of documents ({len(documents)})."
        )

    client = get_chroma_client()
    try:
        collection = client.get_or_create_collection(collection_name)

        # Check for duplicate IDs
        existing_ids = collection.get(include=[])["ids"]
        duplicate_ids = [id for id in ids if id in existing_ids]

        if duplicate_ids:
            raise ValueError(
                f"The following IDs already exist in collection '{collection_name}': {duplicate_ids}. "
                f"Use 'chroma_update_documents' to update existing documents."
            )

        result = collection.add(documents=documents, metadatas=metadatas, ids=ids)

        # Check the return value
        if result and isinstance(result, dict):
            # If the return value is a dictionary, it may contain success information
            if "success" in result and not result["success"]:
                raise Exception(f"Failed to add documents: {result.get('error', 'Unknown error')}")

            # If the return value contains the actual number added
            if "count" in result:
                return f"Successfully added {result['count']} documents to collection {collection_name}"

        # Default return
        return f"Successfully added {len(documents)} documents to collection {collection_name}, result is {result}"
    except Exception as e:
        raise Exception(
            f"Failed to add documents to collection '{collection_name}': {str(e)}"
        ) from e


@mcp.tool()
async def chroma_query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas", "distances"],
) -> Dict:
    """Query documents from a Chroma collection with advanced filtering.

    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts to search for
        n_results: Number of results to return per query
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
               Examples:
               - Contains: {"$contains": "value"}
               - Not contains: {"$not_contains": "value"}
               - Regex: {"$regex": "[a-z]+"}
               - Not regex: {"$not_regex": "[a-z]+"}
               - Logical AND: {"$and": [{"$contains": "value1"}, {"$not_regex": "[a-z]+"}]}
               - Logical OR: {"$or": [{"$regex": "[a-z]+"}, {"$not_contains": "value2"}]}
        include: List of what to include in response. By default, this will include documents, metadatas, and distances.
    """
    if not query_texts:
        raise ValueError("The 'query_texts' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include,
        )
    except Exception as e:
        raise Exception(
            f"Failed to query documents from collection '{collection_name}': {str(e)}"
        ) from e


@mcp.tool()
async def chroma_query_with_sources(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Dict | None = None,
    where_document: Dict | None = None,
) -> str:
    """Query documents and return results formatted with source citations and bibliography.

    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts to search for
        n_results: Number of results to return per query
        where: Optional metadata filters
        where_document: Optional document content filters

    Returns:
        Formatted string with results and bibliography of source files
    """
    if not query_texts:
        raise ValueError("The 'query_texts' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("documents"):
            return "No results found."

        output_lines = []
        sources_used = set()

        for query_idx, query_text in enumerate(query_texts):
            if len(query_texts) > 1:
                output_lines.append(f"Query: {query_text}")
                output_lines.append("")

            docs = results["documents"][query_idx]
            metas = results["metadatas"][query_idx]
            dists = results["distances"][query_idx]

            for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
                similarity = 1 - dist

                # Extract source info from metadata
                source_file = meta.get("filename", "Unknown") if meta else "Unknown"
                chunk_idx = meta.get("chunk_index", 0) if meta else 0
                source_path = meta.get("source", "") if meta else ""

                # Just show the document content without source info in each result
                doc_text = doc if len(doc) <= 400 else doc[:400] + "..."
                output_lines.append(doc_text)
                output_lines.append("")

                # Collect sources
                if source_file != "Unknown":
                    sources_used.add(source_file)

        # Add simple bibliography at the end
        if sources_used:
            output_lines.append("Sources:")
            for filename in sorted(sources_used):
                output_lines.append(filename)

        return "\n".join(output_lines)

    except Exception as e:
        raise Exception(
            f"Failed to query documents from collection '{collection_name}': {str(e)}"
        ) from e


@mcp.tool()
async def chroma_get_documents(
    collection_name: str,
    ids: List[str] | None = None,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas"],
    limit: int | None = None,
    offset: int | None = None,
) -> Dict:
    """Get documents from a Chroma collection with optional filtering.

    Args:
        collection_name: Name of the collection to get documents from
        ids: Optional list of document IDs to retrieve
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
               Examples:
               - Contains: {"$contains": "value"}
               - Not contains: {"$not_contains": "value"}
               - Regex: {"$regex": "[a-z]+"}
               - Not regex: {"$not_regex": "[a-z]+"}
               - Logical AND: {"$and": [{"$contains": "value1"}, {"$not_regex": "[a-z]+"}]}
               - Logical OR: {"$or": [{"$regex": "[a-z]+"}, {"$not_contains": "value2"}]}
        include: List of what to include in response. By default, this will include documents, and metadatas.
        limit: Optional maximum number of documents to return
        offset: Optional number of documents to skip before returning results

    Returns:
        Dictionary containing the matching documents, their IDs, and requested includes
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.get(
            ids=ids,
            where=where,
            where_document=where_document,
            include=include,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise Exception(
            f"Failed to get documents from collection '{collection_name}': {str(e)}"
        ) from e


@mcp.tool()
async def chroma_update_documents(
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]] | None = None,
    metadatas: List[Dict] | None = None,
    documents: List[str] | None = None,
) -> str:
    """Update documents in a Chroma collection.

    Args:
        collection_name: Name of the collection to update documents in
        ids: List of document IDs to update (required)
        embeddings: Optional list of new embeddings for the documents.
                    Must match length of ids if provided.
        metadatas: Optional list of new metadata dictionaries for the documents.
                   Must match length of ids if provided.
        documents: Optional list of new text documents.
                   Must match length of ids if provided.

    Returns:
        A confirmation message indicating the number of documents updated.

    Raises:
        ValueError: If 'ids' is empty or if none of 'embeddings', 'metadatas',
                    or 'documents' are provided, or if the length of provided
                    update lists does not match the length of 'ids'.
        Exception: If the collection does not exist or if the update operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    if embeddings is None and metadatas is None and documents is None:
        raise ValueError(
            "At least one of 'embeddings', 'metadatas', or 'documents' must be provided for update."
        )

    # Ensure provided lists match the length of ids if they are not None
    if embeddings is not None and len(embeddings) != len(ids):
        raise ValueError("Length of 'embeddings' list must match length of 'ids' list.")
    if metadatas is not None and len(metadatas) != len(ids):
        raise ValueError("Length of 'metadatas' list must match length of 'ids' list.")
    if documents is not None and len(documents) != len(ids):
        raise ValueError("Length of 'documents' list must match length of 'ids' list.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(f"Failed to get collection '{collection_name}': {str(e)}") from e

    # Prepare arguments for update, excluding None values at the top level
    update_args = {
        "ids": ids,
        "embeddings": embeddings,
        "metadatas": metadatas,
        "documents": documents,
    }
    kwargs = {k: v for k, v in update_args.items() if v is not None}

    try:
        collection.update(**kwargs)
        return (
            f"Successfully processed update request for {len(ids)} documents in "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to update documents in collection '{collection_name}': {str(e)}"
        ) from e


@mcp.tool()
async def chroma_delete_documents(collection_name: str, ids: List[str]) -> str:
    """Delete documents from a Chroma collection.

    Args:
        collection_name: Name of the collection to delete documents from
        ids: List of document IDs to delete

    Returns:
        A confirmation message indicating the number of documents deleted.

    Raises:
        ValueError: If 'ids' is empty
        Exception: If the collection does not exist or if the delete operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(f"Failed to get collection '{collection_name}': {str(e)}") from e

    try:
        collection.delete(ids=ids)
        return (
            f"Successfully deleted {len(ids)} documents from "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to delete documents from collection '{collection_name}': {str(e)}"
        ) from e


def validate_thought_data(input_data: Dict) -> Dict:
    """Validate thought data structure."""
    if not input_data.get("sessionId"):
        raise ValueError("Invalid sessionId: must be provided")
    if not input_data.get("thought") or not isinstance(input_data.get("thought"), str):
        raise ValueError("Invalid thought: must be a string")
    if not input_data.get("thoughtNumber") or not isinstance(input_data.get("thoughtNumber"), int):
        raise ValueError("Invalid thoughtNumber: must be a number")
    if not input_data.get("totalThoughts") or not isinstance(input_data.get("totalThoughts"), int):
        raise ValueError("Invalid totalThoughts: must be a number")
    if not isinstance(input_data.get("nextThoughtNeeded"), bool):
        raise ValueError("Invalid nextThoughtNeeded: must be a boolean")

    return {
        "sessionId": input_data.get("sessionId"),
        "thought": input_data.get("thought"),
        "thoughtNumber": input_data.get("thoughtNumber"),
        "totalThoughts": input_data.get("totalThoughts"),
        "nextThoughtNeeded": input_data.get("nextThoughtNeeded"),
        "isRevision": input_data.get("isRevision"),
        "revisesThought": input_data.get("revisesThought"),
        "branchFromThought": input_data.get("branchFromThought"),
        "branchId": input_data.get("branchId"),
        "needsMoreThoughts": input_data.get("needsMoreThoughts"),
    }


def main():
    """Entry point for the Chroma MCP server."""
    global _directory_db_path

    parser = create_parser()
    args = parser.parse_args()

    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
        # re-parse args to read the updated environment variables
        parser = create_parser()
        args = parser.parse_args()

    # Initialize directory management database if using persistent client
    if args.client_type == "persistent" and args.data_dir:
        _directory_db_path = get_directory_db_path(args.data_dir)
        init_directory_db(_directory_db_path)

        # If no directories configured, add the base directory as default
        directories = list_directories()
        if not directories:
            add_directory("default", args.data_dir)
            set_active_directory("default")

    # Validate required arguments based on client type
    if args.client_type == "http":
        if not args.host:
            parser.error(
                "Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client"
            )

    elif args.client_type == "cloud":
        if not args.tenant:
            parser.error(
                "Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client"
            )
        if not args.database:
            parser.error(
                "Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client"
            )
        if not args.api_key:
            parser.error(
                "API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client"
            )

    # Initialize client with parsed args
    try:
        get_chroma_client(args)
        pass  # Successfully initialized Chroma client
    except Exception as e:
        import sys

        print(f"Failed to initialize Chroma client: {str(e)}", file=sys.stderr)
        raise

    # Initialize and run the server
    # Starting MCP server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
