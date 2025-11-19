# Jenny AI Assistant - Quick Start Guide

## 👋 Start Here!

**Are you Claude Code, a developer, or an AI assistant trying to understand this project?**

This guide tells you exactly where to look and what to do.

---

## 📚 Documentation Map

```
START HERE
    ↓
┌─────────────────────────────────────────────────────────┐
│  QUICKSTART.md (YOU ARE HERE)                          │
│  ↓                                                      │
│  Read this first to understand the project structure   │
└─────────────────────────────────────────────────────────┘
    ↓
    ├─→ For Installation/Setup:
    │   ┌──────────────────────────────────────────┐
    │   │  INSTALL.md                              │
    │   │  - Automated setup scripts               │
    │   │  - Step-by-step installation guide       │
    │   │  - Troubleshooting                       │
    │   └──────────────────────────────────────────┘
    │
    ├─→ For Development/Adding Features:
    │   ┌──────────────────────────────────────────┐
    │   │  IMPLEMENTATION_GUIDE.md                 │
    │   │  - What's already built                  │
    │   │  - What's pending                        │
    │   │  - How to extend Jenny                   │
    │   │  - Code examples                         │
    │   └──────────────────────────────────────────┘
    │
    ├─→ For Understanding Architecture:
    │   ┌──────────────────────────────────────────┐
    │   │  ARCHITECTURE.md                         │
    │   │  - System design                         │
    │   │  - Technology stack                      │
    │   │  - Migration phases                      │
    │   └──────────────────────────────────────────┘
    │
    ├─→ For Understanding CrewAI:
    │   ┌──────────────────────────────────────────┐
    │   │  CREWAI_BEST_PRACTICES.md                │
    │   │  - CrewAI implementation details         │
    │   │  - @CrewBase pattern                     │
    │   │  - Process.hierarchical routing          │
    │   │  - YAML configuration                    │
    │   └──────────────────────────────────────────┘
    │
    ├─→ For Understanding Databases:
    │   ┌──────────────────────────────────────────┐
    │   │  DATABASE_ARCHITECTURE.md                │
    │   │  - PostgreSQL, Redis, Neo4j explained    │
    │   │  - What each database does               │
    │   │  - Data flow diagrams                    │
    │   └──────────────────────────────────────────┘
    │
    └─→ For Usage/API Reference:
        ┌──────────────────────────────────────────┐
        │  README.md                               │
        │  - Project overview                      │
        │  - API endpoints                         │
        │  - Usage examples                        │
        └──────────────────────────────────────────┘
```

---

## 🎯 What is Jenny?

**Jenny is a self-learning AI business assistant powered by CrewAI** that:
- ✅ **Intelligent multi-agent orchestration** (CrewAI with hierarchical routing)
- ✅ **Remembers conversations** (Mem0 open source, 100% local)
- ✅ **Syncs with 3 calendars** (Google, Outlook, Apple)
- ✅ **Sends scheduled reminders** via Telegram
- ✅ **Natural language understanding** (no keywords needed!)
- ⏳ **Processes voice notes & images** (pending)
- ⏳ **Provides productivity insights** (pending)

**Key Principles**:
- 🔒 **100% local data storage. Zero cloud dependencies.**
- 🤖 **CrewAI multi-agent framework for intelligent task delegation**
- 🧠 **LLM-based routing (understands natural language, not keywords)**

---

## 🚀 I Want To...

### Option 1: "Just Install and Run Jenny"

**→ Go to: [INSTALL.md](INSTALL.md)**

```bash
# Quick install (5 minutes)
cd Jenny
python setup.py  # or ./setup.sh on Linux/Mac

# Start services
python start.py

# Test it
curl http://localhost:8044/health
```

**Prerequisites:**
- Python 3.11+
- Docker Desktop
- OpenAI API key

---

### Option 2: "Understand What's Built and Add Features"

**→ Go to: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**

