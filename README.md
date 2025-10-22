# Jenny

Jenny is a local-first orchestration playground composed of two FastAPI applications:

- `app.main`: the primary orchestrator service bundling agents, storage, and coordination logic.
- `app.mem0.server.main`: a lightweight memory microservice the orchestrator queries and updates.

Everything is designed to run locally using Docker Compose with Postgres (pgvector), Redis, and Neo4j.

## Project Structure

```
jenny/
  app/
    api/
    core/
    mem0/server/
    strands/agents/
```

Refer to the source files for detailed implementation notes.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose

## Quickstart

1. Copy the environment template and adjust if needed:
   ```bash
   cp .env.example .env
   ```
2. Configure your managed services (Neon, Upstash, Neo4j Aura) and ensure `.env` contains the correct credentials.
3. The main API is available at <http://localhost:8044/health> (FastAPI docs are available if run in debug mode) and Mem0 at <http://localhost:8081/docs>.

Docker images install dependencies every time they start to keep the setup simple. For longer term use consider authoring dedicated Dockerfiles.

## Running the Stack Locally

Even though Postgres, Redis, and Neo4j are now provided by remote services, you can still run the application processes locally.

1. Create and activate a virtual environment with Python 3.12.
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. Start the Mem0 microservice:
   ```bash
   uvicorn app.mem0.server.main:app --host 0.0.0.0 --port 8081
   ```
3. In a new terminal, start the main API (requires Postgres, Redis, Neo4j credentials configured in `.env`):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8044 --reload
   ```

Adjust connection strings in `.env` to point at your locally running databases if you are not using Docker.

## Data Stores

These services now live off the machine:

- **Postgres (Neon + pgvector)**: long-term semantic storage for Mem0 and task/profile tables.
- **Redis (Upstash)**: session cache and short-term context for multi-step flows.
- **Neo4j (Aura)**: graph logging of every interaction for exploration and advanced reasoning.

Ensure the corresponding connection strings are present in `.env` before starting the services.

## API Overview

- `GET /api/health`: confirms the main service can reach Mem0.
- `POST /api/orchestrate`: processes a prompt through the orchestrator and returns aggregated agent results.
- `POST /memory` (Mem0): records a memory payload.
- `POST /search` (Mem0): retrieves stored memories matching the supplied query.

## Telegram Bot

Set `TELEGRAM_BOT_TOKEN` in `.env`, install dependencies, and run:

```bash
python -m pip install -r requirements.txt
python run_telegram_bot.py
```

The bot uses the same orchestrator as the HTTP API and supports text, voice notes, and images.

## Development Notes

- Configuration lives in `app/core/config.py` and reads from `.env`.
- The orchestrator composes async agents defined in `app/strands/agents/`.
- Minimal docstrings and inline comments keep the code approachable while remaining concise.
