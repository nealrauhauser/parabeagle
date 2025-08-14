This repo is a fork of [Chroma's Official MCP Server](https://github.com/chroma-core/chroma-mcp/)

There were a number of specific things I wanted that were not in the base.

1. My systems are M1 Macs and can handle more than the basic 384 dimension embedding.
2. Chunking needed to be made paragraph aware for some work I do.
3. Chunking needed to handle court documents in a sensible fashion.
4. A fast, deterministic means of adding documents was a must, no LLM convulsions.
5. I need to produce multiple pre-embedded sets of documents for distribution to others.

Chroma's system supports a variety of storage methods, this software is only tested on local storage.

The assumed mode of use with this software is Claude Desktop or some other MCP host querying the system, but loading documents is done in batches via the command line. The internals of the server support higher dimensional embedding and its begun to sprout new features.

There is a script that evaluates documents so you can set optimum chunk size. Run the script, look at the maximum paragraph size, and it's probably still a sensible number under 3,000 characters. I used to have a website called Disinfodrome that provided search services across hundreds of thousands of documents, so I need to see all the tuning knobs for the sake of large batches.

The MCP server's internal chunking remains the simplistic 1k character blocks. The command line loader is smart about paragraphs in literature and it tries to do the right things with court documents. There is no compatibility issue here, the details of how chunking was done don't matter for retrieval. There is a separate script for some advanced notions on chunking, but it's starting to feel unnecessarily complex.

The scripts look for the storage path in $CHROMADIR and this can be overridden with the command line --data-dir option. I both use Chroma in production, as well as for creating bundles of pre-embedded documents for others to use.

To Do:

There needs to be a method to create a tarball from one or more given collections and their metadata from Chroma's Sqlite3 database. There is a companion need to be able to import such a thing into an existing system.

There is also a need for the system to support more than one folder, which will contain one or more collections of documents. One use case here is court work - if I have two similar cases I certainly don't want them merged. The folder switching should be available within the MCP server, rather than the current method which requires shutting down the MCP client and modifying an environment variable.

Chroma's original deletion function depends on knowing the document you want to remove. If you've turned a sixty page court filing into many paragraphs (documents) that's an impossible mess. When handling evidence or intel, it's not uncommon to decide to back out something you've received. There is now a script to remove an entire PDF from a collection and the new chroma_query_with_sources provides a bibliography of file names at the end of its response. This obviously needs polishing but it's a start.