**What's already done:**
- ✅ **CrewAI multi-agent orchestration** (with @CrewBase pattern)
- ✅ **Process.hierarchical** for automatic intelligent routing
- ✅ **5 specialized agents** (Memory, Task, Calendar, Profile, General)
- ✅ Mem0 open source integration
- ✅ Google/Outlook/Apple calendar sync
- ✅ Scheduled reminders (APScheduler)
- ✅ Natural language parsing (no keywords needed!)
- ✅ Local PostgreSQL + Redis + Neo4j

**What's pending:**
- ⏳ Voice transcription (Whisper)
- ⏳ Image analysis (GPT-4 Vision)
- ⏳ Dashboard APIs
- ⏳ Security/encryption layer

**Start developing:**
```bash
# Read the implementation guide
cat IMPLEMENTATION_GUIDE.md

# See examples of how to:
# - Add a new agent
# - Add a new calendar provider
# - Extend the system
```

---

### Option 3: "Understand the Architecture"

**→ Go to: [ARCHITECTURE.md](ARCHITECTURE.md)**

Understand:
- System design diagrams
- Technology choices (why CrewAI? why Mem0?)
- Component interactions
- CrewAI multi-agent orchestration
- Migration phases

---

### Option 4: "Understand the Databases"

**→ Go to: [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)**

Learn about:
- **PostgreSQL**: Stores memories + vector embeddings
- **Redis**: Schedules jobs + caching
- **Neo4j**: Knowledge graph + relationships

All running locally via Docker.

---

## 🎓 For Claude Code (or AI Assistants)

**If you're Claude Code or another AI trying to help with this project:**

### Step 1: Read These Files First
1. `QUICKSTART.md` (this file) - Get oriented
2. `IMPLEMENTATION_GUIDE.md` - Understand what exists and what's pending
3. `ARCHITECTURE.md` - Understand the design

### Step 2: Install and Run
Follow `INSTALL.md` to set up the environment.

### Step 3: Understand the Codebase Structure
```
Jenny/
├── app/
│   ├── crew/                   # ✅ NEW: CrewAI Implementation
│   │   ├── config/             # YAML configurations
│   │   │   ├── agents.yaml     # Agent roles, goals, backstories
│   │   │   └── tasks.yaml      # Task templates
│   │   ├── crew.py             # @CrewBase with Process.hierarchical
│   │   └── tools.py            # CrewAI tools (memory, tasks, calendar)
│   ├── api/routes.py           # Main API endpoints
│   ├── integrations/calendar/  # ✅ DONE: Calendar sync (3 providers)
│   ├── scheduler/              # ✅ DONE: Reminders system
│   ├── services/memory.py      # ✅ DONE: Mem0 integration
│   ├── strands/                # Legacy agent implementations
│   │   ├── agents/             # Original agent functions (deprecated)
│   │   └── conversation.py     # Conversation interface (uses CrewAI)
│   └── main.py                 # FastAPI app entry point
├── docker-compose.yml          # ✅ DONE: PostgreSQL, Redis, Neo4j
├── requirements.txt            # ✅ DONE: CrewAI + all dependencies
├── .env.example                # ✅ DONE: Configuration template
└── [Documentation files]
```

### Step 4: Make Changes
Use `IMPLEMENTATION_GUIDE.md` to:
- See what's already implemented
- Find code examples
- Understand how to add new features

### Step 5: Test
```bash
# Run tests
pytest

# Manual test
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"What can you do?"}'
```

---

## 🔑 Key Files to Edit

### Adding a Feature?

**Voice Transcription:**
1. Create: `app/services/voice_transcription.py`
2. Update: `app/strands/agents/multimedia_agent.py`
3. Test with Telegram voice notes

**Image Analysis:**
1. Create: `app/services/image_analysis.py`
2. Update: `app/strands/agents/multimedia_agent.py`
3. Test with Telegram photos

**New Agent:**
1. Create: `app/strands/agents/your_agent.py`
2. Register in: `app/strands/orchestrator.py`
3. Add intent keywords

**Dashboard:**
1. Create: `app/api/dashboard.py`
2. Create: `app/services/analytics.py`
3. Add routes to `app/main.py`

---

## 📋 Development Checklist

