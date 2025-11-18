# Jenny Installation Guide - Automated Setup

This guide covers the **automated installation** methods for Jenny. For manual setup, see [SETUP.md](SETUP.md).

## 🚀 Quick Install (Recommended)

### Option 1: Bash Script (Linux/macOS)

```bash
cd Jenny
./setup.sh
```

### Option 2: Python Script (All Platforms)

```bash
cd Jenny
python3 setup.py
```

Both scripts will:
- ✅ Check Python 3.11+ and Docker
- ✅ Install Python dependencies
- ✅ Create `.env` file from template
- ✅ Prompt for OpenAI API key (or skip to add later)
- ✅ Start Docker services (PostgreSQL, Redis, Neo4j)
- ✅ Verify all services are running

**Setup time: ~5 minutes**

---

## 📋 Prerequisites

Before running the setup script, ensure you have:

1. **Python 3.11 or higher**
   - Check: `python3 --version`
   - Install: https://www.python.org/downloads/

2. **Docker Desktop** (or Docker Engine + Docker Compose)
   - Check: `docker --version` and `docker compose version`
   - Install: https://docs.docker.com/get-docker/

3. **OpenAI API Key** (optional during setup, required to run)
   - Get from: https://platform.openai.com/api-keys

---

## 🎯 Installation Steps

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Jenny
```

### Step 2: Run Setup Script

**Linux/macOS:**
```bash
./setup.sh
```

**Windows/Cross-platform:**
```bash
python setup.py
```

### Step 3: Configure API Key (if skipped during setup)

Edit `.env` file:
```bash
nano .env  # or use your preferred editor
```

Add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 4: Start Services

**Option A: Using the Launcher (Easiest)**
```bash
python start.py
```
This starts both Mem0 and Jenny main app automatically!

**Option B: Manual (Two Terminals)**

Terminal 1 - Mem0 service:
```bash
python -m uvicorn app.mem0.server.main:app --port 8081
```

Terminal 2 - Jenny main app:
```bash
python -m uvicorn app.main:app --port 8044
```

### Step 5: Test Installation

```bash
curl http://localhost:8044/health
```

Expected response:
```json
{"ok":true}
```

---

## 🔧 What Gets Installed?

### Python Packages (via pip)
- FastAPI, Uvicorn - Web framework
- PostgreSQL, Redis, Neo4j drivers
- OpenAI client
- strands-agents-tools (50+ tools)
- Telegram bot framework
- And more... (see requirements.txt)

### Docker Containers
- **PostgreSQL 16** with pgvector extension
  - Port: 5432
  - User: jenny
  - Password: jenny123
  - Database: jenny_db

- **Redis 7**
  - Port: 6379
  - No password (local only)

- **Neo4j 5 Community**
  - HTTP: 7474
  - Bolt: 7687
  - User: neo4j
  - Password: jenny123

---

## 📊 Setup Script Features

The automated setup script:

### ✅ Checks & Validation
- Python version >= 3.11
- Docker installation and daemon status
- Docker Compose availability
- Port availability (8044, 8081)

### ⚙️ Configuration
- Creates `.env` from `.env.example`
- Prompts for OpenAI API key
- Preserves existing `.env` if present
- Sets up local database credentials

### 🐳 Docker Services
- Starts PostgreSQL, Redis, Neo4j
- Waits for services to be healthy
- Verifies connectivity to each service
- Shows status for each database

### 📝 Final Output
- Service URLs and credentials
- Next steps instructions
- Useful commands reference
- Database access information

---

## 🎮 Using the Service Launcher

The `start.py` script provides an easy way to run Jenny:

```bash
python start.py
```

**Features:**
- ✅ Starts both Mem0 and Jenny main app
- ✅ Waits for services to be ready
- ✅ Health checks for both services
- ✅ Monitors processes
- ✅ Graceful shutdown with Ctrl+C
- ✅ Shows service URLs and test commands

**Output:**
```
✓ All services started successfully!

Service URLs:
  - Mem0:  http://localhost:8081
  - Jenny: http://localhost:8044

Database interfaces:
  - Neo4j Browser: http://localhost:7474
  - PostgreSQL:    localhost:5432
  - Redis:         localhost:6379

Press Ctrl+C to stop all services
```

---

## 🛠️ Troubleshooting

### "Python 3.11 or higher required"

**Solution:** Install Python 3.11+
```bash
# macOS (Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11

# Windows
# Download from python.org
```

### "Docker not found"

**Solution:** Install Docker Desktop
- macOS/Windows: https://www.docker.com/products/docker-desktop
- Linux: https://docs.docker.com/engine/install/

### "Docker daemon is not running"

**Solution:** Start Docker
- macOS/Windows: Open Docker Desktop
- Linux: `sudo systemctl start docker`

### "Port already in use"

**Solution:** Stop the conflicting service
```bash
# Find process using port
lsof -i :8044  # or :8081, :5432, etc.

