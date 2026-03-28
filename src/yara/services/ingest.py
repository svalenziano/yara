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
        - get_files(directory, extension_filter=["txt", "md"], limit=50) -> list[filepaths]
            - limit to 50 files for now, since we're testing the pipeline
        - read_files(files: list[filepaths]) -> yield one file text at a time
        - postgres.py module
            - get_max_project_id()
            - add_chunk()
        - ingest_chunks(directory) -> str (result message)
            - get files from dir
            - for each file in files, add chunk to postgres
    DO LATER:
        - generate_chunks(single_file) -> list[str]  # or should metadata be attached?

"""


EXTENSIONS = ("md", "txt", "log", "json", "yaml", "toml", "mermaid", "excalidraw", "excalidraw.png", "excalidraw.svg")

