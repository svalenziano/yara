# Arize Phoenix Observability Plan

## Goal

Add Arize Phoenix as a self-hosted Docker container to provide LLM/RAG observability for YARA. Phoenix captures OpenTelemetry traces for every LLM call, embedding generation, and vector retrieval, then visualizes them in a web UI.

---

## 1. Docker Compose — Add Phoenix Service

Add to `docker-compose.yml` alongside the existing `db` service:

```yaml
phoenix:
  image: arizephoenix/phoenix:latest
  ports:
    - 6006:6006   # Web UI + OTLP HTTP collector (/v1/traces)
    - 4317:4317   # OTLP gRPC collector
  volumes:
    - phoenix_data:/mnt/data
```

Add `phoenix_data` to the `volumes:` section.

Uses SQLite storage (default) — no extra Postgres needed for a dev/learning setup.

**Phoenix UI:** http://localhost:6006

---

## 2. Python Dependencies

Add to `pyproject.toml`:

```
arize-phoenix-otel
openinference-instrumentation-openai
```

`arize-phoenix-otel` pulls in `opentelemetry-sdk` and `opentelemetry-exporter-otlp` transitively.

---

## 3. Instrumentation Approach

Use `phoenix.otel.register()` with `auto_instrument=True` for a clean, robust setup.

### 3a. Initialize Tracing — `src/yara/main.py`

Set the environment variable (in `.env`):
```
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

Then in code:
```python
from phoenix.otel import register

tracer_provider = register(
    project_name="yara",
    auto_instrument=True,
)
```

`auto_instrument=True` discovers all installed `openinference-instrumentation-*` packages and activates them.

### 3b. Auto-Instrumented — `src/yara/services/openai_client.py`

No code changes needed. `OpenAIInstrumentor` patches the OpenAI SDK globally. All existing calls are traced automatically:

| Function | Traced As |
|----------|-----------|
| `classify_request()` | LLM span (responses.parse) |
| `enrich_query()` | LLM span (responses.create) |
| `simple_llm_call()` | LLM span (responses.create) |
| `generate_embeddings()` | Embedding span |
| `generate_single_embedding()` | Embedding span |

---

## 4. Files to Modify

| File | Change |
|------|--------|
| `docker-compose.yml` | Add `phoenix` service + volume |
| `pyproject.toml` | Add `arize-phoenix-otel`, `openinference-instrumentation-openai` |
| `src/yara/main.py` | Initialize tracing with `register()` |
| `.env` | Add `PHOENIX_COLLECTOR_ENDPOINT` |

---

## 5. Verification

1. `docker compose up -d` — confirm Phoenix starts and UI is accessible at http://localhost:6006
2. Run `python -m yara.main` and issue a query
3. Open Phoenix UI and verify:
   - LLM call spans (classify, enrich, response) with input/output content
   - Embedding spans with model and token counts
   - Retriever span with similarity search details
4. Check span hierarchy shows the full request flow

---

## 6. Future Enhancements

### Manual Retriever Span — `src/yara/services/get_chunks.py`

Add a custom span to trace vector retrieval separately from the auto-instrumented OpenAI calls:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def query_similar_chunks(...):
    with tracer.start_as_current_span("vector_search", attributes={
        "openinference.span.kind": "RETRIEVER",
        "input.value": query_text,
    }) as span:
        # existing similarity search logic
        ...
        span.set_attribute("retrieval.documents", len(results))
```
