# LLM Model Configuration Guide

This guide explains how to configure different LLM models for Jenny AI Assistant's various components.

## Overview

Jenny uses multiple LLM models for different purposes:

1. **CrewAI Agents** - Powers Jenny's conversational AI and task delegation
2. **Mem0 Memory Operations** - Used for understanding and retrieving memories
3. **Mem0 Embeddings** - Creates semantic embeddings for storing memories

## Quick Start

### Recommended Configuration (Cost-Optimized)

```bash
# CrewAI: Use DeepSeek Chat for agents
CREWAI_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# Mem0: Use DeepSeek for memory retrieval, OpenAI for embeddings
MEM0_LLM_PROVIDER=deepseek
MEM0_LLM_MODEL=deepseek-chat
MEM0_EMBED_MODEL=text-embedding-3-small

# API Keys
OPENAI_API_KEY=your-openai-api-key  # For embeddings
```

### Alternative: Gemini Configuration

```bash
# CrewAI: Use Gemini 2.5 Flash for agents
CREWAI_LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# Mem0: Still use DeepSeek for cost savings
MEM0_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
MEM0_LLM_MODEL=deepseek-chat
MEM0_EMBED_MODEL=text-embedding-3-small

# API Keys
OPENAI_API_KEY=your-openai-api-key  # For embeddings
```

## Component Details

### 1. CrewAI Agents (`CREWAI_LLM_PROVIDER`)

**What it does**: Powers all of Jenny's conversational agents including:
- General Assistant (main conversation handler)
- Memory Keeper (memory management)
- Task Coordinator (task/reminder management)
- Calendar Coordinator (calendar operations)
- Profile Manager (user preferences)

**Configuration**:

```bash
CREWAI_LLM_PROVIDER=<openai|deepseek|gemini>
```

#### Option A: DeepSeek (Recommended for Cost)

```bash
CREWAI_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat
```

**Pros**:
- Very cost-effective (~20x cheaper than GPT-4)
- Good performance for most conversational tasks
- Fast response times

**Cons**:
- Slightly less capable than GPT-4 for complex reasoning
- May need more explicit instructions

#### Option B: Gemini 2.5 Flash (Recommended for Speed)

```bash
CREWAI_LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL=gemini-2.0-flash-exp
```

**Pros**:
- Very fast response times
- Good multimodal capabilities
- Competitive cost

**Cons**:
- Requires Google Cloud account
- API may have rate limits

**Note**: You need to install `langchain-google-genai`:
```bash
pip install langchain-google-genai
```

#### Option C: OpenAI (Most Reliable)

```bash
CREWAI_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

**Pros**:
- Most reliable and well-tested
- Best for complex reasoning
- Strong instruction following

**Cons**:
- More expensive than alternatives
- May be slower for simple tasks

### 2. Mem0 Memory Operations (`MEM0_LLM_PROVIDER`)

**What it does**: Used by Mem0 when:
- Understanding user queries about memories
- Retrieving relevant memories based on context
- Generating memory summaries
- Reasoning about stored information

**Configuration**:

```bash
MEM0_LLM_PROVIDER=<openai|deepseek>
MEM0_LLM_MODEL=<model-name>
```

#### Recommended: DeepSeek

```bash
MEM0_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
MEM0_LLM_MODEL=deepseek-chat
```

**Why**: Memory retrieval is frequent but doesn't require the most advanced reasoning. DeepSeek provides excellent cost savings here.

#### Alternative: OpenAI

```bash
MEM0_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
MEM0_LLM_MODEL=gpt-4o-mini
```

**When to use**: If you need more reliable memory retrieval and cost is not a concern.

### 3. Mem0 Embeddings (`MEM0_EMBED_MODEL`)

**What it does**: Creates semantic embeddings when storing memories. These embeddings enable:
- Semantic search of memories
- Finding similar memories
- Contextual memory retrieval

**Configuration**:

```bash
MEM0_EMBED_MODEL=text-embedding-3-small
OPENAI_API_KEY=your-openai-api-key
```

**⚠️ Important**: Always use OpenAI's `text-embedding-3-small` for embeddings:
- Industry-leading quality
- Cost-effective ($0.02 per 1M tokens)
- Required for consistent semantic search
- Well-optimized for pgvector

**Do NOT change this** unless you have specific requirements and understand the implications for memory retrieval quality.

## Cost Comparison

Based on typical usage patterns for Jenny:

| Configuration | Monthly Cost (Est.) | Performance | Use Case |
|--------------|---------------------|-------------|----------|
| DeepSeek + OpenAI Embeddings | $5-15 | Good | Recommended for most users |
| Gemini + DeepSeek Mem0 | $10-25 | Very Good | Best for speed + cost balance |
| OpenAI Everything | $50-150 | Excellent | Best for reliability |

**Note**: Costs assume ~10k agent calls/month and 5k memory operations/month.

## Environment Variables Reference

### Required for All Configurations

```bash
# OpenAI (always needed for embeddings)
OPENAI_API_KEY=your-openai-api-key

