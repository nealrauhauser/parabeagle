Parabeagle is a fork of [Chroma's Official MCP Server](https://github.com/chroma-core/chroma-mcp/) with modifications that are helpful for those of us who work on multiple court cases in parallel. This software is for small offices, the sort of environment where a paralegal is supporting a small number of attorneys. There is no team access, the Chroma database folders the system creates get passed manually in a fashion similar to a word processor document.

This software offers the following features:

1. Semantic chunking based on paragraphs, with provisions for court documents.
2. Multiple mutually exclusive data directories, compartmentalizing court case work.
3. 384 or 768 dimension embedding; be fast, or be very accurate.
4. Command line document tools suitable for batch loading.
5. An MCP search function that returns a bibliography of documents and full file paths.

An LLM is basically a stochastic parrot, and they will "hallucinate", which is a polite industry term to describe the fabrication of "facts" on the fly in order to make pleasing sentences and paragraphs. This sort of cognitive defect is simply unacceptable for intelligence or litigation work. This MCP server offers a function called chroma_query_with_sources, which permits the user to verify the LLM's statements by inspecting source documents. 


The Chroma MCP server's default chunking is to split documents into 1,000 character blocks. This software's command line loader looks for paragraphs in literature and it has some features meant to handle court documents. The default maximum chunk size is 3,000 characters. A very dense 8.5x11" page is just under 2,000 characters, so unless you're working on an Ayn Rand novel, your paragraphs will be kept whole for the sake of semantic search.


This software assumes you're going to run local embedding rather than using a paid API. You have a choice of embeddings - minilm-384 (fast), mpnet-768(accurate), bert-768 (tries to balance). Each collection can have its own embedding, documents in a collection must be the same. 

Note that this only apply to the CLI addpdf.py loader. The chroma_add_documents function in the server code is still just the 1k chunk 384 dimension default, so this has been DISABLED. If you were to use it to load a document over the top of a batch created collection, terrible things would happen.

The pdfstruct.py script evaluates a document in terms of paragraph size distribution. If you have enormous datasets there might be some advantage in tweaking the maximum chunk size.

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

To Do:

Right now the only way to move data between systems is to archive an entire data directory and share it. There really needs to be a function that exports a collection from a directory, and a companion function that will merge such an export into a different directory. If a paralegal evaluates a huge collection of files and then adds a hundred of them to a collection, it may be necessary to export and transfer it to the system the attorney(s) on the case are using.

There really should be a shared folders function, such that the creator/modifier of a database has full access, while the people who just need read access can see, but not change the databases. This should be tested with file sharing methods. I will do this with Dropbox, Google Drive, and Proton Drive. Open an issue if you need some other file sharing mechanism added and tested. Access control would be accomplished with an option in the Claude Desktop configuration file, something would denote if a given system were a writer, or just a reader.

Chroma's original deletion function depends on knowing the document(paragraph) you want to remove. If you've turned a sixty page court filing into many documents that's an impossible mess. When handling evidence or intel, it's not uncommon to decide to back out something you've received. There is a script to remove an entire PDF from a collection. The new chroma_query_with_sources provides a bibliography of file names at the end of its response, facilitating removal.

This will never be forensic software, but it does need more features in terms of the raw documents that are added to the databases. There should be a root folder with subdirectories for each case and the system should keep a SHA256 hash of each file in addition to the other metadata.