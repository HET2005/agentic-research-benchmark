# Agent Memory Solutions for Agentic Pipelines

## Overview
Memory solutions allow agents to persist information across sessions, 
recall past interactions, and build knowledge over time.

---

## Complete List

### 1. Letta (formerly MemGPT)
- **What it does**: Self-editing memory for LLM agents. Agents can read/write their own memory.
- **Memory types**: In-context, archival, recall
- **Persistence**: ✅ Cross-session
- **Self-editing**: ✅ Yes
- **Integration**: LangChain, custom
- **Hosting**: Self-hosted or cloud
- **Best for**: Long-running conversational agents that need to manage their own memory
- **GitHub**: github.com/letta-ai/letta

---

### 2. mem0
- **What it does**: Persistent memory layer for AI apps. Stores user preferences, facts, history.
- **Memory types**: User memory, agent memory, session memory
- **Persistence**: ✅ Cross-session
- **Self-editing**: ❌ No
- **Integration**: LangChain, AutoGen, CrewAI, custom
- **Hosting**: Self-hosted or hosted API
- **Best for**: Personalized AI assistants and multi-framework projects
- **GitHub**: github.com/mem0ai/mem0

---

### 3. Zep
- **What it does**: Long-term memory server for LLM apps with auto-summarization.
- **Memory types**: Chat history, semantic memory, document memory
- **Persistence**: ✅ Cross-session
- **Self-editing**: ❌ No
- **Integration**: LangChain, LlamaIndex, custom
- **Hosting**: Self-hosted or cloud
- **Best for**: Chatbots needing conversation history with fast semantic retrieval
- **GitHub**: github.com/getzep/zep

---

### 4. LangChain Memory (Built-in)
- **What it does**: In-session memory for LangChain agents.
- **Memory types**: Buffer, Summary, Vector store, Entity
- **Persistence**: ❌ Session only (resets between runs)
- **Self-editing**: ❌ No
- **Integration**: LangChain only
- **Hosting**: In-process
- **Best for**: Simple single-session LangChain agents

---

### 5. CrewAI Built-in Memory
- **What it does**: Memory system built directly into CrewAI crews.
- **Memory types**: Short-term, long-term, entity, contextual
- **Persistence**: ✅ Long-term via ChromaDB
- **Self-editing**: ❌ No
- **Integration**: CrewAI only
- **Hosting**: Local ChromaDB
- **Best for**: CrewAI-native multi-agent workflows — enable with `memory=True`

---

### 6. Cognee
- **What it does**: Knowledge graph based memory. Builds structured knowledge from conversations.
- **Memory types**: Graph-based knowledge, episodic memory
- **Persistence**: ✅ Cross-session
- **Self-editing**: ❌ No
- **Integration**: LangChain, custom
- **Hosting**: Self-hosted
- **Best for**: Agents needing structured reasoning over past interactions

---

### 7. Motörhead
- **What it does**: Redis-backed memory server with auto-summarization of old context.
- **Memory types**: Chat history with rolling summarization
- **Persistence**: ✅ Cross-session
- **Self-editing**: ❌ No
- **Integration**: LangChain, custom REST API
- **Hosting**: Self-hosted (Redis)
- **Best for**: High-throughput agents needing fast in-memory storage

---

### 8. Vector DBs as Memory (Chroma, Pinecone, Weaviate)
- **What it does**: Store embeddings of past interactions, retrieve via similarity search.
- **Memory types**: Semantic/vector memory
- **Persistence**: ✅ Cross-session
- **Self-editing**: ❌ No
- **Integration**: Any framework
- **Hosting**: Self-hosted or cloud
- **Best for**: Custom memory implementations with semantic retrieval

---

### 9. AutoGen Built-in Memory
- **What it does**: Teachable agent that learns from conversations.
- **Memory types**: Short-term conversation buffer, teachable long-term
- **Persistence**: ⚠️ Limited
- **Self-editing**: ❌ No
- **Integration**: AutoGen only
- **Hosting**: In-process
- **Best for**: AutoGen-native agents that learn from user feedback

---

## Comparison Table

| Library | Persistent | Cross-session | Multi-framework | Self-editing | Difficulty |
|---|---|---|---|---|---|
| **mem0** | ✅ | ✅ | ✅ All 3 | ❌ | Easy |
| **Letta** | ✅ | ✅ | ⚠️ Limited | ✅ | Hard |
| **Zep** | ✅ | ✅ | ⚠️ Partial | ❌ | Medium |
| **CrewAI Memory** | ✅ | ✅ | ❌ CrewAI only | ❌ | Very Easy |
| **LangChain Memory** | ❌ | ❌ | ❌ LangChain only | ❌ | Very Easy |
| **Cognee** | ✅ | ✅ | ⚠️ Limited | ❌ | Medium |
| **Motörhead** | ✅ | ✅ | ✅ Any | ❌ | Medium |
| **Vector DBs** | ✅ | ✅ | ✅ Any | ❌ | Hard |
| **AutoGen Memory** | ⚠️ | ❌ | ❌ AutoGen only | ❌ | Easy |

---

## Recommendation for This Project

### Pick: **mem0 + CrewAI Built-in Memory**

#### Why mem0:
- Works with all 3 frameworks (LangGraph, AutoGen, CrewAI) — single memory layer for the whole benchmark
- Simple API — `memory.add()` and `memory.search()` — minimal code changes
- Free self-hosted option — no extra API cost
- Agents can remember which pipeline-question combinations worked well across runs
- Most actively maintained as of 2024-2025

#### Why also CrewAI built-in:
- Already installed — zero extra dependency
- One line to enable: `crew = Crew(..., memory=True)`
- Gives CrewAI agents short-term + long-term memory instantly

#### Integration Plan:
1. **Phase 1** — Enable `memory=True` in all CrewAI Crew objects (10 minutes)
2. **Phase 2** — Add mem0 as shared memory layer across all 3 frameworks
3. **Phase 3** — Add memory as a 5th evaluation metric in the benchmark scorer

#### Install:
```bash