# Jenny AI Assistant - New Architecture Design

## Executive Summary

This document outlines the migration from the current custom implementation to a Strands SDK-based architecture with official Mem0 integration, designed to support advanced business automation features.

## Current Architecture (Before Migration)

### Components
- **Orchestrator**: Custom intent router using keyword matching
- **Agents**: Simple async functions (memory_agent, task_agent, calendar_agent, etc.)
- **Memory**: Custom Mem0 microservice with PostgreSQL + pgvector
- **Tools**: Recently added strands-agents-tools integration (limited)
- **Databases**: PostgreSQL (pgvector), Redis, Neo4j (all local via Docker)

### Limitations
1. No structured agent framework - agents are just functions
2. Custom Mem0 implementation instead of official library
3. Limited tool integration
4. No support for complex workflows
5. Basic intent detection (keyword-based)
6. Missing business automation features

## New Architecture (Strands SDK + Official Mem0)

### Core Framework Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Jenny AI Assistant                      │
├─────────────────────────────────────────────────────────────┤
│  User Interfaces                                            │
│  ├─ Telegram Bot (primary interface)                       │
│  ├─ REST API                                                │
│  └─ Dashboard (Premium)                                     │
├─────────────────────────────────────────────────────────────┤
│  Orchestration Layer                                        │
│  ├─ StrandsOrchestrator (replaces custom Orchestrator)     │
│  ├─ Intent Router (enhanced with Mem0 context)             │
│  └─ Session Manager                                         │
├─────────────────────────────────────────────────────────────┤
│  Agents Layer (Strands Agent Pattern)                      │
│  ├─ MemoryAgent (conversation tracking)                    │
│  ├─ TaskAgent (reminders, todos, lists)                    │
│  ├─ CalendarAgent (Google, Outlook, Apple sync)            │
│  ├─ SchedulerAgent (timed reminders, recurring tasks)      │
│  ├─ MultimediaAgent (voice, image processing)              │
│  ├─ KnowledgeAgent (Q&A, research)                         │
│  ├─ ToolsAgent (50+ Strands tools)                         │
│  └─ DashboardAgent (analytics, insights)                   │
├─────────────────────────────────────────────────────────────┤
│  Tools Layer (Strands Tools Library)                       │
│  ├─ File Operations (read, write, edit)                    │
│  ├─ Web Search & Scraping                                  │
│  ├─ HTTP Requests                                           │
│  ├─ Python REPL                                             │
│  ├─ Mem0 Memory (official integration)                     │
│  ├─ Calendar APIs (Google, Microsoft, CalDAV)              │
│  ├─ Image Analysis (OpenAI Vision)                         │
│  └─ Voice Transcription (Whisper)                          │
├─────────────────────────────────────────────────────────────┤
│  Memory Layer (Mem0 Open Source - Local)                  │
│  ├─ Short-term Memory (conversation context)               │
│  ├─ Long-term Memory (user preferences, history)           │
│  ├─ Entity Memory (facts, relationships)                   │
│  ├─ Vector Store (local PostgreSQL + pgvector)             │
│  └─ Graph Memory (local Neo4j for complex relationships)   │
├─────────────────────────────────────────────────────────────┤
│  Scheduler Layer (APScheduler)                             │
│  ├─ Cron Jobs (daily summaries, recurring tasks)           │
│  ├─ Interval Tasks (periodic checks)                       │
│  ├─ One-time Reminders                                     │
│  └─ Calendar Event Triggers                                │
├─────────────────────────────────────────────────────────────┤
│  Security Layer                                             │
│  ├─ End-to-End Encryption (cryptography)                   │
│  ├─ Password Hashing (passlib)                             │
│  ├─ JWT Authentication (python-jose)                       │
│  └─ Rate Limiting                                           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (Docker Services)                              │
│  ├─ PostgreSQL + pgvector (vector embeddings)              │
│  ├─ Redis (caching, session state)                         │
│  └─ Neo4j (knowledge graph, relationships)                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Dependencies (Updated requirements.txt)