### First Time Setup
```bash
# 1. Clone repository
cd Jenny

# 2. Read documentation
cat IMPLEMENTATION_GUIDE.md
cat ARCHITECTURE.md

# 3. Install
python setup.py

# 4. Configure
cp .env.example .env
# Edit .env with your API keys

# 5. Start databases
docker-compose up -d

# 6. Start services
python start.py

# 7. Test
curl http://localhost:8044/health
```

### Adding a New Feature
```bash
# 1. Read IMPLEMENTATION_GUIDE.md for examples

# 2. Create your files in appropriate directories

# 3. Update orchestrator if adding an agent

# 4. Test locally

# 5. Commit
git add .
git commit -m "Add [feature]"
git push
```

---

## 🧪 Testing Jenny

### Health Check
```bash
curl http://localhost:8044/health
# Expected: {"ok":true}
```

### Test Memory
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Remember I love coffee"}'

# Then:
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"What do I like?"}'
# Expected: Mentions coffee
```

### Test Calendar
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"What'\''s on my calendar today?"}'
```

### Test Reminders
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"telegram_123456789","text":"Remind me in 5 minutes to test reminders"}'
# Wait 5 minutes, check Telegram
```

---

## 🗺️ Project Status

### ✅ Completed (Phases 1-3)
- Mem0 open source integration
- Calendar sync (Google, Outlook, Apple)
- Scheduled reminders (Telegram)
- Natural language parsing
- Local database infrastructure

### ⏳ Pending (Phases 4-7)
- Voice & image processing (Phase 4)
- Dashboard backend APIs (Phase 5)
- Security & encryption (Phase 6)
- Testing & documentation (Phase 7)

**Progress**: 43% complete (7/16 hours)

---

## 🆘 Common Questions

### Q: Where do I start if I want to add voice note support?
**A:** Read `IMPLEMENTATION_GUIDE.md`, Phase 4: Multimedia Processing. It has code examples.

### Q: How does memory work?
**A:** Read `DATABASE_ARCHITECTURE.md`, section on PostgreSQL + Mem0. Shows data flow.

### Q: Can I use this without Docker?
**A:** No. PostgreSQL, Redis, and Neo4j run in Docker containers. It's required.

### Q: Where is the Telegram bot code?
**A:** Currently planned but not implemented. Reminder service has placeholder for Telegram integration at `app/integrations/telegram/bot.py` (to be created).

### Q: Is this using cloud Mem0?
**A:** **NO!** Using `mem0ai` open source library with 100% local PostgreSQL + Neo4j storage.

### Q: Why Redis?
**A:** Two reasons:
1. APScheduler stores scheduled reminder jobs in Redis
2. Caching layer for fast lookups

See `DATABASE_ARCHITECTURE.md` for details.

---

## 📞 Getting Help

### Documentation Order:
1. **QUICKSTART.md** (you are here) - Orientation
2. **INSTALL.md** - Installation guide
3. **IMPLEMENTATION_GUIDE.md** - Development guide
4. **ARCHITECTURE.md** - System design
5. **DATABASE_ARCHITECTURE.md** - Database details

### For Developers:
- Read `IMPLEMENTATION_GUIDE.md` first
- See code examples for adding features
- Check `ARCHITECTURE.md` for design decisions

### For Users:
- Read `INSTALL.md` first
- Follow automated setup
- Check `README.md` for API usage

---

## 🎯 Success Criteria

**Jenny is "complete" when:**
- ✅ Calendar sync works (3 providers)
- ✅ Reminders work (scheduled + recurring)
- ✅ Memory works (local Mem0)
- ⏳ Voice notes transcribed
- ⏳ Images analyzed
- ⏳ Dashboard shows insights
- ⏳ Data encrypted
- ⏳ Tests passing
- ⏳ Docs complete

---

## 🚀 Next Steps

**Choose your path:**

→ **Want to install?** Read [INSTALL.md](INSTALL.md)

→ **Want to develop?** Read [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)

→ **Want to understand?** Read [ARCHITECTURE.md](ARCHITECTURE.md)

→ **Want to use?** Read [README.md](README.md)

---

**Remember**: All data stays local. No cloud. Complete privacy. 🔒

**Last Updated**: 2025-11-18
