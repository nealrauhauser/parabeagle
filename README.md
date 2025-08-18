This repo is a fork of [Chroma's Official MCP Server](https://github.com/chroma-core/chroma-mcp/)

This software offers the following features:

1. Semantic chunking based on paragraphs, with provisions for court documents.
2. Multiple mutually exclusive data directories, suitable for court case work.
3. User configurable 384 or 768 dimension embedding; go fast, or be really accurate.
4. Command line document tools suitable for batch loading.
5. An MCP search function that returns a bibliography of documents and their file paths.

An LLM is basically a stochastic parrot, and they will "hallucinate", which is a polite industry term to describe the fabrication of "facts" on the fly in order to make pleasing sentences and paragraphs. This sort of cognitive defect is simply unacceptable for intelligence or litigation work. This MCP server offers a function called chroma_query_with_sources, which permits the user to verify the LLM's statements by inspecting source documents. 


Chroma's default chunking is to split documents into 1,000 character blocks. This software's command line loader looks for paragraphs in literature and it has some features meant to handle court documents. The default maximum chunk size is 3,000 characters. A very dense 8.5x11" page is just under 2,000 characters, so unless you're working on an Ayn Rand novel, your paragraphs will be kept whole for the sake of semantic search.

This software assumes you're going to run local embedding rather than using a paid API. You have a choice of embeddings - minilm-384 (fast), mpnet-768(accurate), bert-768 (tries to balance). Each collection can have its own embedding, documents in a collection must be the same. 

Note that this only apply to the CLI addpdf.py loader. The chroma_add_documents function in the server code is still just the 1k chunk 384 dimension default, so this has been DISABLED. If you were to use it to load a document over the top of a batch created collection, terrible things would happen.

The pdfstruct.py script evaluates a document in terms of paragraph size distribution. If you have enormous datasets there might be some advantage in tweaking the maximum chunk size.

To Do:

Right now the only way to move data between systems is to archive an entire data directory and share it. There really needs to be a function that exports a collection from a directory, and a companion function that will merge such an export into a different directory. If your paralegal evaluates a huge collection of documents and adds a hundred to a collection, it will be necessary to be able to export that work and transfer it to the system the attorney(s) on the case are using.


Chroma's original deletion function depends on knowing the document you want to remove. If you've turned a sixty page court filing into many paragraphs (documents) that's an impossible mess. When handling evidence or intel, it's not uncommon to decide to back out something you've received. There is now a script to remove an entire PDF from a collection. The new chroma_query_with_sources provides a bibliography of file names at the end of its response, facilitating removal.