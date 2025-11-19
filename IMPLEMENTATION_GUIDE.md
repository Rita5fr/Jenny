# Jenny AI Assistant - Implementation Guide

## 🎯 Purpose

This guide tells developers (human or AI like Claude Code) exactly what Jenny is, what's been built, what's pending, and how to implement remaining features.

---

## 📖 What is Jenny?

**Jenny is a self-learning AI business assistant powered by CrewAI** that:
- Uses CrewAI multi-agent orchestration with intelligent LLM-based routing
- Remembers conversations and learns user preferences (Mem0 open source)
- Syncs with Google Calendar, Outlook, and Apple Calendar
- Sends scheduled reminders via Telegram
- Processes voice notes and images
- Helps with daily business tasks through natural language

**Key Principles**:
- 100% local data storage. No cloud services. Complete privacy.
- Intelligent routing via CrewAI (no keyword matching needed)

---

## ✅ What's Already Built (Phase 1-3 Complete)

### 1. **Mem0 Open Source Integration** ✅
**Location**: `app/services/memory.py`, `app/mem0/client.py`

**What it does**:
- Stores user memories using mem0ai open source library
- All data in local PostgreSQL + pgvector (vector embeddings)
- Graph relationships in local Neo4j
- Fallback to custom microservice if mem0ai not installed

**How to use**:
```python
from app.services.memory import add_memory, search_memory

# Add a memory
await add_memory(
    user_id="telegram_123456789",
    messages=[{"role": "user", "content": "I love coffee"}]
)

# Search memories
results = await search_memory(
    user_id="telegram_123456789",
    query="what do I like?",
    limit=5
)
```

### 2. **Calendar Integrations (3 Providers)** ✅
**Location**: `app/integrations/calendar/`

**Files**:
- `google_calendar.py` - Google Calendar API
- `microsoft_calendar.py` - Outlook/O365 Graph API
- `apple_calendar.py` - iCloud CalDAV
- `unified.py` - Single interface for all 3

**What it does**:
- OAuth authentication for Google & Microsoft
- List, create, update, delete events
- Search events across all calendars
- Natural language parsing ("schedule meeting tomorrow at 2pm")

**How to use**:
```python
from app.integrations.calendar import get_calendar_service

calendar = get_calendar_service(user_id="telegram_123456789")

# List events
events = await calendar.list_events(
    start=datetime.now(),
    end=datetime.now() + timedelta(days=7)
)

# Create event
event = await calendar.create_event(
    title="Team Meeting",
    start=datetime.now() + timedelta(hours=1),
    end=datetime.now() + timedelta(hours=2),
    description="Discuss Q1 goals"
)
```

### 3. **Scheduled Reminders (APScheduler)** ✅
**Location**: `app/scheduler/`

**Files**:
- `scheduler.py` - APScheduler setup with Redis backend
- `reminder_service.py` - Reminder management

**What it does**:
- One-time reminders ("remind me in 2 hours")
- Recurring reminders (daily, weekly, cron-based)
- Persistent job storage in Redis
- Telegram notifications when reminders fire

**How to use**:
```python
from app.scheduler import schedule_reminder, schedule_recurring_reminder

# One-time reminder
job_id = await schedule_reminder(
    user_id="telegram_123456789",
    message="Take medication",
    run_at=datetime.now() + timedelta(hours=1)
)

# Daily recurring reminder
job_id = await schedule_recurring_reminder(
    user_id="telegram_123456789",
    message="Morning standup",
    hour=9,
    minute=0
)
```

### 4. **Enhanced Calendar Agent** ✅
**Location**: `app/strands/agents/calendar_agent.py`

**What it does**:
- Natural language understanding: "What's on my calendar tomorrow?"
- Event creation: "Schedule a meeting tomorrow at 2pm"
- Event search: "Find events about project X"
- Calendar sync across all providers

### 5. **Database Infrastructure** ✅
**Location**: `docker-compose.yml`

**Services running**:
- PostgreSQL 16 + pgvector (port 5432)
- Redis 7 (port 6379)
- Neo4j 5 Community (ports 7474, 7687)

**What they're used for**:
- **PostgreSQL**: Vector embeddings for mem0, user data
- **Redis**: APScheduler job store, caching, session state
- **Neo4j**: Knowledge graph, conversation relationships

---

## ⏳ What's NOT Built Yet (Pending Implementation)

### Phase 4: Multimedia Processing
**Status**: NOT STARTED
**Estimated**: 2 hours

