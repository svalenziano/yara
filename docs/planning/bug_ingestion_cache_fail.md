## problems

Some files are being ingested on every ingestion, even when the files haven't changed.

### 1 - SQL Comparison?
I'm not sure, but the bug might have something to do with files that are located in the root directory of the ingestion folder.  Ignoring this bug for now because the consequences seem to be ... pretty inconsequential.


### 2 - Empty files
Empty files produce 0 chunks and are never inserted into the DB

Solution: Always skip empty files.

Fixed.