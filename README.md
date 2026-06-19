# LangGraph Chatbot — Evolution Project

A portfolio project that builds a chatbot three times, each time adding a layer of sophistication. The goal is to show how LangGraph's checkpointer system works by starting from nothing and progressively adding memory, persistence, and UX features.

**Stack:** LangGraph · FastAPI · Streamlit · OpenAI · SQLite

---

## The Evolution

### Stage 1 — Stateless (v0)

The simplest possible chatbot. No memory whatsoever — every message is treated as a brand new conversation. Send two messages and the bot has no idea what you said in the first one.

- LangGraph graph with a single `chat_node`
- Compiled with no checkpointer: `graph.compile()`
- Each request is independent; state is born and dies with the HTTP call
- Useful baseline to understand what "memory" actually means

**Endpoint:** `POST /v0/chat`

---

### Stage 2 — In-Memory Checkpointer (v1)

The first real memory. LangGraph's `InMemorySaver` stores conversation state in a Python dictionary, keyed by `thread_id`. The bot now remembers the full conversation history within a session.

The catch: this memory lives in RAM. Restart the server and everything is gone. It also can't be shared across multiple server processes.

- Compiled with: `graph.compile(checkpointer=InMemorySaver())`
- `thread_id` is passed in every request to identify the conversation
- State persists across messages in the same session

**Endpoint:** `POST /v1/chat`

---

### Stage 3 — SQLite Checkpointer (v2)

The same graph, but now the checkpointer writes state to a SQLite database (`chatbot.db`). Conversations survive server restarts. This is what real persistence looks like.

LangGraph's `SqliteSaver` handles all the serialisation and retrieval automatically — the graph code itself doesn't change at all. Only the `compile()` call changes.

- Compiled with: `graph.compile(checkpointer=SqliteSaver(conn))`
- State is written to `chatbot.db` after every message
- Conversations are durable across restarts

**Endpoint:** `POST /v2/chat`

---

### Stage 4 — Conversation Management

With persistence in place, the next step was to expose conversations through the API so the frontend could list and reload them.

- `GET /chats` — lists all past conversations (reads from the checkpointer)
- `GET /chats/{thread_id}` — loads the full message history for a conversation
- A `chat_names` table was added to `chatbot.db` to store human-readable names alongside the raw `thread_id`

```sql
CREATE TABLE chat_names (
    thread_id TEXT PRIMARY KEY,
    name      TEXT
);
```

---

### Stage 5 — Automatic Conversation Naming

Rather than showing raw UUIDs in the sidebar, the app automatically generates a title for each conversation after the second human message.

The LLM is given the first few messages and asked to produce a one-line title. That title is stored in the `chat_names` table and shown in the Streamlit sidebar.

- Triggered automatically on every message via `auto_name(thread_id)`
- Only fires when `human_count == 2` to avoid re-naming on every turn
- Manual rename also available: `POST /chats/{thread_id}/name`

---

## Project Structure

```
.
├── main.py                  # FastAPI app — all routes
├── state.py                 # LangGraph state schema (shared by all versions)
├── llm.py                   # LLM initialisation (OpenAI)
├── utils.py                 # Streaming helper, title generation, auto-naming
├── api/
│   ├── v0_stateless.py      # Stage 1 — no checkpointer
│   ├── v1_memory.py         # Stage 2 — InMemorySaver
│   └── v2_sqlite.py         # Stage 3 — SqliteSaver
├── frontend/
│   └── app.py               # Streamlit UI
├── chatbot.db               # SQLite database (auto-created)
└── .env                     # API keys (not committed)
```

---

## API Reference

| Method | Endpoint                  | Description                              |
|--------|---------------------------|------------------------------------------|
| POST   | `/v0/chat`                | Stateless chat                           |
| POST   | `/v1/chat`                | Chat with in-memory persistence          |
| POST   | `/v2/chat`                | Chat with SQLite persistence             |
| GET    | `/chats`                  | List all conversations with names        |
| GET    | `/chats/{thread_id}`      | Load full message history                |
| POST   | `/chats/{thread_id}/name` | Manually set a conversation name         |

All chat endpoints accept:
```json
{ "message": "...", "thread_id": "..." }
```

And support a `?stream=true` query parameter for streaming responses.

---

## Running Locally

**1. Clone and install dependencies**
```bash
git clone <repo-url>
cd LG_portfolio_project
uv sync
```

**2. Set up environment variables**

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=your_base_url_here   # optional, omit if using OpenAI directly
```

**3. Start the FastAPI backend**
```bash
uv run uvicorn main:app --reload
```

**4. Start the Streamlit frontend** (new terminal)
```bash
uv run streamlit run frontend/app.py
```

- Backend: http://localhost:8000
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

---

## Key Concepts Demonstrated

**Checkpointers** — LangGraph's mechanism for persisting graph state between invocations. The graph logic stays identical across all three versions; only the storage backend changes.

**thread_id** — The key that identifies a conversation. LangGraph uses it to look up and restore the correct state before each invocation.

**Streaming** — LangGraph's `stream_mode='messages'` streams tokens as they arrive from the LLM. FastAPI returns a `StreamingResponse`; Streamlit consumes it with `st.write_stream`.

**State schema** — Defined once in `state.py` and shared by all versions. Uses LangGraph's `add_messages` reducer so new messages are appended rather than overwriting the list.

---

## What Would Change in Production

- **SQLite → PostgreSQL** — LangGraph ships a `PostgresSaver` that's a drop-in replacement for `SqliteSaver`, suitable for multi-process deployments
- **localhost URLs → environment variable** — The Streamlit app hardcodes `http://localhost:8000`; a production build would read this from config
- **Auto-naming timing** — Currently fires on every request and checks the count; a cleaner approach would be a background task or a webhook
