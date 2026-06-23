from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from utils import stream_response, summarise_title, auto_name
from pydantic import BaseModel
from api.v0_stateless import v0_chatbot
from api.v1_memory import v1_chatbot
from api.v2_sqlite import v2_chatbot
from langchain_core.messages import HumanMessage, SystemMessage
from api.v2_sqlite import conn

app = FastAPI() # fastapi app

@app.get("/health")
def health():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


#----------The non-streaming endpoint:

@app.post("/v0/chat")
def v0_chat(request: ChatRequest, stream: bool = False):
    if stream:
        return StreamingResponse(
            stream_response(v0_chatbot,request.message),
            media_type='text/plain'
        )
    else:
        response = v0_chatbot.invoke(
            {'messages': [HumanMessage(content=request.message)]}
        )
        return {"response": response['messages'][-1].content}

@app.post("/v1/chat")
def v1_chat(request: ChatRequest, stream: bool = False):
    if stream:
        return StreamingResponse(
            stream_response(v1_chatbot,request.message, request.thread_id),
            media_type='text/plain'
        )
    else:
        response = v1_chatbot.invoke(
            {'messages': [HumanMessage(content=request.message)]},
            config={'configurable': {'thread_id': request.thread_id}}
        )
        return {"response": response['messages'][-1].content}


@app.post("/v2/chat")
def v2_chat(request: ChatRequest, stream: bool = False):
    if stream:
        return StreamingResponse(
            stream_response(v2_chatbot,request.message, request.thread_id, on_complete=lambda:
  auto_name(request.thread_id)),
            media_type='text/plain'
        )
    else:
        response = v2_chatbot.invoke(
            {'messages': [HumanMessage(content=request.message)]},
            config={'configurable': {'thread_id': request.thread_id}}
        )
        auto_name(request.thread_id)
        return {"response": response['messages'][-1].content}
    
@app.get("/chats")
def get_chats():
    seen = set()
    threads = []
    for checkpoint in v2_chatbot.checkpointer.list(None):
        thread_id = checkpoint.config['configurable']['thread_id']
        if thread_id not in seen:
            seen.add(thread_id)
            name = conn.execute("SELECT name FROM chat_names WHERE thread_id=?", (thread_id,)).fetchone()
            threads.append({"thread_id": thread_id, "name": name[0] if name else thread_id})
    return {"threads": threads}

@app.get("/chats/{thread_id}")
def load_conversation(thread_id: str):
    messages = v2_chatbot.get_state(config = {'configurable': {'thread_id': thread_id}}).values['messages']
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        else:
            role = "assistant"
        result.append({"role": role, "content": msg.content})
    return {"messages": result}


@app.post('/chats/{thread_id}/name')
def generate_title(thread_id:str):
    title = summarise_title(thread_id)
    conn.execute("INSERT OR REPLACE INTO chat_names (thread_id, name) VALUES (?, ?)", (thread_id, title))
    conn.commit()
    return {"name": title}