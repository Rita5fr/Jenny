# Jenny - Personal AI Assistant

Jenny is a local-first AI orchestration platform designed as a personal assistant with multi-agent architecture, semantic memory, and multi-modal support.

## 🚀 Quick Start

**New to Jenny?** Follow the [Complete Setup Guide (SETUP.md)](SETUP.md) for detailed step-by-step instructions.

### Quick Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start ALL databases locally:**
   ```bash
   docker-compose up -d
   ```
   This starts PostgreSQL, Redis, and Neo4j - **no cloud services needed!**

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key (defaults work for local databases!)
   ```

4. **Start services:**
   ```bash
   # Terminal 1: Mem0 service
   python -m uvicorn app.mem0.server.main:app --port 8081

   # Terminal 2: Main app
   python -m uvicorn app.main:app --port 8044
   ```

5. **Test:**
   ```bash
   curl http://localhost:8044/health
   ```

## Features

### Core Capabilities

#### 1. **Memory Agent** ✓
- Persistent semantic memory storage with vector embeddings
- Automatic preference detection ("my favorite", "I like", "I love", "I prefer")
- Memory search with similarity ranking
- Powered by Mem0 microservice with pgvector

#### 2. **Task Agent** ✓
- Create, list, complete, and delete tasks/reminders
- Natural language date parsing:
  - Relative: "tomorrow", "today", "next week"
  - Absolute: "2024-12-31"
- Recurring tasks support: daily, weekly, monthly
- Multi-step conversation for task creation
- Postgres-backed storage

#### 3. **Profile Agent** ✓
- Manage user preferences across categories:
  - Drink preferences
  - Dietary preferences
  - Habits
  - Music preferences
- Upsert operations (create or update)

#### 4. **Recall Agent** ✓
- Question answering with memory context
- Combines memory search + task list for comprehensive answers
- Powered by DeepSeek reasoner for intelligent responses

#### 5. **Knowledge Agent** ✓
- External knowledge retrieval
- Queries Gemini 2.5 Flash for information
- Graceful fallback when API unavailable

#### 6. **Voice Processing** ✓
- Audio transcription using Gemini Audio API
- Multi-modal message handling
- Automatic text extraction from voice messages

#### 7. **Session Management** ✓
- Redis-backed context persistence
- Conversation history (max 20 messages)
- 30-minute session TTL
- Tracks last intent and metadata

#### 8. **Neo4j Interaction Logging** ✓
- Full interaction tracking in graph database
- Stores queries, responses, and agent routing
- Graceful degradation if unavailable

#### 9. **Telegram Bot** ✓
- Full bot interface with multi-modal support
- Handlers for:
  - Text messages
  - Voice/audio messages
  - Photo messages
- Uses same orchestrator as HTTP API

#### 10. **Advanced Tools Agent** ✓ NEW!
- Integrated with strands-agents-tools library (50+ tools)
- Capabilities include:
  - Web search and content extraction
  - File operations (read, write, edit)
  - HTTP requests to APIs
  - Python code execution (REPL)
  - And more!
- Ask: "list tools" to see all available tools

### Planned Features (Stubs)

- **Calendar Agent** - Meeting and event management
- **Mail Agent** - Email integration
- **Research Agent** - Web research capabilities
- **Image Processing** - Image understanding and analysis

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Jenny Platform                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐        ┌──────────────┐      │
│  │ Telegram Bot │        │  HTTP API    │      │
│  └──────┬───────┘        └──────┬───────┘      │
│         │                       │              │
│         └───────────┬───────────┘              │
│                     │                          │
│            ┌────────▼────────┐                 │
│            │  Orchestrator   │                 │
│            │ (Intent Router) │                 │
│            └────────┬────────┘                 │
│                     │                          │
│      ┌──────────────┼──────────────┐          │
│      │              │              │          │
│  ┌───▼───┐     ┌───▼────┐    ┌───▼────┐     │
│  │Memory │     │  Task  │    │Profile │     │
│  │Agent  │     │ Agent  │    │ Agent  │     │
│  └───┬───┘     └───┬────┘    └───┬────┘     │
│      │             │              │          │
│  ┌───▼───┐     ┌───▼────┐    ┌───▼────┐     │
│  │Recall │     │Knowledge│   │ Voice  │     │
│  │Agent  │     │ Agent   │   │ Agent  │     │
│  └───────┘     └─────────┘   └────────┘     │
│                                              │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼─────┐      ┌─────▼──────┐
    │ Mem0 μS  │      │   Core     │
    │(pgvector)│      │ Services   │
    └────┬─────┘      └─────┬──────┘
         │                  │
    ┌────▼────────┬─────────▼────┬────────────┐
    │  Postgres   │    Redis     │   Neo4j    │
    │  (Local)    │   (Local)    │  (Local)   │
    │  +pgvector  │              │            │
    └─────────────┴──────────────┴────────────┘

    🎉 All services run locally via docker-compose!
```

## Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Python 3.11+** - Runtime

### Databases & Infrastructure

**🎉 100% Local Setup - No Cloud Services Required!**

#### PostgreSQL + pgvector (Local via Docker)
- Semantic memory storage with vector embeddings
- Task management and profile storage
- Runs completely locally for privacy and control
- Uses ankane/pgvector Docker image
- Automatic database initialization with extensions

#### Redis (Local via Docker)
- Session cache and context persistence
- Conversation history storage
- Zero latency - runs on localhost
- Persistent data with append-only file

#### Neo4j (Local via Docker)
- Graph database for interaction logging
- Tracks user queries and agent responses
- Includes web interface at http://localhost:7474
- APOC plugin included for advanced queries

### AI/LLM Integration
- **OpenAI** - Embeddings (text-embedding-3-small)
- **Gemini** - Audio transcription and knowledge queries (optional)
- **DeepSeek** - Reasoning for recall agent (optional)

### Agent Tools & Frameworks
- **strands-agents-tools** - 50+ pre-built tools for file ops, web search, code execution
- **python-telegram-bot 22.5** - Telegram bot integration

## Installation

> **📖 For detailed step-by-step instructions, see [SETUP.md](SETUP.md)**

### Prerequisites
- Python 3.11 or higher
- Docker and Docker Compose
- OpenAI API key

**That's it! No cloud accounts needed** - everything runs locally.

### Quick Setup

1. **Clone and install dependencies**
   ```bash
   git clone <repository-url>
   cd Jenny
   pip install -r requirements.txt
   ```

2. **Start ALL databases locally**
   ```bash
   docker-compose up -d
   ```
   This starts PostgreSQL (with pgvector), Redis, and Neo4j.

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenAI key:
   ```bash
   # Required - get from https://platform.openai.com/api-keys
   OPENAI_API_KEY=sk-proj-your-key-here

   # Database defaults (no changes needed!)
   # PGHOST=localhost
   # PGUSER=jenny
   # PGPASSWORD=jenny123
   # REDIS_URL=redis://localhost:6379
   # NEO4J_PASSWORD=jenny123
   ```

4. **Start services**
   ```bash
   # Terminal 1: Mem0 microservice
   python -m uvicorn app.mem0.server.main:app --port 8081

   # Terminal 2: Main application
   python -m uvicorn app.main:app --port 8044
   ```

5. **Verify installation**
   ```bash
   curl http://localhost:8044/health
   # Should return: {"ok":true}
   ```

### Docker Commands

```bash
# Start databases
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop databases
docker-compose down

# Access Neo4j browser
open http://localhost:7474
```

## API Endpoints

### Main Application (Port 8044)

#### Health Check
```bash
GET /health
```

#### Ask Jenny
```bash
POST /ask
Content-Type: application/json

{
  "user_id": "user123",
  "text": "Remember that my favorite color is blue"
}
```