# Mem0 Embeddings (always use this)
MEM0_EMBED_MODEL=text-embedding-3-small
```

### For DeepSeek

```bash
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# Use for CrewAI
CREWAI_LLM_PROVIDER=deepseek

# Use for Mem0
MEM0_LLM_PROVIDER=deepseek
MEM0_LLM_MODEL=deepseek-chat
```

### For Gemini

```bash
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-google-api-key  # Same as GOOGLE_API_KEY
GEMINI_MODEL=gemini-2.0-flash-exp

# Use for CrewAI
CREWAI_LLM_PROVIDER=gemini
```

### For OpenAI

```bash
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo, etc.

# Use for CrewAI
CREWAI_LLM_PROVIDER=openai

# Use for Mem0
MEM0_LLM_PROVIDER=openai
MEM0_LLM_MODEL=gpt-4o-mini
```

## Getting API Keys

### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Add credits to your account ($5-10 is enough to start)

### DeepSeek
1. Visit https://platform.deepseek.com/
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Add credits (very affordable, $5 can last months)

### Google (for Gemini)
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create an API key
4. Enable "Generative Language API" in Google Cloud Console

## Testing Your Configuration

After setting up your environment variables:

1. **Test CrewAI agents**:
```bash
# Start the application
python app/main.py

# Send a test message via Telegram or API
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "hi", "user_id": "test_user"}'
```

2. **Check logs** for model initialization:
```bash
# You should see logs like:
# INFO:app.crew.crew:Using DeepSeek Chat for CrewAI agents
# INFO:app.services.memory:Mem0 client initialized successfully
```

3. **Test memory operations**:
```bash
# Store a memory
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "remember that I love pizza", "user_id": "test_user"}'

# Retrieve the memory
curl -X POST http://localhost:8044/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "what do I like to eat?", "user_id": "test_user"}'
```

## Troubleshooting

### "Module not found: langchain_google_genai"

**Solution**: Install the Gemini langchain integration:
```bash
pip install langchain-google-genai
```

### "OpenAI API key not found"

**Solution**: Even if using DeepSeek/Gemini for agents, you still need OpenAI API key for embeddings:
```bash
export OPENAI_API_KEY=your-openai-api-key
```

### "DeepSeek API authentication failed"

**Solution**: Check your API key and ensure you have credits:
1. Visit https://platform.deepseek.com/
2. Check your API key is correct
3. Verify you have credits in your account

### "Mem0 client initialization failed"

**Solution**: Check all required environment variables are set:
```bash
# PostgreSQL (required)
echo $PGHOST $PGPORT $PGDATABASE $PGUSER $PGPASSWORD

# Embeddings (required)
echo $OPENAI_API_KEY $MEM0_EMBED_MODEL

# LLM (optional but recommended)
echo $DEEPSEEK_API_KEY $MEM0_LLM_PROVIDER
```

## Best Practices

1. **Start with DeepSeek**: It's cost-effective and works well for most use cases.

2. **Always use OpenAI embeddings**: The `text-embedding-3-small` model is the best balance of cost and quality.

3. **Monitor costs**: Set up billing alerts in your API provider dashboards.

4. **Test incrementally**: Test with a small number of queries first before deploying to production.

5. **Keep API keys secure**: Never commit `.env` files to git. Use `.env.example` as a template.

6. **Use environment-specific configs**: Have different configs for development, staging, and production.

## Migration Guide

### From OpenAI-only to DeepSeek

1. Get a DeepSeek API key: https://platform.deepseek.com/
2. Update `.env`:
```bash
DEEPSEEK_API_KEY=your-deepseek-api-key
CREWAI_LLM_PROVIDER=deepseek
MEM0_LLM_PROVIDER=deepseek
```
3. Keep `OPENAI_API_KEY` for embeddings
4. Restart the application
5. Test with a few queries
6. Monitor responses for quality

### From DeepSeek to Gemini

1. Get a Google API key: https://makersuite.google.com/app/apikey
2. Install Gemini integration: `pip install langchain-google-genai`
3. Update `.env`:
```bash
GOOGLE_API_KEY=your-google-api-key
CREWAI_LLM_PROVIDER=gemini
```
4. Keep DeepSeek for Mem0 (cost savings)
5. Restart and test

## Support

For issues or questions about model configuration:
- Check the logs: `tail -f logs/jenny.log`
- Review documentation: [README.md](README.md), [SETUP.md](SETUP.md)
- Open an issue: https://github.com/your-repo/Jenny/issues

## Summary

**For Claude Code**: When setting up Jenny, use this configuration:

```bash
# Recommended for Claude Code
CREWAI_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

MEM0_LLM_PROVIDER=deepseek
MEM0_LLM_MODEL=deepseek-chat
MEM0_EMBED_MODEL=text-embedding-3-small

OPENAI_API_KEY=your-openai-api-key  # For embeddings only
```

This provides the best cost/performance balance for automated agents.
