from langgraph.graph import add_messages
from typing import TypedDict, Annotated

#defining state class.
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]