import os
from pprint import pp
from collections.abc import Generator
from yara.services.chunk import Chunk, File

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
        - push file to database

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

def chunkify_files(filepaths: list[str]) -> Generator[str, None, None]:
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

def chunkify_file(filename: str) -> File:
    """
    Input = a single block of text
    Output = 🚨 Currently outputs one chunk per file
    
    TODO IMPLEMENT CHUNKING LOGIC
        # USE LANCHAIN'S CHUNKER
    """
    file = File(
        dir_path="tktk",
        filename=os.path.basename(filename),
        chunks=[],
        filesize=123,
        metadata={}
    )

    current_chunk = 0

    try:
        with open(path, encoding="utf-8") as f:
            # TODO - IMPLEMENT ACTUAL CHUNKING!
            current_chunk += 1

            File.chunks.append(Chunk(
                chunk_text=f.read(), 
                embedding=[1,2,3], 
                chunk_number=current_chunk,
            ))

    except IOError as e:
        e.filename = filename
        raise e

    return file


def push_file_to_db(filename: str) -> None:
    """
    - Input: filename
    - Side effect: push file chunks and metadata to database
    - Algo:
        
        - chunks = chunkify()
        - for each chunk:
            - insert_chunk (pgvector.py)
                - push to DB
                    filename
                    dir_path
                    chunk_text
                    embedding
                    chunk_number
                    total_chunks
                    filesize
                    metadata = {}
    """
    pass


if __name__ == "__main__":
    path = "/mnt/d/My Junk/Obsidian/SV_Personal_3/01_Intake/"
    # pp(get_all_filepaths(path, limit=20))

    paths = get_all_filepaths(path, limit=20)

    for path in paths:
        c = chunkify_file(path)
        pp(c)


    