### Core Framework
```python
# AI Framework
strands-agents>=0.1.0          # Strands SDK for agent orchestration
strands-agents-tools>=0.1.0    # 70+ pre-built tools
mem0ai>=0.1.0                  # Mem0 open source (configured for local PostgreSQL + Neo4j)

# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# AI Models
openai>=1.3.0
anthropic>=0.7.0               # For Claude models (optional)

# Database & Caching
psycopg2-binary>=2.9.9
redis>=5.0.1
neo4j>=5.14.0
pgvector>=0.2.3

# Scheduling
apscheduler>=3.10.4            # For scheduled reminders
celery[redis]>=5.3.4           # For async task queue (optional)

# Calendar Integrations
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.1.0
msal>=1.24.0                   # Microsoft Graph API
caldav>=1.3.6                  # Apple Calendar (CalDAV)

# Messaging
python-telegram-bot>=22.5      # Telegram Bot (all notifications and reminders)

# Multimedia Processing
openai-whisper>=20231117       # Voice transcription
pillow>=10.1.0                 # Image processing
python-magic>=0.4.27           # File type detection

# Security
cryptography>=41.0.5
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.6

# Utilities
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
tenacity>=8.2.3
sentry-sdk[fastapi]>=1.38.0
```

## Migration Phases

### Phase 1: Core Framework Migration (Current Focus)
**Status**: In Progress
**Duration**: 1-2 hours

Tasks:
1. ✅ Update requirements.txt with all dependencies
2. ✅ Create ARCHITECTURE.md (this document)
3. [ ] Refactor agents to use Strands Agent class
4. [ ] Replace custom Mem0 with official library
5. [ ] Update orchestrator to use Strands SDK
6. [ ] Test basic functionality

**Files to Modify**:
- `requirements.txt`
- `app/strands/agents/*.py` (refactor all agents)
- `app/strands/orchestrator.py` (replace with StrandsOrchestrator)
- `app/mem0/` (replace custom implementation)

### Phase 2: Calendar Integrations
**Status**: Pending
**Duration**: 2-3 hours

Tasks:
1. [ ] Set up Google Calendar API integration
2. [ ] Set up Microsoft Graph API (Outlook)
3. [ ] Set up CalDAV for Apple Calendar
4. [ ] Create unified calendar interface
5. [ ] Implement event creation from natural language
6. [ ] Add calendar sync background job

**New Files**:
- `app/integrations/calendar/google_calendar.py`
- `app/integrations/calendar/microsoft_calendar.py`
- `app/integrations/calendar/apple_calendar.py`
- `app/integrations/calendar/unified.py`

### Phase 3: Scheduled Reminders System
**Status**: Pending
**Duration**: 2 hours

Tasks:
1. [ ] Set up APScheduler
2. [ ] Create reminder scheduler service
3. [ ] Implement recurring task support
4. [ ] Add reminder notification system
5. [ ] Enhance Telegram integration

**New Files**:
- `app/scheduler/scheduler.py`
- `app/scheduler/reminder_service.py`
- `app/scheduler/jobs.py`

### Phase 4: Multimedia Processing
**Status**: Pending
**Duration**: 2 hours

Tasks:
1. [ ] Integrate OpenAI Whisper for voice transcription
2. [ ] Add image analysis with GPT-4 Vision
3. [ ] Create multimedia agent
4. [ ] Add file upload endpoints
5. [ ] Implement storage solution

**New Files**:
- `app/agents/multimedia_agent.py`
- `app/services/voice_transcription.py`
- `app/services/image_analysis.py`

### Phase 5: Dashboard Backend APIs
**Status**: Pending
**Duration**: 2-3 hours

Tasks:
1. [ ] Create analytics endpoints
2. [ ] Implement usage tracking
3. [ ] Add insights generation
4. [ ] Create premium user management
5. [ ] Build reporting APIs

**New Files**:
- `app/api/dashboard.py`
- `app/services/analytics.py`
- `app/services/insights.py`

### Phase 6: Encryption & Privacy
**Status**: Pending
**Duration**: 1-2 hours

Tasks:
1. [ ] Implement end-to-end encryption
2. [ ] Add password hashing
3. [ ] Set up JWT authentication
4. [ ] Create user authentication system
5. [ ] Add rate limiting

**New Files**:
- `app/security/encryption.py`
- `app/security/auth.py`
- `app/security/rate_limit.py`

