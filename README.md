Parabeagle is a fork of [Chroma's Official MCP Server](https://github.com/chroma-core/chroma-mcp/) with modifications that are helpful for those of us who work on multiple court cases in parallel. This software is for small offices, the sort of environment where a paralegal is supporting a small number of attorneys. There is no team access, the Chroma database folders the system creates get passed manually in a fashion similar to a word processor document.

This software offers the following features:

1. Semantic chunking based on paragraphs, with provisions for court documents.
2. Multiple mutually exclusive data directories, compartmentalizing court case work.
3. Command line document tools suitable for batch loading.
4. An MCP search function that returns a bibliography of documents and full file paths.
5. Uses 768 dimension mpnet embeddings for best quality semantic search.
6. Cosine vector distance instead of L2, for MindsDB compatibility.
7. System keeps SHA256 of files it encounters in order to avoid the time of reprocessing a file it already has.

An LLM is basically a stochastic parrot, and they will "hallucinate", which is a polite industry term to describe the fabrication of "facts" on the fly in order to make pleasing sentences and paragraphs. This sort of cognitive defect is simply unacceptable for intelligence or litigation work. This MCP server offers a function called chroma_query_with_sources, which permits the user to verify the LLM's statements by inspecting source documents. 


The Chroma MCP server's default chunking is to split documents into 1,000 character blocks. This software's command line loader looks for paragraphs in literature and it has some features meant to handle court documents. The default maximum chunk size is 3,000 characters. A very dense 8.5x11" page is just under 2,000 characters, so unless you're working on an Ayn Rand novel, your paragraphs will be kept whole for the sake of semantic search.


This software assumes you're going to run local embedding rather than using a paid API. The prior embedding options are gone, we're just using mpnet-768, the slowest, but it's the best quality. Processing time for a clutch of short Substack posts turned to PDF was five to seven seconds each on a Mac with an M1 Pro processor.

Note that the only way to add PDFs to the system is using the CLI addpdf.py loader. The built in chroma_add_documents found in the original Chroma software is disabled - there's no provision to control where it adds documents, and in general this function gives the LLM creative license to make messes, while the command line tools are deterministic.

The pdfstruct.py script evaluates a document in terms of paragraph size distribution. If you have enormous datasets there might be some advantage in tweaking the maximum chunk size. This is more for me in development than anything a user would employ.

This is the configuration from a Mac running Parabeagle. The first folder should be set to the location where you cloned the repository. The second is the default Chroma database folder that is created the first time this server runs. If you use the multi-folder feature the system will create additional folders, each of which contains a fresh, empty Chroma database. The additional folder locations are stored in Chroma's Sqlite3 database, there is no need to have any --data-dir in this configuration beyond the default.
```
    "parabeagle": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/Users/yourname/work/gits/parabeagle",
        "parabeagle",
        "--client-type",
        "persistent",
        "--data-dir",
        "/Users/yourname/chroma/"
      ]
    },
```