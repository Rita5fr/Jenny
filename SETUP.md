# Jenny Complete Setup Guide

**🎉 100% Local Setup - No Cloud Services Required!**

This guide will help you set up Jenny with all services running locally on your machine using Docker.

**🤖 Powered by CrewAI**: Jenny uses CrewAI's multi-agent orchestration framework with intelligent LLM-based routing. No keyword matching - the AI understands natural language!

## How Jenny Works

**Message Flow:**
```
Telegram Bot (or REST API /ask endpoint)
    ↓
JennyCrewRunner.process_query() (app/crew/crew.py)
    ↓
CrewAI with @CrewBase + Process.hierarchical
    ↓
Hierarchical Manager (auto-created by CrewAI)
    ↓ (analyzes query with LLM to determine intent)
    ↓
Delegates to appropriate agent:
    • Memory Keeper → Mem0 operations
    • Task Coordinator → Tasks/reminders
    • Calendar Coordinator → Calendar events (auto OAuth)
    • Profile Manager → User preferences
    • General Assistant → Conversations
    ↓
Agent uses CrewAI tools (app/crew/tools.py)
    ↓
Tools access services:
    • Mem0 (PostgreSQL + Neo4j) for context & memory
    • PostgreSQL for tasks
    • Google Calendar API (OAuth)
    ↓
Response returned to user
```

**Key Components:**
- **CrewAI** = Main orchestrator (intelligent routing, no keywords!)
- **Hierarchical Process** = LLM analyzes intent and delegates to agents
- **5 Specialized Agents** = Defined in `app/crew/config/agents.yaml`
- **Mem0** = Persistent AI memory (100% local PostgreSQL + Neo4j)
- **Calendar OAuth** = Automatic link generation when calendar not connected
- **Direct Integration** = Telegram/API → CrewAI → Mem0 (no intermediate layers)

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
- **CrewAI** (multi-agent orchestration framework)
- **LangChain** (tool integration for CrewAI)
- PostgreSQL, Redis, Neo4j drivers
- OpenAI client
- **Mem0** (AI memory layer, open source)
- **strands-agents-tools** (50+ optional utility tools - not used for orchestration)
- Telegram bot framework
- And more...

**Note**: strands-agents-tools is just a tool library. **CrewAI** is the main orchestration framework.

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

6. **Configure LLM Models** (Recommended - Cost Optimization):

   Jenny supports multiple LLM providers for different components. You can mix and match:

   **For CrewAI Agents** (Jenny's conversational AI):
   ```bash
   # Option 1: DeepSeek (Recommended - Best cost/performance)
   CREWAI_LLM_PROVIDER=deepseek
   DEEPSEEK_API_KEY=your-deepseek-key
   DEEPSEEK_MODEL=deepseek-chat

   # Option 2: Gemini (Fast and capable)
   CREWAI_LLM_PROVIDER=gemini
   GOOGLE_API_KEY=your-google-api-key
   GEMINI_MODEL=gemini-2.0-flash-exp

   # Option 3: OpenAI (Most reliable, default)
   CREWAI_LLM_PROVIDER=openai
   OPENAI_MODEL=gpt-4o-mini
   ```

   **For Mem0 Memory Operations** (Reading/retrieving memories):
   ```bash
   # Recommended: DeepSeek for cost savings
   MEM0_LLM_PROVIDER=deepseek
   MEM0_LLM_MODEL=deepseek-chat

   # Alternative: OpenAI
   MEM0_LLM_PROVIDER=openai
   MEM0_LLM_MODEL=gpt-4o-mini
   ```

   **For Mem0 Embeddings** (Saving memories - always use OpenAI):
   ```bash
   MEM0_EMBED_MODEL=text-embedding-3-small
   ```

   **💡 Recommended Configuration** (Best cost/performance):
   ```bash
   # Use DeepSeek for agents and memory operations
   CREWAI_LLM_PROVIDER=deepseek
   DEEPSEEK_API_KEY=your-deepseek-api-key
   DEEPSEEK_MODEL=deepseek-chat

   MEM0_LLM_PROVIDER=deepseek
   MEM0_LLM_MODEL=deepseek-chat

   # Always use OpenAI for embeddings (best quality)
   MEM0_EMBED_MODEL=text-embedding-3-small
   OPENAI_API_KEY=your-openai-api-key  # For embeddings only
   ```

   **📖 For detailed model configuration guide**, see [MODEL_CONFIGURATION.md](MODEL_CONFIGURATION.md).

   **Getting API Keys:**
   - OpenAI: https://platform.openai.com/api-keys
   - DeepSeek: https://platform.deepseek.com/
   - Google (Gemini): https://makersuite.google.com/app/apikey

   **Installing Gemini support** (if using Gemini):
   ```bash
   pip install langchain-google-genai
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

#### 5.2 Test CrewAI Intelligent Routing

Test that CrewAI properly routes queries to the right agents:

**Test Memory (no "remember" keyword needed):**
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"I love Italian food"}'
```

Expected: CrewAI manager routes to Memory Keeper agent, stores in Mem0 ✅

**Test Task Creation (natural language):**
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"I need to call mom tomorrow at 3pm"}'
```

Expected: CrewAI manager routes to Task Coordinator agent, creates reminder ✅

**Test Calendar (no "calendar" keyword needed):**
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Set up dentist appointment next week"}'
```

Expected: CrewAI manager routes to Calendar Coordinator agent ✅

#### 5.3 Test Memory Recall

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"What do you know about my preferences?"}'
```

Expected: CrewAI routes to Memory Keeper, retrieves from Mem0 ✅

#### 5.4 Test General Queries

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"What can you help me with?"}'
```

Expected: CrewAI routes to General Assistant, explains capabilities ✅

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

All these examples go through **CrewAI's hierarchical manager**, which intelligently routes to the appropriate agent.

### Memory Management (via Memory Keeper Agent)

```bash
# Save preferences (CrewAI routes to Memory Keeper → Mem0)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"My favorite color is blue"}'

# Recall preferences (CrewAI routes to Memory Keeper → searches Mem0)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"What do I like?"}'
```

### Task Management (via Task Coordinator Agent)

```bash
# Create task (CrewAI routes to Task Coordinator → creates task)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"Remind me to call mom tomorrow"}'

# List tasks (CrewAI routes to Task Coordinator → lists tasks)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"List my tasks"}'
```

### Calendar Management (via Calendar Coordinator Agent)

```bash
# Create event (CrewAI routes to Calendar Coordinator → creates event)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"Schedule dentist appointment tomorrow at 2pm"}'

# View calendar (CrewAI routes to Calendar Coordinator → lists events)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"What is on my calendar this week?"}'
```

### Using Advanced Tools (via General Assistant or specialized agents)

```bash
# List available tools
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"what tools do you have?"}'

# Natural conversation (CrewAI routes to General Assistant)
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","text":"What can you help me with?"}'
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

### Enable Optional Tool Libraries

**Note**: These are optional utility tools, not related to CrewAI orchestration.

```bash
# Optional: Additional strands-agents-tools features
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
