New feature:
Print sources when they are available.

Sources are the filenames of chunks retrieved from the vector DB.

Why? Printing the sources below LLM output gives the user the ability to verify 

Current algo:
- add methods to class `Conversation`
    - `add_sources(sources: list[str]) -> None` appends to a `self._sources` list on Conversation
    - `read_sources() -> list[str]` reads the sources, if they exist.  The list will be empty if no sources exist
    - `clear_sources() -> None` simply does `self._sources.clear()`
- in 
- `query_similar_chunks()` in `chat_ui.py`:
    - invoke `convo.add_sources` within