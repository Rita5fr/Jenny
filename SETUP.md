# Jenny Setup Guide

This guide will help you set up Jenny with:
- **Postgres**: Supabase (cloud)
- **Redis**: Local (via Docker)
- **Neo4j**: Local (via Docker)

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Supabase account (free tier available)
- OpenAI API key

## Step 1: Install Dependencies

```bash
# Clone the repository (if not already done)
cd Jenny

# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Set Up Supabase (Postgres)

### 2.1 Create Supabase Project

1. Go to [https://app.supabase.com/](https://app.supabase.com/)
2. Sign up or log in
3. Click **"New Project"**
4. Fill in:
   - **Name**: Jenny (or any name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is sufficient
5. Click **"Create new project"** and wait 2-3 minutes

### 2.2 Get Connection Details

1. In your Supabase project, go to **Settings** → **Database**
2. Scroll to **Connection string** section
3. Select **"URI"** mode
4. You'll see something like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abc123xyz.supabase.co:5432/postgres
   ```

5. Extract the values:
   - **PGHOST**: `db.abc123xyz.supabase.co` (the part after `@` and before `:5432`)
   - **PGPORT**: `5432`
   - **PGDATABASE**: `postgres`
   - **PGUSER**: `postgres`
   - **PGPASSWORD**: Your password from step 2.1

### 2.3 Enable pgvector Extension

For memory storage to work, enable the pgvector extension:

1. In Supabase, go to **Database** → **Extensions**
2. Search for **"vector"** or **"pgvector"**
3. Enable the extension

Alternatively, run this SQL in the **SQL Editor**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Step 3: Start Local Services (Redis & Neo4j)

### Option A: Using Docker Compose (Recommended)

```bash
# Start Redis and Neo4j in the background
docker-compose up -d

# Verify services are running
docker-compose ps

# You should see:
# - jenny-redis   (port 6379)
# - jenny-neo4j   (ports 7474, 7687)
```

