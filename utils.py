
from langchain_core.messages import HumanMessage, SystemMessage
from llm import model
from api.v2_sqlite import v2_chatbot, conn


def stream_response(chatbot, message, thread_id = None, on_complete=None):
    config = {'configurable': {'thread_id': thread_id}} if thread_id else {}
    for chunk, metadata in chatbot.stream(
        {'messages': [HumanMessage(content=message)]},
          config=config,
          stream_mode='messages'):
        yield chunk.content
        if on_complete:
          on_complete()

def summarise_title(thread_id):                                                                              
    conversation = v2_chatbot.get_state(config={'configurable':{'thread_id':thread_id}})                         
    part = conversation.values['messages']                                                                         
    human_convo = [msg.content for msg in part if isinstance(msg, HumanMessage)]                                   
    text_needed = human_convo[:3] 
    title = model.invoke([
        SystemMessage(content="Generate a one-line title for this conversation. Reply with only the title."),
        HumanMessage(content=f"Messages: {text_needed}")]
    )
    return title.content


def auto_name(thread_id):
    state = v2_chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    human_count = sum(1 for msg in state.values['messages'] if isinstance(msg, HumanMessage))
    if human_count == 2:
        title = summarise_title(thread_id)
        conn.execute("INSERT OR REPLACE INTO chat_names (thread_id, name) VALUES (?, ?)", (thread_id, title))
        conn.commit()