from state import ChatState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from llm import model


#establishing db connection
conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS chat_names (thread_id TEXT PRIMARY KEY, name TEXT)")
conn.commit()


#--------defining node function-----------
# chatnode function

checkpointer = SqliteSaver(conn = conn)



def chat_node(state: ChatState) -> ChatState:

    #take user query from state
    messages = state['messages']

    #send to llm
    response = model.invoke(messages)

    #update state with response
    return {'messages': [response]}


#----------building the graph--------------

v2_graph = StateGraph(ChatState)

v2_graph.add_node('chat_node', chat_node)

v2_graph.add_edge(START, 'chat_node')
v2_graph.add_edge('chat_node', END)

# compiling the graph
v2_chatbot = v2_graph.compile(checkpointer=checkpointer)


