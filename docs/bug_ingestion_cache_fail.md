## problems

Some files are being ingested on every ingestion, even when the files haven't changed.

### 1 - Trailing Slash
The SQL LIKE pattern in 


### 2 - Empty files
Empty files produce 0 chunks and are never inserted into the DB

Solution: Always skip empty files