"""
Ingest data from filesystem into Database
"""

import os
import random
from math import ceil
from pprint import pp
from collections.abc import Generator, Iterator, Iterable

from yara.config import env
from yara.types import FileBundle, Chunk
from yara.db.pgvector import insert_chunks, get_chunk_count, get_max_project_id
from yara.services.openai_embedding import generate_embeddings

MOCK = False  # not implemented
LIMIT: int | None = 500
VERBOSE = env['VERBOSE']
EXTENSIONS = ("md", "txt", "log", "json", "yaml", "toml", "mermaid", "excalidraw", "excalidraw.png", "excalidraw.svg")

def _mock_vector() -> list[float]:
    vector_dimensions = int(env['VECTOR_DIMS'])
    return [random.random() for _ in range(vector_dimensions)]

def _has_extension(
    filename: str, 
    extensions=['md', 'txt']
    ) -> bool:
    for extension in extensions:
        if filename.endswith("." + extension):
            return True
    return False

def _get_all_filepaths(
        directory: str, 
        extensions:list[str]= ["md", "txt"], 
        limit=LIMIT,
        verbose=VERBOSE,
    ) -> list[str]:
    """
    Walk the directory recursively and return paths matching `extensions`, up to `limit`.
    """
    keep_going = True

    if not os.path.isdir(directory):                                                       
      raise ValueError(f"Directory does not exist: {directory}")  
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(directory):
        if not keep_going:
            break
        for filename in filenames:
            if limit and len(found) >= limit:
                keep_going = False
                break
            if _has_extension(filename, extensions):
                found.append(os.path.join(dirpath, filename))

        dirnames[:] = [d for d in dirnames if "." not in d]
    if verbose: print(f"Found {len(found)} files.")
    return found

def _get_file_metadata(filename: str):
    # NOT IMPELMENTED
    return {"data": "this feature not yet implemented"}

def _chunk_text(text_to_chunk: str, max_characters= 1000) -> list[str]:
    """
    Fixed-size text chunking
    """
    chunked = []
    for i in range(0, len(text_to_chunk), max_characters):
        chunked.append(text_to_chunk[i:i + max_characters])
    return chunked

def _chunk_file(filename: str) -> list[str]:
    try:
        with open(filename, encoding="utf-8") as f:
            return _chunk_text(f.read(), 1000)

    except IOError as e:
        e.filename = filename
        raise e

def _bundle_file(filename: str, chunk=True) -> FileBundle:
    """
    Turn a filename into a FileBundle.
    """
    file = FileBundle(
        dir_path=os.path.dirname(filename),
        filename=os.path.basename(filename),
        chunks=_chunk_file(filename) if chunk else [],
        filesize=os.path.getsize(filename),
        metadata=_get_file_metadata(filename)
    )
    return file

def _bundle_files(
        filepaths: list[str]
    ) -> list[FileBundle]:
    """
    Convert filepaths into Bundles.  Texts are chunked as part of this step.

    If any file reads raise an IOError, the paths are recorded
    And the error is re-raised at the end.
    """
    errors = []
    error_paths = []
    bundles: list[FileBundle] = []

    for path in filepaths:
        try:
            bundles.append(_bundle_file(path))
        except IOError as e:
            errors.append(e)
            error_paths.append(path)
    if error_paths:
        print("\nIOErrors while reading files:")
        for p in error_paths:
            print(p)
        raise IOError(errors)
    return bundles
    
def _files_to_chunks(files: Iterable[FileBundle]) -> list[Chunk]:
    """
    Flatten FileBundles into a list of Chunks, for feeding to the Embedder
    """
    chunks = []

    for file in files:
        chunk_count = len(file.chunks)
        for idx, chunk in enumerate(file.chunks):
            chunks.append(
                Chunk(
                    chunk_text=chunk,
                    embedding=[],
                    chunk_number=idx + 1,
                    total_chunks=chunk_count,
                    dir_path=file.dir_path,
                    filename=file.filename,
                    filesize=file.filesize,
                    metadata=file.metadata,
                )
        )

    return chunks

   

def ingest_files_to_db(directory_path: str, batch_size=100, verbose=VERBOSE) -> None:
    """
    **TODO:** ensure you don't exceed the OpenAI 300k tokens per-request limit

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
    if verbose: print(f"\n⌛ Ingesting files...")

    paths = _get_all_filepaths(directory_path)
    batches = ceil(len(paths) / batch_size)

    if verbose: print(f"\nIngesting in {batches} batches.")

    project_id = get_max_project_id() + 1

    for batch in range(batches):
        if verbose: print(f"\nHandling batch {batch}")

        start = batch * batch_size
        batch_paths = paths[start: start + batch_size]

        bundles = _bundle_files(batch_paths)
        chunks = _files_to_chunks(bundles)
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [{'filename':chunk.filename, 'filepath':chunk.dir_path} for chunk in chunks]

        if verbose: print(f"  Chunk count = {len(texts)}")

        if MOCK:
            raise Exception("Not implemented")
        else:
            embeddings = generate_embeddings(texts, metadata)
            
        for embedding in embeddings:
            chunks[embedding.index].embedding = embedding.embedding

        # push chunks to the database
        inserted_rows = insert_chunks(chunks, project_id=project_id)

        if inserted_rows != len(chunks):
            raise Exception(f"  ❌ Expected {len(chunks)} insertions, got {inserted_rows}")

        if verbose: print(f"  ✅ INSERTED {inserted_rows} rows.")
            


if __name__ == "__main__":
    path = "/mnt/d/My Junk/Obsidian/SV_Personal_3/03 Work/"
    ingest_files_to_db(path, )
    print(f"\n📦 Total chunks in DB: {get_chunk_count()}")



    