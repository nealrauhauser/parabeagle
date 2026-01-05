# Getting Started with Parabeagle

This software is a fork of the Chroma vector database and as such it requires a bit of an introduction. You probably refer to a single file on a disk as a document, but in Chroma, if that file is more than a couple pages, it will likely get split into multiple "documents" in the database. This is purely an internal term for Chroma, the system will not make a different file on disk for each document, and when you are using the system for case work the responses will contain links to your FILES, not these internal semantic "documents".

When Parabeagle first starts it needs a database directory where it stores its initial default vector database. When you want to add a case it will require a name for a database directory, which is stored under the default directory. Once you have this you can begin adding collections of documents to the database. Each collection originates in a files folder, so an individual case can have multiple sets of files that are mutually exclusive.

## Terminology

| Term | Meaning |
|------|---------|
| **PDF file** | Your actual file on disk (e.g., `contract.pdf`, `deposition.pdf`) |
| **Document** | A text chunk stored in ChromaDB. One PDF file becomes many "documents" when split into paragraphs. |
| **Collection** | A named container within a Chroma directory that holds documents from multiple PDF files |
| **Chroma Directory** | A database folder containing ChromaDB files and one or more collections. This is NOT where your PDF files are stored - it contains only the vector database. Created as a subdirectory under your main CHROMADIR. |
| **CHROMADIR** | Environment variable pointing to the root folder where all your Chroma directories are stored |

**Hierarchy:** CHROMADIR → Chroma Directory → Collection(s) → Documents (chunks)

---

## About This Guide

This guide walks you through creating your first document collection in Parabeagle.

When you add a 10-page PDF to a collection, Parabeagle splits it into semantic chunks (paragraphs). Each chunk becomes a separate "document" in Chroma terminology. A single PDF might create 20-50 documents depending on its length and structure.

## Prerequisites

1. **Set your CHROMADIR environment variable** to point to your Chroma storage location:
   ```bash
   export CHROMADIR=/path/to/your/chroma/
   ```
   Add this to your `~/.profile` to make it permanent and don't forget to "source ~/.profile" to activate the change.

2. **Navigate to the CLI tools directory:**
   ```bash
   cd /path/to/parabeagle/cli
   ```

---

## Step 1: Create a Chroma Directory for Your Project

Each case or project should have its own directory. This keeps your data compartmentalized:

```bash
./manage_dirs.py --add my-project
```

This creates a new subdirectory under your `CHROMADIR` called `my-project/` and registers it in the directory database.

To see all your directories:
```bash
./manage_dirs.py --list
```

---

## Step 2: Set Your Project as Active

Before working with collections, set your project directory as active:

```bash
./manage_dirs.py --set-active my-project
```

All subsequent commands will work within this directory until you change it.

---

## Step 3: Create a Collection

Now create a collection to hold your documents:

```bash
./mkcol.py -c my-collection
```

The `-c` flag specifies the collection name. Choose something descriptive like `depositions`, `contracts`, or `evidence`.

To verify:
```bash
./lscol.py
```

You should see your new collection (with 0 documents).

---

## Step 4: Add PDF Files

Add PDF files to your collection:

```bash
# Add a single PDF
./addpdf.py -c my-collection /path/to/document.pdf

# Add multiple PDFs
./addpdf.py -c my-collection file1.pdf file2.pdf file3.pdf

# Add all PDFs in a directory
./addpdf.py -c my-collection /path/to/pdf/folder/
```

Processing takes 5-7 seconds per short PDF on an M1 Mac. Longer documents take proportionally longer.

For detailed output showing chunk counts and progress:
```bash
./addpdf.py -c my-collection -v /path/to/document.pdf
```

---

## Step 5: Verify Your Collection

Check what's in your collection:

```bash
# List all collections and document counts
./lscol.py

# List all PDF files in a specific collection
./colfiles.py -c my-collection
```

---

## Quick Reference

| Task | Command |
|------|---------|
| List directories | `./manage_dirs.py --list` |
| Switch to a directory | `./manage_dirs.py --set-active name` |
| Create collection | `./mkcol.py -c collection-name` |
| List collections | `./lscol.py` |
| Add PDFs | `./addpdf.py -c collection-name file.pdf` |
| List files in collection | `./colfiles.py -c collection-name` |
| Remove a PDF | `./rmpdf.py -c collection-name file.pdf` |
| Delete collection | `./rmcol.py -c collection-name` |

---

## Example: Setting Up a New Court Case

```bash
# Create and activate a directory for the case
./manage_dirs.py --add smith-v-jones-2024
./manage_dirs.py --set-active smith-v-jones-2024

# Create collections for different document types
./mkcol.py -c depositions
./mkcol.py -c contracts
./mkcol.py -c correspondence

# Load documents
./addpdf.py -c depositions ~/Documents/SmithCase/Depositions/*.pdf
./addpdf.py -c contracts ~/Documents/SmithCase/Contracts/*.pdf
./addpdf.py -c correspondence ~/Documents/SmithCase/Emails/*.pdf

# Verify
./lscol.py
```

---

## Duplicate Detection

Parabeagle tracks file SHA256 hashes. If you try to add a PDF that's already in the collection, it will be skipped automatically. This prevents accidentally processing the same file twice.

---

## Using with Claude Desktop or Other MCP Clients

Once your collections are loaded via the CLI tools, they're immediately available to any MCP client connected to Parabeagle. Use the `chroma_query_with_sources` tool to search your documents and get citations with full file paths for verification.

---

## Troubleshooting

**"No collections found"** - Make sure you've set an active directory with `./manage_dirs.py --set-active name`

**"Collection already exists"** - The collection name is taken. Use `./lscol.py` to see existing collections.

**Slow processing** - Embedding each chunk takes time. This is normal. Use `-v` flag to see progress.

**PDF not extracting text** - Some PDFs are scanned images without text layers. Parabeagle cannot process these.