### Phase 7: Testing & Documentation
**Status**: Pending
**Duration**: 2 hours

Tasks:
1. [ ] Update all tests
2. [ ] Create integration tests
3. [ ] Update README.md
4. [ ] Update INSTALL.md
5. [ ] Create API documentation
6. [ ] Create user guide

## Agent Architecture (Strands Pattern)

### Base Agent Structure

```python
from strands_agents import Agent, ToolRegistry

class JennyBaseAgent(Agent):
    """Base class for all Jenny agents using Strands SDK"""

    def __init__(self, name: str, description: str):
        super().__init__(name=name, description=description)
        self.memory = get_mem0_client()
        self.tools = ToolRegistry()

    async def execute(self, query: str, context: dict) -> dict:
        """Main execution method - to be overridden"""
        raise NotImplementedError

    async def get_user_memory(self, user_id: str) -> list:
        """Fetch user context from Mem0"""
        return await self.memory.search(query="", user_id=user_id)

    async def save_memory(self, user_id: str, text: str):
        """Save to Mem0"""
        await self.memory.add(messages=[{"role": "user", "content": text}], user_id=user_id)
```

### Example: Task Agent (Strands Pattern)

```python
from strands_agents import Agent
from strands_tools import get_tool
from mem0 import MemoryClient

class TaskAgent(Agent):
    """Manages tasks, reminders, todos using Strands + Mem0"""

    def __init__(self):
        super().__init__(
            name="task_agent",
            description="Handles task creation, reminders, and todo management"
        )
        self.memory = MemoryClient()
        self.scheduler = get_scheduler()

    async def execute(self, query: str, context: dict) -> dict:
        user_id = context.get("user_id")

        # Get user context from Mem0
        memories = await self.memory.search(query=query, user_id=user_id, limit=5)

        # Determine intent
        if "remind" in query.lower():
            return await self.create_reminder(query, user_id, memories)
        elif "list" in query.lower():
            return await self.list_tasks(user_id)
        elif "complete" in query.lower():
            return await self.complete_task(query, user_id)

        # Use LLM for complex queries
        response = await self.llm_invoke(query, context=memories)

        # Save interaction to Mem0
        await self.memory.add(
            messages=[{"role": "assistant", "content": response}],
            user_id=user_id
        )

        return {"reply": response}
```

## Mem0 Integration (Open Source - Local Configuration)

**Important**: We are using the `mem0ai` **open source library** (NOT the cloud service).
All data is stored locally in PostgreSQL + pgvector and Neo4j. No data leaves your infrastructure.

### Current Custom Implementation (Fallback)
```python
# app/mem0/server/main.py - Custom Mem0 microservice (legacy fallback)
# - Custom PostgreSQL + pgvector implementation
# - Custom embedding generation
# - Custom search logic
# - Microservice running on port 8081
```

### New Mem0 Open Source Integration (Primary)
```python
# app/services/memory.py - Using mem0ai open source library
from mem0 import MemoryClient

# Initialize with LOCAL PostgreSQL backend (no cloud!)
memory = MemoryClient(
    config={
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "host": "localhost",
                "port": 5432,
                "database": "jenny_db",
                "user": "jenny",
                "password": "jenny123"
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small"
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "url": "neo4j://localhost:7687",
                "username": "neo4j",
                "password": "jenny123"
            }
        }
    }
)

# Add memory
await memory.add(
    messages=[{"role": "user", "content": "I love coffee"}],
    user_id="user_123"
)

# Search memory
results = await memory.search(
    query="what do I like?",
    user_id="user_123",
    limit=5
)

# Get all memories
all_memories = await memory.get_all(user_id="user_123")
```

## Calendar Integration Architecture

### Unified Calendar Interface

```python
# app/integrations/calendar/unified.py

from typing import Protocol, List
from datetime import datetime

class CalendarProvider(Protocol):
    """Protocol for calendar providers"""

    async def list_events(self, start: datetime, end: datetime) -> List[dict]:
        ...

    async def create_event(self, title: str, start: datetime, end: datetime, **kwargs) -> dict:
        ...

    async def update_event(self, event_id: str, **kwargs) -> dict:
        ...

    async def delete_event(self, event_id: str) -> bool:
        ...

class UnifiedCalendar:
    """Unified interface for all calendar providers"""

    def __init__(self):
        self.providers = {
            "google": GoogleCalendarProvider(),
            "outlook": MicrosoftCalendarProvider(),
            "apple": AppleCalendarProvider()
        }

    async def sync_all(self, user_id: str):
        """Sync events from all connected calendars"""
        events = []
        for name, provider in self.providers.items():
            if await self.is_connected(user_id, name):
                events.extend(await provider.list_events())
        return events
```

