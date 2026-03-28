import os
from dotenv import load_dotenv
from typing import TypedDict


class Env(TypedDict):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PG_USER: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: str
    PG_DB_NAME: str
    VECTOR_DIMS:str


env: Env = {}  # type: ignore[typeddict-item]  # import this object into your module

# LOAD VARS FROM ENVIRONMENT
# Beware verbose logging, which may log your API keys
load_dotenv(override=True, verbose=False)

expected_env_vars = list(Env.__annotations__)

misses = []

for key in expected_env_vars:
    if key in env:
        raise ValueError(f"Key '{key}' was found in both your config.py and the environment.  It should only exist in one location.")
    found = os.getenv(key)
    if found != None:  # Keys with empty strings will follow this code path
        env[key] = found
    else:
        misses.append(key)        

if misses:
    raise Exception(f"Some env vars were not found: {", ".join(misses)}")