# Kill the process
kill -9 <PID>

# Or stop Jenny services
pkill -f uvicorn
docker-compose down
```

### "Failed to start Docker services"

**Solution:** Check Docker logs
```bash
docker-compose logs postgres
docker-compose logs redis
docker-compose logs neo4j

# Restart services
docker-compose restart
```

### "Service timeout"

Some services (especially Neo4j) can take 1-2 minutes to start.

**Solution:** Wait a bit longer, then check:
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f neo4j

# Manually verify
docker exec jenny-neo4j wget -q --spider http://localhost:7474 && echo "Ready"
```

---

## 🔄 Reinstalling / Resetting

### Complete Reset

```bash
# Stop all services
docker-compose down -v  # WARNING: Deletes all data!

# Remove .env
rm .env

# Re-run setup
./setup.sh
# or
python setup.py
```

### Just Reset Databases

```bash
docker-compose down -v
docker-compose up -d
```

### Reinstall Python Packages

```bash
pip install -r requirements.txt --upgrade --force-reinstall
```

---

## 📂 File Reference

| File | Purpose |
|------|---------|
| `setup.sh` | Bash setup script (Linux/macOS) |
| `setup.py` | Python setup script (cross-platform) |
| `start.py` | Service launcher (both Mem0 and Jenny) |
| `.env.example` | Environment template |
| `.env` | Your configuration (created by setup) |
| `docker-compose.yml` | Database services definition |
| `requirements.txt` | Python dependencies |

---

## 🎯 What Happens During Setup?

```
setup.sh / setup.py
    ↓
1. Check Python 3.11+
2. Check Docker & Docker Compose
3. Install pip dependencies
    ↓
4. Create .env file
5. Prompt for OpenAI API key
    ↓
6. Start docker-compose up -d
    - PostgreSQL
    - Redis
    - Neo4j
    ↓
7. Wait for services (health checks)
8. Display final instructions
    ↓
start.py (optional)
    ↓
9. Start Mem0 service (port 8081)
10. Start Jenny app (port 8044)
11. Monitor services
```

---

## 🚀 Quick Commands Reference

```bash
# Setup
./setup.sh              # Linux/macOS automated setup
python setup.py         # Cross-platform automated setup

# Start services
python start.py         # Easiest - starts both services
docker-compose up -d    # Just databases

# Stop services
Ctrl+C                  # Stop start.py
docker-compose down     # Stop databases

# Check status
docker-compose ps       # Database services
curl http://localhost:8044/health  # Jenny app

# View logs
docker-compose logs -f  # All database logs
docker-compose logs postgres  # Specific service

# Restart
docker-compose restart postgres
```

---

## 📖 Next Steps

After installation:

1. **Test the API:**
   ```bash
   curl -X POST http://localhost:8044/ask \
     -H "Content-Type: application/json" \
     -d '{"user_id":"test","text":"Remember I love coffee"}'
   ```

2. **Explore the tools:**
   ```bash
   curl -X POST http://localhost:8044/ask \
     -H "Content-Type: application/json" \
     -d '{"user_id":"test","text":"list tools"}'
   ```

3. **Access databases:**
   - Neo4j: http://localhost:7474 (neo4j/jenny123)
   - PostgreSQL: `psql -h localhost -U jenny -d jenny_db`
   - Redis: `redis-cli`

4. **Read the docs:**
   - API Reference: [README.md](README.md)
   - Manual Setup: [SETUP.md](SETUP.md)

---

## 💡 Tips

- **First run?** Use `python setup.py` - it's cross-platform and well-tested
- **Already setup?** Use `python start.py` to quickly start services
- **Development mode?** Use `--reload` flag: `uvicorn app.main:app --reload --port 8044`
- **Production?** Change default passwords in `.env` and `docker-compose.yml`
- **Backup data?** `docker-compose down` preserves volumes, `-v` deletes them

---

## ✅ Success Checklist

After running setup, you should have:

- [x] Python 3.11+ installed
- [x] Docker running
- [x] `.env` file with OpenAI API key
- [x] Three Docker containers running (postgres, redis, neo4j)
- [x] Python packages installed
- [x] Health endpoint responding: http://localhost:8044/health

If any item is unchecked, see [Troubleshooting](#troubleshooting) section.

---

## 🎉 You're Ready!

Jenny is now installed and ready to use! Try asking it something:

```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"your-name","text":"Hello Jenny! Tell me what you can do"}'
```

For more examples and API documentation, see [README.md](README.md).