## Scheduler Architecture

### APScheduler Integration

```python
# app/scheduler/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from datetime import datetime

jobstores = {
    'default': RedisJobStore(host='localhost', port=6379)
}

scheduler = AsyncIOScheduler(jobstores=jobstores)

# Example: Schedule a reminder
scheduler.add_job(
    send_reminder,
    'date',  # One-time job
    run_date=datetime(2024, 1, 15, 10, 0),
    args=[user_id, "Take medication"],
    id=f"reminder_{user_id}_{timestamp}"
)

# Example: Recurring task
scheduler.add_job(
    daily_summary,
    'cron',
    hour=20,  # 8 PM daily
    args=[user_id],
    id=f"daily_summary_{user_id}"
)
```

## Security Architecture

### End-to-End Encryption

```python
# app/security/encryption.py

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class EncryptionService:
    """Handle user data encryption"""

    def __init__(self):
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def encrypt_message(self, message: str) -> str:
        """Encrypt user message"""
        return self.cipher.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted: str) -> str:
        """Decrypt user message"""
        return self.cipher.decrypt(encrypted.encode()).decode()
```

## Environment Configuration (Updated .env)

```bash
# Core Services
OPENAI_API_KEY=sk-proj-...
ENV=production

# Databases (unchanged)
PGHOST=localhost
PGPORT=5432
PGDATABASE=jenny_db
PGUSER=jenny
PGPASSWORD=jenny123

REDIS_URL=redis://localhost:6379

NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=jenny123

# Mem0 Configuration (official library)
MEM0_VECTOR_STORE=pgvector
MEM0_GRAPH_STORE=neo4j
MEM0_EMBEDDER=openai

# Calendar Integrations
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8044/auth/google/callback

MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_REDIRECT_URI=http://localhost:8044/auth/microsoft/callback

# WhatsApp Business API (Twilio)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Telegram
TELEGRAM_BOT_TOKEN=...

# Security
JWT_SECRET_KEY=... (generate with: openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

ENCRYPTION_KEY=... (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Scheduler
SCHEDULER_TIMEZONE=America/New_York

# Dashboard
DASHBOARD_ENABLED=true
PREMIUM_FEATURES_ENABLED=true
```

## Success Criteria

### Phase 1 (Core Migration)
- [ ] All agents refactored to Strands pattern
- [ ] Official Mem0 library integrated
- [ ] All existing tests passing
- [ ] No regression in functionality

### Final Product
- [ ] Calendar sync working for all 3 providers
- [ ] Scheduled reminders functional via Telegram
- [ ] Telegram bot fully integrated
- [ ] Voice note transcription working
- [ ] Image analysis working
- [ ] Dashboard APIs functional
- [ ] Encryption enabled for sensitive data
- [ ] 24/7 availability (no crashes)
- [ ] Response time < 2 seconds
- [ ] Comprehensive test coverage > 80%

## Timeline

- **Phase 1**: 2 hours (Core Migration) ✅ COMPLETED
- **Phase 2**: 3 hours (Calendar) ✅ COMPLETED
- **Phase 3**: 2 hours (Scheduler) ✅ COMPLETED
- **Phase 4**: 2 hours (Multimedia)
- **Phase 5**: 3 hours (Dashboard)
- **Phase 6**: 2 hours (Security)
- **Phase 7**: 2 hours (Testing & Docs)

**Total Estimated Time**: 16 hours
**Completed**: 7 hours (Phases 1-3)
**Remaining**: 9 hours (Phases 4-7)

## Next Steps

1. Complete Phase 1: Core Framework Migration
2. Test thoroughly before moving to Phase 2
3. Implement phases sequentially
4. Deploy and monitor

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
**Author**: Claude (AI Assistant)