#### Direct Memory Operations
```bash
POST /demo/remember
{
  "user_id": "user123",
  "text": "I love pizza"
}

GET /demo/search?user_id=user123&q=food&k=5
```

### Mem0 Microservice (Port 8081)

#### Add Memory
```bash
POST /memories
{
  "messages": [{"role": "user", "content": "I prefer tea over coffee"}],
  "user_id": "user123"
}
```

#### Search Memories
```bash
GET /memories/search?q=beverage&user_id=user123&k=5
```

## Usage Examples

### Memory Management
```bash
# Save a preference
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "text": "My favorite drink is green tea"}'

# Ask about preferences
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "text": "What do I like to drink?"}'
```

### Task Management
```bash
# Create a task
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "text": "Remind me to buy groceries tomorrow"}'

# List tasks
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "text": "List my tasks"}'

# Complete a task
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "text": "Complete task <task-id>"}'
```

### Knowledge Queries
```bash
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "text": "Tell me about the benefits of green tea"}'
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Current test coverage:
- ✓ Memory storage routing
- ✓ Task management routing
- ✓ General fallback behavior
- ✓ Voice message processing
- ✓ Recall agent selection
- ✓ Knowledge agent routing

## Development

### Project Structure
```
Jenny/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API routes
│   ├── bots/
│   │   └── telegram_bot.py  # Telegram bot
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cache.py         # Redis utilities
│   │   ├── config.py        # Settings management
│   │   ├── db.py            # Postgres connection
│   │   └── graph.py         # Neo4j utilities
│   ├── mem0/
│   │   └── server/
│   │       └── main.py      # Mem0 microservice
│   └── strands/
│       ├── __init__.py
│       ├── orchestrator.py  # Intent routing
│       ├── conversation.py  # Message handling
│       ├── context_store.py # Session management
│       └── agents/
│           ├── memory_agent.py
│           ├── task_agent.py
│           ├── profile_agent.py
│           ├── recall_agent.py
│           ├── knowledge_agent.py
│           └── voice_agent.py
├── tests/
│   ├── test_phase1.py
│   └── test_phase2.py
├── requirements.txt
└── .env.example
```

### Adding New Agents

1. Create agent file in `app/strands/agents/`
2. Implement agent function with signature: `async def agent(query: str, context: Dict) -> Dict`
3. Register in `orchestrator.py`
4. Add intent keywords to `INTENT_MAP`

### Code Quality

The codebase follows modern Python best practices:
- ✓ Type hints throughout
- ✓ Async/await for I/O operations
- ✓ Proper error handling and logging
- ✓ Pydantic for data validation
- ✓ Modern FastAPI patterns (lifespan events)

## Recent Improvements

### Bug Fixes (Latest Commit)
- ✓ Fixed broken `/api/orchestrate` endpoint
- ✓ Fixed regex escaping in date parsing
- ✓ Modernized Pydantic validators
- ✓ Replaced deprecated FastAPI lifecycle events
- ✓ Added comprehensive error logging
- ✓ Made database connections optional for graceful startup
- ✓ Added missing `pydantic-settings` dependency

### Features Working
- ✓ All 9 core agents functional
- ✓ Multi-modal support (text, voice, images)
- ✓ Session persistence
- ✓ Conversation history
- ✓ Intent-based routing
- ✓ Graceful degradation

## Troubleshooting

### Database Connection Issues
The app will start even if databases are unavailable, with warnings logged. Database-dependent features will be disabled gracefully.

### Missing API Keys
- Memory features require OpenAI API key for embeddings
- Voice transcription requires Gemini API key (optional)
- Knowledge queries work with Gemini API key (optional)
- Recall agent uses DeepSeek API key (optional)

### Telegram Bot Not Starting
Ensure `TELEGRAM_BOT_TOKEN` is set in `.env` and valid.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and feature requests, please open an issue on GitHub.
