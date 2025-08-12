This repo is a fork of [Chroma's Official MCP Server](https://github.com/chroma-core/chroma-mcp/)

There were a number of specific things I wanted that were not in the base.

1. My systems are M1 Macs and can handle more than the basic 384 dimension embedding.
2. Chunking needed to be made paragraph aware for some work I do.
3. Chunking needed to handle court documents in a sensible fashion.
4. A fast, deterministic means of adding documents was a must.
5. I need to produce multiple pre-embedded sets of documents for distribution to others.

Chroma's system supports a variety of storage methods, this software is only tested on local storage.

The assumed mode of use with this software is Claude Desktop or some other MCP host querying the system, but loading documents is done in batches via the command line. The internals of the server have been left original, except where changes were absolutely necessary.

There is a script that evaluates documents so you can set optimum chunk size. Run the script, look at the maximum paragraph size, and it's probably still a sensible number under 3,000 characters. I used to have a system called Disinfodrome that provided search services across hundreds of thousands of documents, so I need to see all the tuning knobs.

The MCP server's chunking remains the simplistic 1k character blocks. The command line loader is smart about paragraphs in literature and it tries to do the right things with court documents. There is no compatibility issue here, the details of how chunking was done don't matter for retrieval. You just want to avoid loading documents via the MCP server unless you're willing to take the hit on retrieval performance.

The scripts look for the storage path in $CHROMADIR and this can be overridden with the command line --data-dir option. I both use Chroma in production, as well as for creating bundles of pre-embedded documents for others to use.

To Do:

The document evaluation script really should have a histogram function, so we're not tweaking things endlessly over half a dozen very large paragraphs in some enormous file. If it's a perfect match 98% of the time performance will be acceptable.

There needs to be a method to create a tarball from a given collection and its metadata from Chroma's Sqlite3 database. There is a companion need to be able to import such a thing into an existing system.

Chroma's deletion function depends on knowing the document you want to remove. If you've turned a sixty page court filing into many paragraphs (documents) that's an impossible mess. When handling evidence or intel, it's not uncommon to decide to back out something you've receieved. Perhaps this is a keyword search with optional interactive delete. I will need to spend some time using the system on real world problems before this becomes clear.

