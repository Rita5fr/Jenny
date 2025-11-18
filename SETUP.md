# Jenny Complete Setup Guide

**🎉 100% Local Setup - No Cloud Services Required!**

This guide will help you set up Jenny with all services running locally on your machine using Docker.

## Prerequisites

- **Python 3.11 or higher**
- **Docker and Docker Compose** ([Install Docker](https://docs.docker.com/get-docker/))
- **OpenAI API key** ([Get API key](https://platform.openai.com/api-keys))

That's it! Everything else runs locally.

## Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
# Clone the repository (if not already done)
cd Jenny

# Install dependencies
pip install -r requirements.txt
```

This installs:
- FastAPI, Uvicorn (web framework)
- PostgreSQL, Redis, Neo4j drivers
- OpenAI client
- **strands-agents-tools** (50+ agent tools)
- Telegram bot framework
- And more...

### Step 2: Start Local Databases

Start PostgreSQL, Redis, and Neo4j with one command:

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL 16** with pgvector extension on port `5432`
- **Redis 7** on port `6379`
- **Neo4j 5 Community** on ports `7474` (HTTP) and `7687` (Bolt)

#### Verify Services Are Running

```bash
docker-compose ps
```

You should see:
```
NAME            IMAGE                     STATUS
jenny-postgres  ankane/pgvector:latest    Up (healthy)
jenny-redis     redis:7-alpine            Up (healthy)
jenny-neo4j     neo4j:5-community         Up (healthy)
```

#### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs postgres
docker-compose logs redis
docker-compose logs neo4j
```

### Step 3: Configure Environment

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your OpenAI API key:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Update the OpenAI API key:**
   ```bash
   # Required - get from https://platform.openai.com/api-keys
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   ```

4. **Database credentials (defaults work!):**
   The following are already configured in `.env.example`:
   ```bash
   # PostgreSQL (local)
   PGHOST=localhost
   PGPORT=5432
   PGDATABASE=jenny_db
   PGUSER=jenny
   PGPASSWORD=jenny123
   PGSSLMODE=disable

   # Redis (local)
   REDIS_URL=redis://localhost:6379

   # Neo4j (local)
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=jenny123
   ```

5. **Optional API keys** (for enhanced features):
   ```bash
   # For voice transcription and knowledge queries
   GEMINI_API_KEY=your-gemini-key

   # For advanced reasoning in recall agent
   DEEPSEEK_API_KEY=your-deepseek-key

   # For Telegram bot
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```

### Step 4: Start Jenny Services

#### Terminal 1: Mem0 Microservice

```bash
python -m uvicorn app.mem0.server.main:app --host 0.0.0.0 --port 8081
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8081
```

#### Terminal 2: Main Jenny Application

Open a **new terminal** and run:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8044
```

You should see:
```
INFO:     Started server process
INFO:     Postgres pool initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8044
```

#### Terminal 3 (Optional): Telegram Bot

Open a **third terminal** and run:
```bash
python app/bots/telegram_bot.py
```

### Step 5: Verify Installation

#### 5.1 Test Health Endpoint

```bash
curl http://localhost:8044/health
```

Expected response:
```json
{"ok":true}
```

#### 5.2 Test Memory Storage

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Remember that I love green tea"}'
```

Expected response includes:
```json
{
  "agent": "memory_agent",
  "reply": "Got it, I've saved that."
}
```

#### 5.3 Test Task Creation

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Remind me to buy groceries tomorrow"}'
```

#### 5.4 Test Tools Agent (NEW!)

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"list tools"}'
```

This shows all available tools from strands-agents-tools library!

#### 5.5 Run Test Suite

```bash
pytest tests/ -v
```

Expected: All 6 tests should pass ✅

### Step 6: Access Database Interfaces

#### PostgreSQL

```bash
# Using psql
docker exec -it jenny-postgres psql -U jenny -d jenny_db

# Check tables
\dt

# Check pgvector extension
\dx

# Exit
\q
```

#### Redis

```bash
# Access Redis CLI
docker exec -it jenny-redis redis-cli

# Test connection
> ping
PONG

# See stored sessions
> keys *

# Exit
> exit
```

#### Neo4j Browser

1. Open [http://localhost:7474](http://localhost:7474) in your browser
2. Login with:
   - **Username:** `neo4j`
   - **Password:** `jenny123`
3. Run a test query:
   ```cypher
   MATCH (n) RETURN n LIMIT 10
   ```

## Usage Examples

### Memory Management

```bash
# Save preferences
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"My favorite color is blue"}'

# Recall preferences
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"What do I like?"}'
```

### Task Management

```bash
# Create task
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"Remind me to call mom tomorrow"}'

# List tasks
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"List my tasks"}'
```

### Using Advanced Tools

```bash
# List available tools
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"what tools do you have?"}'

# Web search (if strands-agents-tools is installed)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"web search for Python tutorials"}'
```

## Managing Services

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart postgres
docker-compose restart redis
docker-compose restart neo4j

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop and remove data (WARNING: deletes all data!)
docker-compose down -v
```

### Application Commands

```bash
# Start Mem0 service
python -m uvicorn app.mem0.server.main:app --port 8081

# Start main app
python -m uvicorn app.main:app --port 8044

# Start with auto-reload (development)
python -m uvicorn app.main:app --port 8044 --reload

# Start Telegram bot
python app/bots/telegram_bot.py
```

## Troubleshooting

### Issue: "Failed to initialize Postgres pool"

**Cause:** PostgreSQL not running or wrong credentials

**Solutions:**
1. Check if PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. View PostgreSQL logs:
   ```bash
   docker-compose logs postgres
   ```

3. Restart PostgreSQL:
   ```bash
   docker-compose restart postgres
   ```

4. Verify credentials in `.env` match `docker-compose.yml`:
   - PGUSER=jenny
   - PGPASSWORD=jenny123
   - PGDATABASE=jenny_db

### Issue: "Redis connection refused"

**Solutions:**
1. Check if Redis is running:
   ```bash
   docker-compose ps redis
   ```

2. Test Redis connection:
   ```bash
   docker exec -it jenny-redis redis-cli ping
   ```

3. Restart Redis:
   ```bash
   docker-compose restart redis
   ```

### Issue: "Neo4j connection failed"

**Solutions:**
1. Wait 30 seconds after starting (Neo4j takes time to initialize)

2. Check Neo4j logs:
   ```bash
   docker-compose logs neo4j
   ```

3. Verify Neo4j is accessible:
   - Open http://localhost:7474
   - Login with neo4j/jenny123

4. Restart Neo4j:
   ```bash
   docker-compose restart neo4j
   ```

### Issue: "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### Issue: "OpenAI API key not found"

**Solutions:**
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-your-key
   ```
3. Restart the application

### Issue: Port Already in Use

**Solution:**
```bash
# Find process using port
lsof -i :8044  # for main app
lsof -i :8081  # for Mem0
lsof -i :5432  # for PostgreSQL

# Kill the process
kill -9 <PID>

# Or change port in command
python -m uvicorn app.main:app --port 8045
```

## Default Ports

| Service | Port | Access |
|---------|------|--------|
| Main App | 8044 | http://localhost:8044 |
| Mem0 Service | 8081 | http://localhost:8081 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| Neo4j Browser | 7474 | http://localhost:7474 |
| Neo4j Bolt | 7687 | bolt://localhost:7687 |

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| PostgreSQL | jenny | jenny123 |
| Redis | (none) | (none) |
| Neo4j | neo4j | jenny123 |

## Data Persistence

All data is persisted in Docker volumes:
- `postgres-data` - PostgreSQL database files
- `redis-data` - Redis append-only file
- `neo4j-data` - Neo4j graph database
- `neo4j-logs` - Neo4j log files

To backup:
```bash
docker-compose down
docker run --rm -v jenny_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Advanced Configuration

### Change Database Passwords

1. Update `docker-compose.yml`:
   ```yaml
   environment:
     - POSTGRES_PASSWORD=your-new-password
     - NEO4J_AUTH=neo4j/your-new-password
   ```

2. Update `.env`:
   ```bash
   PGPASSWORD=your-new-password
   NEO4J_PASSWORD=your-new-password
   ```

3. Restart:
   ```bash
   docker-compose down -v  # WARNING: Deletes data!
   docker-compose up -d
   ```

### Enable Strands Tools Optional Features

Install additional tools:
```bash
pip install strands-agents-tools[mem0_memory,use_browser,rss,use_computer]
```

## Production Deployment

For production:

1. **Change all default passwords**
2. **Enable SSL/TLS** for database connections
3. **Set up firewall rules** to restrict access
4. **Configure backups** for all databases
5. **Add monitoring** (Sentry, Prometheus, etc.)
6. **Use environment secrets** instead of `.env` file
7. **Consider managed services** for databases

## Getting Help

- **Documentation:** See [README.md](README.md) for API docs
- **Issues:** Report bugs on GitHub
- **Logs:** Check `docker-compose logs` for errors

## Quick Reference

```bash
# Complete setup from scratch
git clone <repo>
cd Jenny
pip install -r requirements.txt
docker-compose up -d
cp .env.example .env
# Edit .env with OpenAI key
python -m uvicorn app.mem0.server.main:app --port 8081 &
python -m uvicorn app.main:app --port 8044
curl http://localhost:8044/health

# Stop everything
docker-compose down
pkill -f uvicorn
```

Congratulations! Your Jenny AI assistant is now running locally! 🎉
