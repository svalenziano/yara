import os
import random
from pprint import pp
from collections.abc import Generator

from yara.config import env
from yara.services.chunk import Chunk, FileChunkBundle
from yara.db.pgvector import insert_chunks

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
        - push files to database (keep db connection open for entire process)

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

def _mock_vector() -> list[float]:
    return [random.random() for _ in env['VECTOR_DIMS']]

def _has_extension(
    filename: str, 
    extensions=['md', 'txt']
    ) -> bool:
    for extension in extensions:
        if filename.endswith(extension):
            return True
    return False

def _get_all_filepaths(
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
            if _has_extension(filename, extensions):
                found.append(os.path.join(dirpath, filename))
                if len(found) >= limit:
                    return found
        dirnames[:] = [d for d in dirnames if "." not in d]
    return found

def _chunkify_file(filename: str) -> FileChunkBundle:
    """
    Input = a single block of text
    Output = 🚨 Currently outputs one chunk per file
    
    **TODO IMPLEMENT CHUNKING LOGIC**
    USE LANCHAIN'S CHUNKER
    """
    file = FileChunkBundle(
        dir_path="tktk",
        filename=os.path.basename(filename),
        chunks=[],
        filesize=123,
        metadata={}
    )

    current_chunk = 0

    try:
        with open(filename, encoding="utf-8") as f:
            # TODO - IMPLEMENT ACTUAL CHUNKING!
            current_chunk += 1

            file.chunks.append(Chunk(
                chunk_text=f.read(), 
                embedding=_mock_vector(), 
                chunk_number=current_chunk,
            ))

    except IOError as e:
        e.filename = filename
        raise e

    return file

def _chunkify_files(
        filepaths: list[str]
    ) -> Generator[FileChunkBundle, None, None]:
    """
    Yields the text from each file.

    If any file reads raise an IOError, the paths are recorded
    And the error is re-raised at the end.
    """
    errors = []
    error_paths = []
    for path in filepaths:
        try:
            file_bundle = _chunkify_file(path)
            yield file_bundle
        except IOError as e:
            errors.append(e)
            error_paths.append(path)
    if error_paths:
        print("\nErrors while reading files:")
        for p in error_paths:
            print(p)
        raise IOError(errors)

def ingest_files_to_db(directory_path: str) -> None:
    """
    - Side effect: push file chunks and metadata to database
    - Algo:
        - paths = get all paths
        - file_bundles = chunkify_files(paths)
        - for each file bundle:
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
    paths = _get_all_filepaths(directory_path)

    bundles = _chunkify_files(paths)
    inserted_rows = insert_chunks(bundles)

    if inserted_rows != len(paths):
        raise Exception(f"❌ Expected {len(paths)} insertions, got {inserted_rows}")

    print(f"✅ INSERTED {inserted_rows} rows.")
            


if __name__ == "__main__":
    path = "/mnt/d/My Junk/Obsidian/SV_Personal_3/01_Intake/"
    ingest_files_to_db(path)



    