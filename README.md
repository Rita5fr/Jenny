# Jenny - Personal AI Assistant

Jenny is a local-first AI orchestration platform designed as a personal assistant with multi-agent architecture, semantic memory, and multi-modal support.

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
    │  (Neon)     │  (Upstash)   │  (Aura)    │
    └─────────────┴──────────────┴────────────┘
```

## Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Python 3.11+** - Runtime

### Databases
- **PostgreSQL + pgvector** - Semantic memory storage (Neon hosted)
- **Redis** - Session cache and context (Upstash)
- **Neo4j** - Graph database for interaction logging (Aura)

### AI/LLM Integration
- **OpenAI** - Embeddings (text-embedding-3-small)
- **Gemini** - Audio transcription and knowledge queries
- **DeepSeek** - Reasoning for recall agent

### Bot Framework
- **python-telegram-bot 22.5** - Telegram integration

## Installation

### Prerequisites
- Python 3.11 or higher
- External services (or local alternatives):
  - PostgreSQL database
  - Redis instance
  - Neo4j database (optional)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Jenny
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```bash
# Postgres (Neon or local)
PGHOST=<postgres-host>
PGPORT=5432
PGDATABASE=mem0
PGUSER=<username>
PGPASSWORD=<password>
PGSSLMODE=require  # for Neon

# Redis (Upstash or local)
REDIS_URL=redis://<host>:<port>

# Neo4j (optional)
NEO4J_URL=neo4j://<host>:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>

# Mem0 service
MEMO_BASE_URL=http://127.0.0.1:8081

# API Keys
OPENAI_API_KEY=<your-key>
GEMINI_API_KEY=<your-key>  # optional
DEEPSEEK_API_KEY=<your-key>  # optional

# Telegram (optional)
TELEGRAM_BOT_TOKEN=<your-token>

# Monitoring (optional)
SENTRY_DSN=<your-dsn>
```

4. **Start the Mem0 microservice**
```bash
python -m uvicorn app.mem0.server.main:app --host 0.0.0.0 --port 8081
```

5. **Start the main application**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8044
```

6. **Start the Telegram bot** (optional)
```bash
python app/bots/telegram_bot.py
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
