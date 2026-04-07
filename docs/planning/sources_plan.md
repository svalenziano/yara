## New feature:
Print sources when they are available.

Sources are the filenames of chunks retrieved from the vector DB.

Why? Printing the sources below LLM output gives the user the ability to verify 

## Current algo:
- add attributes & methods to class `Conversation`
    - `self._sources: list[SimilarChunk]`
    - `add_sources(sources: list[SimilarChunk]) -> None` 
        - ONLY WORKS when `self._sources` is empty.  Throws error if the list isn't empty.  This is to protect against accidentally adding sources without first clearing them.
        - appends to a `self._sources` list on Conversation
        - Keep in mind: there may be multiple chunks from the same file
    
    - `read_sources() -> list[SimilarChunk]` 
        - reads the sources, if they exist.  The list will be empty if no sources exist
    - `clear_sources() -> None` simply does `self._sources.clear()`
- in `rag_request()` in `handlers.py`:
    - invoke `conversation.add_sources( ... )` 
- in `chat_ui.py`:
    - `sources_panel(sources: list[SimilarChunk]) -> Panel`:
        - chunks are deduplicated - only one chunk from each filepath + filename combo is kept
        - order the combined filepath + filename alphabetically, as they'd appear in the filesystem
        - prints the filepath and filename.  Filepath is a faded color while filename is `bright_black`
    - check for sources, and if they exist invoke `sources_panel()` to print them to the console in a panel that sits BELOW the assistant panel, then `conversation.clear_sources()`