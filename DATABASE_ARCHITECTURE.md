# Jenny Database Architecture

## Overview

Jenny uses **3 database services** running locally via Docker. Each serves a specific purpose:

```
┌──────────────────────────────────────────────────────────────┐
│                    Jenny AI Assistant                        │
└──────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │    Neo4j     │
│  + pgvector  │  │              │  │              │
│  Port: 5432  │  │  Port: 6379  │  │  Port: 7687  │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 1. PostgreSQL + pgvector (Port 5432)

**Image**: `ankane/pgvector:latest`
**Container**: `jenny-postgres`

### Used For:

✅ **Mem0 Vector Store** (Primary use)
- Stores conversation memories as text
- Stores vector embeddings (1536 dimensions)
- Enables semantic search ("what did I say about coffee?")

✅ **User Data Storage**
- User profiles
- Preferences
- Calendar sync data
- Task lists

### Configuration:
```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=jenny_db
PGUSER=jenny
PGPASSWORD=jenny123
```

### Example Usage:
```python
# Mem0 stores memories here
memory = MemoryClient(config={
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "host": "localhost",
            "port": 5432,
            "database": "jenny_db",
            "user": "jenny",
            "password": "jenny123"
        }
    }
})
```

### Tables:
- `mem0` - Vector embeddings and text
- `users` - User profiles
- `tasks` - Task lists
- `calendar_events` - Cached calendar data

---

## 2. Redis (Port 6379)

**Image**: `redis:7-alpine`
**Container**: `jenny-redis`

### Used For:

✅ **APScheduler Job Store** (Primary use)
- Stores scheduled reminder jobs
- Persists job state across restarts
- Manages job execution times

✅ **Caching Layer**
- Session state
- API response caching
- Temporary data storage
- Rate limiting data

✅ **Mem0 Optional Caching**
- Can cache frequently accessed memories
- Speed up repeated queries

### Configuration:
```bash
REDIS_URL=redis://localhost:6379
```

### Example Usage:
```python
# APScheduler uses Redis for job persistence
jobstores = {
    'default': RedisJobStore(
        host='localhost',
        port=6379
    )
}

scheduler = AsyncIOScheduler(jobstores=jobstores)

# Caching layer
from app.core.cache import get_client

redis = await get_client()
await redis.set("key", "value", ex=3600)  # Cache for 1 hour
```

### Keys/Namespaces:
- `jenny:apscheduler:jobs` - Scheduled jobs
- `jenny:apscheduler:run_times` - Job run times
- `memory:user_id:*` - Cached memories
- `search:user_id:*` - Cached search results
- `session:user_id` - User sessions

---

## 3. Neo4j (Ports 7474, 7687)

**Image**: `neo4j:5-community`
**Container**: `jenny-neo4j`

### Used For:

✅ **Mem0 Graph Store** (Primary use)
- Stores relationships between entities
- Maps conversation context
- Tracks user-topic connections

✅ **Interaction Logging**
- Records user interactions
- Builds conversation history graph
- Tracks agent usage patterns

### Configuration:
```bash
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=jenny123
# Web UI: http://localhost:7474
```

### Example Usage:
```python
# Mem0 stores graph relationships here
memory = MemoryClient(config={
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "neo4j://localhost:7687",
            "username": "neo4j",
            "password": "jenny123"
        }
    }
})

# Manual graph operations
from app.core.graph import create_node

await create_node("Interaction", {
    "user_id": "telegram_123",
    "agent": "calendar_agent",
    "query": "What's on my calendar?",
    "timestamp": time.time()
})
```

### Graph Structure:
```
(User)-[:ASKED]->(Question)
(User)-[:LIKES]->(Coffee)
(User)-[:HAS_EVENT]->(CalendarEvent)
(User)-[:SET_REMINDER]->(Reminder)
(User)-[:INTERACTED_WITH]->(Agent)
```

---

## Data Flow Examples

### 1. Memory Storage
```
User says: "I love coffee"
         ↓
    Jenny Agent
         ↓
    Mem0 Service
         ↓
    ┌────────────────────┐
    │   PostgreSQL       │  Stores: text + vector embedding
    │   "I love coffee"  │
    │   [0.234, -0.123,  │
    │    0.456, ...]     │
    └────────────────────┘
         +
    ┌────────────────────┐
    │      Neo4j         │  Creates: (User)-[:LIKES]->(Coffee)
    │  User → Coffee     │
    └────────────────────┘
```

### 2. Memory Retrieval
```
User asks: "What do I like?"
         ↓
    Jenny Agent
         ↓
    Mem0 Service
         ↓
    PostgreSQL: Vector similarity search
         ↓
    Returns: "I love coffee" (score: 0.95)
         ↓
    Neo4j: Graph traversal
         ↓
    Returns: (User)-[:LIKES]->(Coffee, Tea, Programming)
         ↓
    Jenny: "You mentioned you love coffee, tea, and programming"
