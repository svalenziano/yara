import os
import random
from pprint import pp
from collections.abc import Generator

from yara.config import env
from yara.services.chunk import Chunk, FileChunkBundle
from yara.db.pgvector import insert_chunks, get_chunk_count

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

LIMIT: int | None = 50
EXTENSIONS = ("md", "txt", "log", "json", "yaml", "toml", "mermaid", "excalidraw", "excalidraw.png", "excalidraw.svg")

def _mock_vector() -> list[float]:
    vector_dimensions = int(env['VECTOR_DIMS'])
    return [random.random() for _ in range(vector_dimensions)]

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
        limit=LIMIT,
        verbose=True,
    ) -> list[str]:
    """
    Walk the directory recursively and return paths matching `extensions`, up to `limit`.
    """
    if not os.path.isdir(directory):                                                       
      raise ValueError(f"Directory does not exist: {directory}")  
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if limit and len(found) >= limit:
                break
            if _has_extension(filename, extensions):
                found.append(os.path.join(dirpath, filename))

        dirnames[:] = [d for d in dirnames if "." not in d]
    if verbose: print(f"Found {len(found)} files.")
    return found

def _get_file_metadata(filename: str):
    # NOT IMPELMENTED
    return {"data": "this feature not yet implemented"}

def _chunkify_file(filename: str) -> FileChunkBundle:
    """
    Output = 🚨 Currently outputs one chunk per file
    
    **TODO IMPLEMENT CHUNKING LOGIC**
    USE LANCHAIN'S CHUNKER
    """
    file = FileChunkBundle(
        dir_path=os.path.dirname(filename),
        filename=os.path.basename(filename),
        chunks=[],
        filesize=os.path.getsize(filename),
        metadata=_get_file_metadata(filename)
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
    path = "/mnt/d/My Junk/Obsidian/SV_Personal_3/03 Work/"
    ingest_files_to_db(path)
    print(f"📦 Total chunk count: {get_chunk_count()}")



    