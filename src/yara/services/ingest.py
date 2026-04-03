"""
Ingest data from filesystem into Database
"""

import logging
import os
import random
from collections.abc import Iterable
from math import ceil

from yara.config import env
from yara.db.pgvector import (
    delete_chunks_for_file,
    get_chunk_count,
    get_ingested_files,
    get_or_create_project,
    insert_chunks,
    update_project_last_ingested,
)
from yara.services.openai_client import generate_embeddings
from yara.types import Chunk, FileBundle

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


MOCK = False  # not implemented
LIMIT: int | None = 400
VERBOSE = env["VERBOSE"]
# EXTENSIONS = (
#     "md",
#     "txt",
#     "log",
#     "json",
#     "yaml",
#     "toml",
#     "mermaid",
#     "excalidraw",
#     "excalidraw.png",
#     "excalidraw.svg",
# )


def _mock_vector() -> list[float]:
    vector_dimensions = int(env["VECTOR_DIMS"])
    return [random.random() for _ in range(vector_dimensions)]


def _has_extension(filename: str, extensions=["md", "txt"]) -> bool:
    for extension in extensions:
        if filename.endswith("." + extension):
            return True
    return False


def _get_all_filepaths(
    directory: str,
    extensions: list[str] = ["md", "txt"],
    limit=LIMIT,
) -> list[str]:
    """
    Walk the directory recursively and return paths
    matching `extensions`, up to `limit`.
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
    logger.debug("Found %d files in %s", len(found), directory)
    return found


def _get_file_metadata(filename: str):
    # NOT IMPELMENTED
    return {"data": "this feature not yet implemented"}


def _chunk_text(text_to_chunk: str, max_characters=1000) -> list[str]:
    """
    Fixed-size text chunking
    """
    chunked = []
    for i in range(0, len(text_to_chunk), max_characters):
        chunked.append(text_to_chunk[i : i + max_characters])
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
        metadata=_get_file_metadata(filename),
    )
    return file


def _bundle_files(filepaths: list[str]) -> list[FileBundle]:
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
        for p in error_paths:
            logger.warning("IOError reading file: %s", p)
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


def purge_stale_files(directory_path: str, project_id: int, purge_modified: bool = True) -> int:
    """
    Deletes chunks from the DB for files that no longer exist on disk,
    or whose filesize has changed (when purge_modified=True).
    Returns count of purged files.
    """
    ingested = get_ingested_files(directory_path, project_id)
    to_purge = []
    for dir_path, filename, filesize in ingested:
        full_path = os.path.join(dir_path, filename)
        if not os.path.isfile(full_path):
            to_purge.append((dir_path, filename, "stale"))
        elif purge_modified and os.path.getsize(full_path) != filesize:
            to_purge.append((dir_path, filename, "modified"))

    for dir_path, filename, reason in to_purge:
        logger.debug("Purging %s/%s (reason: %s)", dir_path, filename, reason)
        delete_chunks_for_file(dir_path, filename, project_id)

    stale = sum(1 for *_, r in to_purge if r == "stale")
    modified = sum(1 for *_, r in to_purge if r == "modified")
    logger.info("Purge complete: %d stale, %d modified", stale, modified)
    return len(to_purge)


def _filter_already_ingested(
    paths: list[str], ingested: set[tuple[str, str, int]]
) -> list[str]:
    """
    Returns only paths not already present in the DB with the same filesize.
    """
    filtered = []
    for path in paths:
        dir_path = os.path.dirname(path)
        filename = os.path.basename(path)
        filesize = os.path.getsize(path)
        if filesize < 1:
            logger.debug("Skipping empty file: %s/%s", dir_path, filename)
        elif (dir_path, filename, filesize) in ingested:
            logger.debug("Skipping already-ingested: %s/%s", dir_path, filename)
        else:
            filtered.append(path)
            logger.info("Queued for ingestion: %s/%s", dir_path, filename)
    skipped = len(paths) - len(filtered)
    logger.info("Skip complete: %d unchanged, %d to ingest", skipped, len(filtered))
    return filtered


def ingest_files_to_db(directory_path: str, project_id: int, batch_size=100) -> None:
    """
    Chunk and ingest files into the Vector Database
    """
    logger.info("Starting ingestion for %s", directory_path)

    paths = _get_all_filepaths(directory_path)
    logger.info("Found %d files", len(paths))

    purge_stale_files(directory_path, project_id, purge_modified=True)
    ingested = get_ingested_files(directory_path, project_id)
    paths = _filter_already_ingested(paths, ingested)

    batches = ceil(len(paths) / batch_size) if paths else 0
    logger.info("Ingesting in %d batch(es)", batches)

    total_inserted = 0

    for batch in range(batches):
        start = batch * batch_size
        batch_paths = paths[start : start + batch_size]

        bundles = _bundle_files(batch_paths)
        chunks = _files_to_chunks(bundles)
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [
            {"filename": chunk.filename, "filepath": chunk.dir_path} for chunk in chunks
        ]

        logger.debug("Batch %d/%d — %d chunks", batch + 1, batches, len(chunks))

        embeddings = generate_embeddings(texts, metadata)

        for embedding in embeddings:
            chunks[embedding.index].embedding = embedding.embedding

        inserted_rows = insert_chunks(chunks, project_id=project_id)

        if inserted_rows != len(chunks):
            raise Exception(f"Expected {len(chunks)} insertions, got {inserted_rows}")

        total_inserted += inserted_rows
        logger.info(
            "Inserted %d chunks (batch %d/%d)", inserted_rows, batch + 1, batches
        )

    logger.info(
        "Ingestion complete: %d files, %d chunks inserted", len(paths), total_inserted
    )
    update_project_last_ingested(project_id)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("yara.log"),
            logging.StreamHandler(),
        ],
    )

    for project_name, path in [
        ("software","/mnt/d/My Junk/Obsidian/SV_Personal_3/03 Work/0/Software-Details"),
        ("food", "/mnt/d/My Junk/Obsidian/SV_Personal_3/02_Personal/Recipes/"),
    ]:
        logger.info("🟢 Let's do this!")
        proj_id = get_or_create_project(project_name, path)
        ingest_files_to_db(path, proj_id)
        logger.info("🟢 Done! Total chunks in DB: %d", get_chunk_count())