**Access Neo4j Browser**: Open [http://localhost:7474](http://localhost:7474)
- Username: `neo4j`
- Password: `jenny123`

### Option B: Manual Installation

#### Install Redis

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Windows:**
Download from [https://redis.io/download](https://redis.io/download) or use WSL2.

#### Install Neo4j

**Neo4j Desktop (All platforms):**
1. Download from [https://neo4j.com/download/](https://neo4j.com/download/)
2. Install and create a new database
3. Set password (e.g., `jenny123`)
4. Start the database

**Docker (Quick):**
```bash
docker run -d \
  --name jenny-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/jenny123 \
  neo4j:5-community
```

## Step 4: Configure Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Update these required fields:**

   ```bash
   # OpenAI API Key (required)
   OPENAI_API_KEY=sk-proj-your-actual-key-here

   # Supabase Postgres (from Step 2.2)
   PGHOST=db.abc123xyz.supabase.co
   PGPORT=5432
   PGDATABASE=postgres
   PGUSER=postgres
   PGPASSWORD=your-supabase-password
   PGSSLMODE=require

   # Local Redis (default if using docker-compose)
   REDIS_URL=redis://localhost:6379

   # Local Neo4j (default if using docker-compose)
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=jenny123
   ```

4. **Optional: Add API keys for enhanced features:**
   ```bash
   # For voice transcription and knowledge queries
   GEMINI_API_KEY=your-gemini-key

   # For advanced reasoning in recall agent
   DEEPSEEK_API_KEY=your-deepseek-key

   # For Telegram bot
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```

## Step 5: Start Jenny Services

### 5.1 Start Mem0 Microservice

Open a terminal and run:
```bash
python -m uvicorn app.mem0.server.main:app --host 0.0.0.0 --port 8081
```

Keep this terminal open. You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8081
```

### 5.2 Start Main Jenny Application

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

### 5.3 (Optional) Start Telegram Bot

Open a **third terminal** and run:
```bash
python app/bots/telegram_bot.py
```

## Step 6: Verify Installation

### 6.1 Test Health Endpoint

```bash
curl http://localhost:8044/health
```

Expected response:
```json
{"ok":true}
```

### 6.2 Test Memory Storage

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Remember that I love green tea"}'
```

Expected response:
```json
{
  "agent": "memory_agent",
  "response": {...},
  "reply": "Got it, I've saved that."
}
```

### 6.3 Test Task Creation

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Remind me to buy groceries tomorrow"}'
```

### 6.4 Run Test Suite

```bash
pytest tests/ -v
```

Expected: All 6 tests should pass.

## Step 7: Verify Database Connections

### Check Supabase Tables

1. Go to Supabase → **Table Editor**
2. You should see tables created by Jenny:
   - `jenny_tasks` - for task management
   - Other tables created by Mem0 service

### Check Redis

```bash
# If using docker-compose
docker exec -it jenny-redis redis-cli
> ping
PONG
> keys *
(shows session keys if any)
> exit
```

### Check Neo4j

1. Open [http://localhost:7474](http://localhost:7474)
2. Login with `neo4j` / `jenny123`
3. Run query:
   ```cypher
   MATCH (n) RETURN n LIMIT 10
   ```
4. You should see interaction nodes if you've used the app

## Troubleshooting

### Issue: "Failed to initialize Postgres pool"

**Solution:**
- Verify Supabase connection details in `.env`
- Check if your IP is whitelisted in Supabase (Settings → Database → Connection Pooling)
- Ensure `PGSSLMODE=require` is set
- Test connection:
  ```bash
  psql "postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres?sslmode=require"
  ```

### Issue: "Redis connection refused"

**Solution:**
- If using Docker: `docker-compose ps` (check if redis is running)
- If using Docker: `docker-compose logs redis` (check logs)
- If manual install: `redis-cli ping` (should return PONG)
- Check `REDIS_URL` in `.env` is `redis://localhost:6379`

### Issue: "Neo4j connection failed"

**Solution:**
- If using Docker: `docker-compose logs neo4j`
- Wait 30 seconds after starting (Neo4j takes time to initialize)
- Verify credentials: `neo4j` / `jenny123`
- Check [http://localhost:7474](http://localhost:7474) is accessible
- Ensure `NEO4J_URI=neo4j://localhost:7687` (not `neo4j+s://`)

### Issue: "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### Issue: "OpenAI API key not found"

**Solution:**
- Get API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Add to `.env`: `OPENAI_API_KEY=sk-proj-...`

## Managing Services

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### Stop and remove data
```bash
docker-compose down -v  # WARNING: This deletes all data!
```

### View logs
```bash
docker-compose logs redis
docker-compose logs neo4j
docker-compose logs -f  # Follow all logs
```

### Restart a service
```bash
docker-compose restart redis
docker-compose restart neo4j
```

## Production Deployment

For production, consider:

1. **Redis**: Use managed Redis (Upstash, Redis Cloud, AWS ElastiCache)
2. **Neo4j**: Use Neo4j Aura (cloud) or self-hosted with backups
3. **Supabase**: Already production-ready (consider paid tier for more resources)
4. **Security**:
   - Never commit `.env` file
   - Use strong passwords
   - Enable SSL/TLS for all connections
   - Set up firewall rules
5. **Monitoring**: Add Sentry DSN for error tracking

## Next Steps

1. Read the main [README.md](README.md) for API documentation
2. Explore the [API endpoints](#)
3. Set up the Telegram bot (optional)
4. Customize agents for your needs

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify `.env` configuration
3. Ensure all services are running
4. Open an issue on GitHub with error details

## Quick Reference

### Default Ports
- Main App: `8044`
- Mem0 Service: `8081`
- Redis: `6379`
- Neo4j Browser: `7474`
- Neo4j Bolt: `7687`

### Default Credentials (Local)
- Neo4j: `neo4j` / `jenny123`
- Redis: No password (default)
- Supabase: Your chosen password

### Useful Commands
```bash
# Start all services
docker-compose up -d

# Start Jenny
python -m uvicorn app.main:app --port 8044

# Start Mem0
python -m uvicorn app.mem0.server.main:app --port 8081

# Run tests
pytest tests/ -v

# Stop all Docker services
docker-compose down
```
