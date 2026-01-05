### 1. Substack Keeper Extension to Parabeagle

I am the creator of Parabeagle, a fork of the Chroma MCP server that employs more accurate embedding and it offers compartments for collections of files, making it suitable for court case work and intel duties.

I would like to employ Parabeagle as a means to preserve Substack sites so I can better understand them without reading exhaustively.

If you don't have enough information to generate useful outputs, ask me questions until you have enough information.

---

## WHAT I'M THINKING ABOUT BUILDING

I want to enter a Substack URL including those with their own custom domain name, and have the system pull every post as a PDF, placing them in a folder named for the site. As they are preserved they should be added to a collection in Parabeagle. I think Parabeagle needs a dedicated Substack database, specifically for this content.

Once this is working I want to be able to use the resulting databases as knowledge bases in MindsDB, offering a web accessible front end that permits semantic understanding of one or more Substack sites based on the preserved content.

---

## BRIEF OUTPUT

### The Problem
This will permit the rapid understanding of the nature of a given Substack, as well as facilitating the locating of specific articles, with only a vague memory as a starting point.

I am concerned about the overall datamodel and its implications. If we do have a Substack database and each collected Substack is a collection, how would a collection be exported for use on another system? Perhaps the correct way to do this is a database per Substack, one collect containing the actual articles, and then a meta collection that contains only the metadata document, but which COULD be used by an analyst to attach additional data?

### Who It's For
- Primary user: me first, then Unix skilled OSINT analysts
- Their current workaround: unknown but presume similar to this, get content from sitemap.xml, have some way to index it.
- Why the workaround isn't good enough: Workaround is bespoke, often gets rebuilt from scratch when it's needed, I've never systematically done this.

### The Simplest Version
The prototype must accept a URL for a Substack and preserve all posts in a Parabeagle datatbase.

### Success Criteria
How will you know if this works? Not "people like it" but specific signals:
- [ ] System will have folder of PDF files with count that matches the sitemap.xml
- [ ] File names of PDFs will match the slug of the related article.
- [ ] Parabeagle will have a collection that has the same name as the Substack.
- [ ] I think Parabeagle needs a database called "Substack" specifically to handle the collected Substack sites.

### Must-Haves vs. Nice-to-Haves

**Must-haves (prototype is useless without these):**
- accept URL of Substack, get URLs for all articles via sitemap.xml
- turn URL into quality PDF using existing code
- Parabeagle must do a neat job of this from the start, having a Substack specific database, and then Substack collections within it.

**Nice-to-haves (add if time permits):**
- Date and time stamp of article publication would be handy metadata
- A collection metadata PDF that lists the contents of sitemap.xml, word count per articles, tags employed.
- Collection metadata PDF could have a one line summary per article.
- Perhaps a single database is inappropriate, a curator might want to package multiple Substacks and search them all at once.
- the metadata being accessible WITH the collection in the same interface is key, but there is no reason not to have a manifest.json with the same material available for other use.
- Annotations could be per file, but not per chunks in the file. Attaching a new file that contains a summary of one or more of the files that contributed to a given collection would be very useful, and implicitly could cover an entire collection, just by "include all files".

### The Build Plan

1. **First session (1-2 hours):** Build the Substack Keeper using Parabeagle and the existing bit of code that gets articles.
2. **Second session (if needed):** Add the code to create the collection metadata PDF and store it with the collection.
3. **Stop when:** Once we have the metadata PDF that reflects a summary of what was collected I need to think about how to make this available.

### One Sentence

This prototype lets OSINT analysts preserve a Substack site in its entirety as a Parabeagle collection instead of whatever manual, messy, scripted solution they currently use.

---
