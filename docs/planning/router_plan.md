# Plan: Finish `classify_request()` and wire up `router()`

## Context

The routing system is stubbed out: `classify_request()` always returns `possible_options[0]` and `router()` always returns `handlers.rag_request`. The goal is to use OpenAI structured output to make an actual routing decision based on the conversation and current query, then return the correct handler callable.

---

## Files to Modify

- `src/yara/services/openai_client.py` — implement `classify_request()`
- `src/yara/services/router.py` — call `classify_request()` instead of hardcoding

---

## Implementation

### 1. `classify_request()` in `openai_client.py`

**Add imports:**
```python
from enum import Enum
from pydantic import BaseModel
```

**Update signature** to accept `query`:
```python
def classify_request(
    conversation: Conversation, possible_options: list[Callable], query: str = ""
) -> Callable:
```

**Body** (replace the `print(options_for_llm); return possible_options[0]` stub):

1. Build `options_for_llm` (already done).
2. Build a dynamic `Enum` from route names so the LLM is forced to pick a valid option:
   ```python
   RouteEnum = Enum("RouteEnum", {opt["route_name"]: opt["route_name"] for opt in options_for_llm})
   ```
3. Define a Pydantic model inside the function:
   ```python
   class RoutingDecision(BaseModel):
       route_name: RouteEnum
   ```
4. Build a routing prompt that lists routes and includes the current query:
   ```python
   routes_text = "\n".join(
       f"- {opt['route_name']}: {opt['route_description']}"
       for opt in options_for_llm
   )
   routing_prompt = (
       "Based on the conversation and the user's latest message and the convseration, "
       "select the most appropriate route.\n\n"
       f"User's latest message: {query}\n\n"
       f"Available routes:\n{routes_text}"
   )
   ```
5. Call `client.responses.parse()` using `get_augmented_entries()`:
   ```python
   augmented = conversation.get_augmented_entries(routing_prompt)
   response = client.responses.parse(
       model=MODELS["fast"],
       input=augmented,
       text_format=RoutingDecision,
       temperature=0,
   )
   chosen_name = response.output_parsed.route_name.value
   ```
6. Match back to the callable and return it:
   ```python
   for option in possible_options:
       if option.__name__ == chosen_name:
           return option
   return possible_options[0]  # fallback (should not happen)
   ```

### 2. `router()` in `router.py`

Replace the TODO block:
```python
def router(query: str, conversation: Conversation) -> Callable:
    if len(conversation) <= 3:  # Conversation has just begun
        logger.info("routing to rag_request (conversation start)")
        return handlers.rag_request

    chosen = classify_request(conversation, ROUTES, query)
    logger.info("routing to %s", chosen.__name__)
    return chosen
```

Also update the `__main__` block to pass a query:
```python
classified = classify_request(c, ROUTES, query="What documents do I have that explain Arduino?")
```

---

## Verification

1. Run the app: `python -m yara.main`
2. Ask an initial question (should route to `rag_request`)
3. Ask a follow-up question on the same topic (should route to `simple_request`)
4. Ask about something unrelated (should route to `new_topic`)
5. Run `router.py` directly: `python -m yara.services.router` — should print a route name instead of the stub list
