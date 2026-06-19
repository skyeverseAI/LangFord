from state import ChatState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from llm import model

#--------defining node function-----------
# chatnode function

checkpointer = InMemorySaver()

def chat_node(state: ChatState) -> ChatState:

    #take user query from state
    messages = state['messages']

    #send to llm
    response = model.invoke(messages)

    #update state with response
    return {'messages': [response]}


#----------building the graph--------------

v1_graph = StateGraph(ChatState)

v1_graph.add_node('chat_node', chat_node)

v1_graph.add_edge(START, 'chat_node')
v1_graph.add_edge('chat_node', END)

# compiling the graph
v1_chatbot = v1_graph.compile(checkpointer=checkpointer)


