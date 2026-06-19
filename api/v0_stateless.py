from state import ChatState
from llm import model
from langgraph.graph import StateGraph, START, END


#--------defining node function-----------
# chatnode function
def chat_node(state: ChatState) -> ChatState:

    #take user query from state
    messages = state['messages']

    #send to llm
    response = model.invoke(messages)

    #update state with response
    return {'messages': [response]}


#----------building the graph--------------

v0_graph = StateGraph(ChatState)

v0_graph.add_node('chat_node', chat_node)

v0_graph.add_edge(START, 'chat_node')
v0_graph.add_edge('chat_node', END)

# compiling the graph
v0_chatbot = v0_graph.compile()


