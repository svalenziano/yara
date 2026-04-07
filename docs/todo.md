


## Done
### Layers of the cake (tentative architecture):
App logic:
- App: Main app logic
	- Data Ingestion
	- Data Querying
- OpenAI adapters - make calls to OpenAI
	- LLM
	- Embedding
- DB
	- pgvector - i/o with Postgres pgvector DB
- Config: loads environment vars

User interface:
- CLI: Invokes the application.  Orchestrates the CLI user experience

### Routing

Rough execution plan: Extracting router and handlers from main loop
```mermaid
flowchart
  a(User query)
  a --"(query:str, convo:dict)"--> b(Classifer)
  b --"(query:str, convo:dict)"--> c(Handler: lots of magic happens in here incl. retrieval, tool calls)
  c --"str: Last LLM message"--> d(render_assistant)
  d --"print LLM response to terminal"-->a
```


How do the python modules interact with each other?
```mermaid
flowchart LR                                                                        
    chat_ui -->|"classify(query, history)"| router                                  
    router -->|route string| chat_ui                                                
    chat_ui -->|"ROUTE_HANDLERS[route](query, conv)"| handlers                      
    handlers --> get_chunks                                                         
    handlers --> openai_client                                                      
    handlers --> ingest     
```