```

### 3. Scheduled Reminder
```
User: "Remind me in 2 hours"
         ↓
    Task Agent
         ↓
    Scheduler Service
         ↓
    ┌────────────────────┐
    │       Redis        │  Stores: Job {
    │  Scheduled Jobs    │    id: "reminder_123_abc",
    │                    │    run_at: "2024-01-15T10:00",
    │                    │    user: "telegram_123",
    │                    │    message: "Take medication"
    │                    │  }
    └────────────────────┘
         ↓
    (2 hours later)
         ↓
    APScheduler fires job
         ↓
    Send Telegram notification 🔔
```

### 4. Calendar Sync
```
User: "What's on my calendar?"
         ↓
    Calendar Agent
         ↓
    Unified Calendar Service
         ↓
    ┌────────────────────┐
    │       Redis        │  Check cache first
    │  Cache Layer       │
    └────────────────────┘
         │ (cache miss)
         ↓
    Fetch from Google/Outlook/Apple
         ↓
    ┌────────────────────┐
    │    PostgreSQL      │  Store cached events
    │  Calendar Cache    │
    └────────────────────┘
         +
    ┌────────────────────┐
    │      Neo4j         │  Log: (User)-[:CHECKED_CALENDAR]->(Today)
    │  Interaction Log   │
    └────────────────────┘
```

---

## Storage Requirements

### Typical Storage Usage (per 1000 users)

**PostgreSQL**:
- Memories: ~100MB (10 memories per user × 10KB each)
- Vector embeddings: ~600MB (10 memories × 1536 dims × 4 bytes)
- User data: ~50MB
- **Total**: ~750MB

**Redis**:
- Scheduled jobs: ~10MB (5 jobs per user × 2KB each)
- Cache: ~50MB (LRU cache, auto-evicts)
- Sessions: ~5MB
- **Total**: ~65MB (mostly transient)

**Neo4j**:
- Nodes: ~100MB (users, memories, interactions)
- Relationships: ~50MB (connections between entities)
- **Total**: ~150MB

**Grand Total**: ~965MB for 1000 active users

---

## Backup Strategy

### PostgreSQL
```bash
# Backup
docker exec jenny-postgres pg_dump -U jenny jenny_db > backup.sql

# Restore
docker exec -i jenny-postgres psql -U jenny jenny_db < backup.sql
```

### Redis
```bash
# Backup (Redis handles this automatically with AOF)
docker exec jenny-redis redis-cli BGSAVE

# Copy backup file
docker cp jenny-redis:/data/dump.rdb ./redis-backup.rdb
```

### Neo4j
```bash
# Backup
docker exec jenny-neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump

# Restore
docker exec jenny-neo4j neo4j-admin load --from=/backups/neo4j-backup.dump --database=neo4j --force
```

---

## Health Checks

All services have built-in health checks:

### Check PostgreSQL
```bash
docker exec jenny-postgres pg_isready -U jenny
# Should output: /var/run/postgresql:5432 - accepting connections
```

### Check Redis
```bash
docker exec jenny-redis redis-cli ping
# Should output: PONG
```

### Check Neo4j
```bash
curl http://localhost:7474
# Should return HTML page

# Or use Cypher query
docker exec jenny-neo4j cypher-shell -u neo4j -p jenny123 "RETURN 1"
```

### Check All Services
```bash
docker-compose ps
# All should show status: Up (healthy)
```

---

## Performance Tuning

### PostgreSQL
```yaml
# docker-compose.yml
environment:
  - POSTGRES_SHARED_BUFFERS=256MB
  - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
  - POSTGRES_WORK_MEM=16MB
```

### Redis
```yaml
# docker-compose.yml
command: >
  redis-server
  --maxmemory 512mb
  --maxmemory-policy allkeys-lru
  --appendonly yes
```

### Neo4j
```yaml
# docker-compose.yml (already configured)
environment:
  - NEO4J_dbms_memory_heap_initial__size=512m
  - NEO4J_dbms_memory_heap_max__size=2G
```

---

## Common Issues

### "Connection refused" to PostgreSQL
```bash
# Check if container is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### Redis "Can't save to disk"
```bash
# Check disk space
df -h

# Clear old data
docker exec jenny-redis redis-cli FLUSHDB
```

### Neo4j "Too many open files"
```bash
# Increase file limits in docker-compose.yml
ulimits:
  nofile:
    soft: 40000
    hard: 40000
```

---

## Summary

✅ **3 Database Services** - All running locally
✅ **PostgreSQL** - Stores memories + vectors (Mem0 primary storage)
✅ **Redis** - Schedules jobs + caching (APScheduler + cache layer)
✅ **Neo4j** - Relationship graphs (Mem0 graph store + interaction logs)

**All data stays local. No cloud dependencies. Complete privacy.**

**Last Updated**: 2025-11-18