**What to build**:
1. **Voice Transcription Service** (`app/services/voice_transcription.py`)
   - Use OpenAI Whisper
   - Accept voice file path or URL
   - Return transcribed text
   - Support Telegram voice notes

2. **Image Analysis Service** (`app/services/image_analysis.py`)
   - Use GPT-4 Vision API
   - Accept image file path or URL
   - Return image description/analysis
   - Support Telegram photos

3. **Multimedia Agent** (`app/agents/multimedia_agent.py`)
   - Handle voice and image inputs
   - Route to appropriate service
   - Return processed results

**Example implementation**:
```python
# app/services/voice_transcription.py
import whisper

model = whisper.load_model("base")

async def transcribe_voice(file_path: str) -> str:
    """Transcribe voice file to text"""
    result = model.transcribe(file_path)
    return result["text"]

# Usage in agent
async def handle_voice_note(voice_url: str, user_id: str):
    # Download voice file
    file_path = await download_file(voice_url)

    # Transcribe
    text = await transcribe_voice(file_path)

    # Process with Jenny
    response = await orchestrator.invoke(text, {"user_id": user_id})
    return response
```

### Phase 5: Dashboard Backend APIs
**Status**: NOT STARTED
**Estimated**: 3 hours

**What to build**:
1. **Analytics Endpoints** (`app/api/dashboard.py`)
   - `/dashboard/analytics` - Usage stats
   - `/dashboard/insights` - AI-generated insights
   - `/dashboard/memory-stats` - Memory usage
   - `/dashboard/calendar-stats` - Calendar stats

2. **Analytics Service** (`app/services/analytics.py`)
   - Track user interactions
   - Calculate usage metrics
   - Generate reports

3. **Insights Service** (`app/services/insights.py`)
   - Analyze conversation patterns
   - Generate productivity insights
   - Suggest optimizations

**Example implementation**:
```python
# app/api/dashboard.py
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard")

@router.get("/analytics")
async def get_analytics(user_id: str):
    """Get user analytics"""
    return {
        "total_conversations": await count_conversations(user_id),
        "total_reminders": await count_reminders(user_id),
        "calendar_events": await count_calendar_events(user_id),
        "most_active_times": await get_active_times(user_id)
    }
```

### Phase 6: Security & Encryption
**Status**: NOT STARTED
**Estimated**: 2 hours

**What to build**:
1. **Encryption Service** (`app/security/encryption.py`)
   - End-to-end encryption for sensitive data
   - Password hashing
   - Secure credential storage

2. **Authentication** (`app/security/auth.py`)
   - JWT token generation
   - User authentication
   - Session management

3. **Rate Limiting** (`app/security/rate_limit.py`)
   - Prevent API abuse
   - Per-user rate limits

**Example implementation**:
```python
# app/security/encryption.py
from cryptography.fernet import Fernet
import os

class EncryptionService:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY").encode()
        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### Phase 7: Testing & Documentation
**Status**: PARTIAL
**Estimated**: 2 hours

**What to build**:
1. **Integration Tests** (`tests/integration/`)
   - Test calendar sync end-to-end
   - Test reminder scheduling
   - Test memory persistence

2. **API Documentation**
   - OpenAPI/Swagger docs
   - Usage examples
   - Error handling guide

3. **User Guide** (`docs/USER_GUIDE.md`)
   - How to set up calendars
   - How to use reminders
   - How to interact via Telegram

---

## 🔧 How to Extend Jenny

### Adding a New Agent

Jenny uses **CrewAI** for intelligent multi-agent orchestration. No keyword matching needed!

1. **Define agent in `app/crew/config/agents.yaml`:**

```yaml
your_agent:
  role: >
    Your Agent Role
  goal: >
    What this agent should accomplish
  backstory: >
    Detailed description of agent's expertise and capabilities
```

2. **Add agent method in `app/crew/crew.py`:**

```python
@agent
def your_agent(self) -> Agent:
    return Agent(
        config=self.agents_config['your_agent'],
        tools=[YourTool1(), YourTool2()],  # Optional tools
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )
```

3. **Create CrewAI tools in `app/crew/tools.py`** (if needed):

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class YourToolInput(BaseModel):
    param: str = Field(..., description="Parameter description")

class YourTool(BaseTool):
    name: str = "your_tool"
    description: str = "Detailed description of what this tool does"
    args_schema: type[BaseModel] = YourToolInput

    def _run(self, param: str) -> str:
        """Implement your tool logic here"""
        result = do_something(param)
        return f"Result: {result}"
```

4. **Test it** (CrewAI manager will automatically route):

```bash
# Natural language - no keywords needed!
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"Help me with [task your agent handles]"}'
```

