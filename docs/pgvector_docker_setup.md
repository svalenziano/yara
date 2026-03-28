
# pgvector Docker Setup

An alternative to installing Postgres + pgvector locally — run it in a Docker container instead.

## Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
services:
  db:
    image: pgvector/pgvector:pg17-bookworm
    environment:
      POSTGRES_PASSWORD: hannaboops
    ports:
      - "8888:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Port mapping

- `8888` — the port you connect to from your host machine
- `5432` — the port Postgres listens on inside the container (not directly accessible from the host)

Docker forwards `localhost:8888` → container port `5432`.

### Volume

The `pgdata` volume persists your database state between container restarts. Without it, all data is lost when the container stops.

## Common Commands

```bash
docker compose up -d      # start in background
docker compose down       # stop (data persists)
docker compose down -v    # stop and delete volume (wipes all data)
```

## Connecting to the Database

**psql:**
```bash
psql -h localhost -p 8888 -U postgres
```

**Python (psycopg2):**
```python
import psycopg2
conn = psycopg2.connect(host="localhost", port=8888, user="postgres", password="hannaboops")
```

**Connection string:**
```
postgresql://postgres:hannaboops@localhost:8888/postgres
```

The default superuser and database are both named `postgres`.

## Image Tags

Tags follow the pattern `pg<version>-<debian>`, e.g. `pg17-bookworm`.

- **bookworm** = Debian 12 (stable) — recommended
- **trixie** = Debian 13 (testing)
- The Debian version lives inside the container — your host OS doesn't matter.
