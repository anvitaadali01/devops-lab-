# Docker Networking Demo

A small Flask REST API backed by MySQL and Redis. Docker Compose connects all three services to a custom bridge network; the API reaches MySQL at `mysql:3306` and Redis at `redis:6379` using their Compose service names.

## Project contents

- `app.py` — Flask health check and item API, MySQL schema initialization, Redis caching, and dependency retry loop.
- `Dockerfile` — builds a small Python image and runs the app as an unprivileged user.
- `docker-compose.yml` — defines Flask, MySQL, Redis, health checks, persistent MySQL storage, and the custom bridge network.
- `requirements.txt` — Python dependencies.
- `.env.example` — environment variable template; actual `.env` is ignored by Git and Docker build context.

## Requirements

- Docker Desktop with Docker Compose v2
- PowerShell (commands below are for Windows)

## Configure and start

1. Create a local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env`. Replace both password placeholders with strong local values. The Compose configuration requires `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, and `MYSQL_PASSWORD`; it will not start with these values missing. Do not commit `.env`.

3. Build and start all services:

   ```powershell
   docker compose up --build -d
   ```

   MySQL and Redis have container health checks, and Flask waits until both services respond before starting the API. The application also creates its `items` table if it does not already exist. Startup can take a minute on the first run while the images download and MySQL initializes.

4. Confirm service status and view logs if needed:

   ```powershell
   docker compose ps
   docker compose logs -f flask
   ```

   Press Ctrl+C to stop following logs; it does not stop the containers.

The API is published at `http://localhost:5000` by default. Set `APP_PORT` in `.env` to change the host port. The internal API port remains 5000.

## API

### Health and connectivity

`GET /health` checks a real MySQL query and Redis `PING`. It returns HTTP 200 when both checks pass and HTTP 503 otherwise.

```powershell
Invoke-RestMethod http://localhost:5000/health
```

Example response:

```json
{
  "status": "ok",
  "checks": {
    "mysql": true,
    "redis": true
  }
}
```

### List items

`GET /api/items` returns stored items. The response is cached in Redis for `CACHE_TTL_SECONDS` (60 seconds by default).

```powershell
Invoke-RestMethod http://localhost:5000/api/items
```

### Create an item

`POST /api/items` stores a named item in MySQL and invalidates the cached item list.

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:5000/api/items `
  -ContentType 'application/json' `
  -Body '{"name":"network demo"}'
```

A successful request returns HTTP 201 with the new item's `id` and `name`. A missing, blank, or overlong name returns HTTP 400.

## Smoke test

After the stack reports healthy, run the health request, create an item, then list items:

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/items -ContentType 'application/json' -Body '{"name":"smoke test"}'
Invoke-RestMethod http://localhost:5000/api/items
```

For automated service state and API startup checks, `docker compose ps` should show all three containers as healthy. The `/health` request verifies both backing service connections.

## Stop and clean up

Stop the containers while retaining MySQL data:

```powershell
docker compose down
```

To also permanently delete the MySQL data volume, use `docker compose down -v`.