CrewAI's hierarchical manager will understand the intent and route to your agent automatically!

### Adding a New Calendar Provider

1. **Create provider**: `app/integrations/calendar/your_provider.py`

Implement the `CalendarProvider` protocol from `base.py`:
```python
from app.integrations.calendar.base import CalendarProvider, CalendarEvent

class YourCalendarProvider:
    async def list_events(self, start, end, max_results=100):
        # Your implementation
        pass

    async def create_event(self, title, start, end, **kwargs):
        # Your implementation
        pass
```

2. **Add to unified calendar**: `app/integrations/calendar/unified.py`

```python
from app.integrations.calendar.your_provider import YourCalendarProvider

class UnifiedCalendar:
    def __init__(self, user_id):
        self.providers = {
            "google": GoogleCalendarProvider(user_id),
            "microsoft": MicrosoftCalendarProvider(user_id),
            "apple": AppleCalendarProvider(user_id),
            "your_provider": YourCalendarProvider(user_id),  # Add here
        }
```

### Adding a New Notification Channel

Currently using Telegram only. To add another (e.g., Email, SMS):

1. **Create notification service**: `app/services/notifications.py`

```python
async def send_notification(user_id: str, message: str, channel: str = "telegram"):
    """Send notification via specified channel"""
    if channel == "telegram":
        await send_telegram_message(user_id, message)
    elif channel == "email":
        await send_email(user_id, message)
    elif channel == "sms":
        await send_sms(user_id, message)
```

2. **Update reminder service**: `app/scheduler/reminder_service.py`

```python
async def send_reminder_notification(user_id, message, reminder_id, metadata=None):
    channel = metadata.get("channel", "telegram") if metadata else "telegram"
    await send_notification(user_id, message, channel)
```

---

## 🗂️ File Structure Reference

```
Jenny/
├── app/
│   ├── api/
│   │   └── routes.py              # Main API endpoints
│   ├── core/
│   │   ├── db.py                  # PostgreSQL connection
│   │   ├── cache.py               # Redis caching
│   │   └── graph.py               # Neo4j connection
│   ├── crew/                      # ✅ CrewAI orchestration (MAIN)
│   │   ├── __init__.py
│   │   ├── crew.py                # JennyCrew (@CrewBase pattern)
│   │   ├── tools.py               # CrewAI tools
│   │   └── config/
│   │       ├── agents.yaml        # Agent definitions
│   │       └── tasks.yaml         # Task templates
│   ├── integrations/
│   │   └── calendar/              # ✅ Calendar integrations
│   │       ├── base.py
│   │       ├── google_calendar.py
│   │       ├── microsoft_calendar.py
│   │       ├── apple_calendar.py
│   │       └── unified.py
│   ├── mem0/
│   │   ├── client.py              # ✅ Fallback mem0 client
│   │   └── server/
│   │       └── main.py            # Custom mem0 microservice
│   ├── scheduler/                 # ✅ Scheduling system
│   │   ├── scheduler.py
│   │   └── reminder_service.py
│   ├── services/
│   │   └── memory.py              # ✅ Official mem0 integration
│   └── strands/
│       ├── context_store.py       # Session management (Redis)
│       ├── orchestrator.py        # (Legacy - deprecated)
│       ├── conversation.py        # (Legacy - deprecated)
│       └── agents/                # (Legacy - kept for reference)
│           ├── calendar_agent.py
│           ├── memory_agent.py
│           ├── task_agent.py
│           └── ...
├── docker-compose.yml             # ✅ PostgreSQL, Redis, Neo4j
├── requirements.txt               # ✅ All dependencies
├── .env.example                   # ✅ Configuration template
├── ARCHITECTURE.md                # ✅ System design
├── CREWAI_BEST_PRACTICES.md       # ✅ CrewAI implementation guide
├── IMPLEMENTATION_GUIDE.md        # ✅ This file (YOU ARE HERE)
├── INSTALL.md                     # Setup instructions
└── README.md                      # Project overview
```

---

## 🚀 Quick Start for Developers

### Setting Up Development Environment

```bash
# 1. Clone and navigate
cd Jenny

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start databases
docker-compose up -d

# 5. Start services
python start.py
```

### Making Your First Contribution

**Scenario**: Add email notifications

1. **Create service** (`app/services/email_service.py`):
```python
import smtplib
from email.mime.text import MIMEText

async def send_email(to: str, subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("SMTP_FROM")
    msg['To'] = to

    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
        server.send_message(msg)
```

