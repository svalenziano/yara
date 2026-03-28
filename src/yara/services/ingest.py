import os
from pprint import pp
from collections.abc import Generator

"""
ALGO
    - Given filepath, generate list of files that match the file extension filter
    - 
    - SQL:
        - get MAX project ID (if any chunks exist, otherwise use 0)
    - Ingest files using the next project_id
    - push to DB

FUNCTIONS:
    DO NOW:
        - postgres.py module
            - get_max_project_id()
            - add_chunk()
        - ingest_chunks(directory) -> str (result message)
            - get files from dir
            - for each file in files, add chunks to postgres
    DO LATER:
        - chunkify (see below)

"""


EXTENSIONS = ("md", "txt", "log", "json", "yaml", "toml", "mermaid", "excalidraw", "excalidraw.png", "excalidraw.svg")

def has_extension(
    filename: str, 
    extensions=['md', 'txt']
    ) -> bool:
    for extension in extensions:
        if filename.endswith(extension):
            return True
    return False

def get_all_filepaths(
        directory: str, 
        extensions:list[str]= ["md", "txt"], 
        limit=50
    ) -> list[str]:
    """
    Walk the directory recursively and return paths matching `extensions`, up to `limit`.
    """
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if has_extension(filename, extensions):
                found.append(os.path.join(dirpath, filename))
                if len(found) >= limit:
                    return found
        dirnames[:] = [d for d in dirnames if "." not in d]
    return found

def read_files(filepaths: list[str]) -> Generator[str, None, None]:
    """
    Yields the text from each file.

    If any file reads raise an IOError, the paths are recorded
    And the error is re-raised at the end.
    """
    errors = []
    error_paths = []
    for path in filepaths:
        try:
            with open(path, encoding="utf-8") as f:
                yield f.read()
        except IOError as e:
            errors.append(e)
            error_paths.append(path)
    if error_paths:
        print("\nErrors while reading files:")
        for p in error_paths:
            print(p)
        raise IOError(errors)

def chunkify(text: str) -> list[str]:
    """
    Input = a single block of text
    Output = list of chunks
    """
    # TODO IMPLEMENT CHUNKING LOGIC

    # USE LANCHAIN'S CHUNKER
    
    return [text]  # PLACEHOLDER: RETURN ONE-CHUNK FOR NOW 





if __name__ == "__main__":
    path = "/mnt/d/My Junk/Obsidian/SV_Personal_3/01_Intake/"
    pp(get_all_filepaths(path, limit=20))

    paths = get_all_filepaths(path, limit=20)

    for text in read_files(paths):
        print(text[:20])


    