2. **Integrate with reminders**:
```python
# In app/scheduler/reminder_service.py
from app.services.email_service import send_email

async def send_reminder_notification(user_id, message, ...):
    # Existing Telegram notification
    await _send_telegram_reminder(user_id, message)

    # NEW: Also send email if configured
    if user_email := get_user_email(user_id):
        await send_email(user_email, "Reminder", message)
```

3. **Test it**:
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"remind me in 5 minutes to test email"}'
```

---

## 📋 Implementation Checklist

Use this when implementing pending features:

### Phase 4: Multimedia
- [ ] Install `openai-whisper` package
- [ ] Create `app/services/voice_transcription.py`
- [ ] Create `app/services/image_analysis.py`
- [ ] Add file upload endpoints in `app/api/routes.py`
- [ ] Test with Telegram voice notes
- [ ] Test with Telegram photos

### Phase 5: Dashboard
- [ ] Create `app/api/dashboard.py` router
- [ ] Implement analytics tracking
- [ ] Create insights generation service
- [ ] Add authentication for dashboard endpoints
- [ ] Test all endpoints

### Phase 6: Security
- [ ] Generate encryption key
- [ ] Create encryption service
- [ ] Implement JWT authentication
- [ ] Add rate limiting middleware
- [ ] Audit all endpoints for security

### Phase 7: Documentation
- [ ] Write integration tests
- [ ] Generate OpenAPI docs
- [ ] Create user guide
- [ ] Add code examples
- [ ] Update README

---

## 🎓 Key Concepts

### How Memory Works

```
User: "I love coffee"
         ↓
Jenny saves to mem0
         ↓
PostgreSQL: Stores text + vector embedding
Neo4j: Creates relationship (User)-[:LIKES]->(Coffee)
         ↓
Later...
         ↓
User: "What do I like?"
         ↓
Jenny searches mem0
         ↓
Vector similarity search finds "coffee" memory
         ↓
Jenny: "You mentioned you love coffee"
```

### How Reminders Work

```
User: "Remind me in 2 hours to call mom"
         ↓
Calendar Agent parses: time = now + 2 hours
         ↓
Scheduler creates job in Redis
         ↓
APScheduler waits...
         ↓
2 hours later...
         ↓
Job fires → send_reminder_notification()
         ↓
Telegram message sent: "🔔 Reminder: call mom"
```

### How Calendar Sync Works

```
User: "What's on my calendar today?"
         ↓
Calendar Agent activates
         ↓
Unified Calendar queries all providers:
  ├─ Google Calendar API
  ├─ Microsoft Graph API
  └─ Apple CalDAV
         ↓
Merge & deduplicate events
         ↓
Format response
         ↓
Jenny: "You have 3 events today:
- Team meeting at 10am (google)
- Lunch at 12pm (outlook)
- Doctor at 3pm (apple)"
```

---

## 🐛 Common Issues & Solutions

### Issue: "mem0ai not available"
**Solution**: The app falls back to custom implementation automatically. To use official mem0:
```bash
pip install mem0ai
```

### Issue: "Scheduler not starting"
**Solution**: Check Redis is running:
```bash
docker-compose ps
redis-cli ping  # Should return PONG
```

### Issue: "Calendar not connecting"
**Solution**: Ensure you've set up OAuth credentials in `.env`:
```bash
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...
```

### Issue: "Telegram bot not responding"
**Solution**: Check bot token is correct:
```bash
# Test with curl
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```

---

## 📚 Additional Resources

- **Mem0 Docs**: https://docs.mem0.ai/
- **APScheduler Docs**: https://apscheduler.readthedocs.io/
- **Google Calendar API**: https://developers.google.com/calendar
- **Microsoft Graph API**: https://docs.microsoft.com/en-us/graph/
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

## 🎯 Success Criteria

When is Jenny "complete"?

- ✅ Phase 1-3 implemented (Mem0, Calendar, Scheduler)
- ⏳ Phase 4: Voice/image processing works
- ⏳ Phase 5: Dashboard provides insights
- ⏳ Phase 6: Encryption enabled
- ⏳ Phase 7: Tests passing, docs complete

**Final Goal**: A user can:
1. Talk to Jenny via Telegram
2. Send voice notes that get transcribed
3. Ask Jenny to check calendar
4. Set reminders naturally
5. Jenny learns and remembers preferences
6. All data stays private (100% local)
7. Dashboard shows productivity insights

---

**This guide should be updated** as new features are implemented. When you add something, document it here so the next developer (human or AI) knows what you built!

**Last Updated**: 2025-11-18
**Status**: Phases 1-3 complete, 4-7 pending
