import streamlit as st
import requests
import uuid

with st.spinner("Connecting to server, please wait..."):
    try:
        requests.get(f"{st.secrets['API_BASE_URL']}/health", timeout=90)
        st.success("Server is ready!")
    except Exception:
        st.error("Could not connect to server. Please refresh and try again.")


# ---- side bar ---

st.sidebar.title('LangFord')
version = st.sidebar.selectbox("Select version", ["v0", "v1", "v2"])

# adding stream output
is_streaming = st.sidebar.toggle("Streaming", value=False)

if st.sidebar.button('Start New Chat'):
    st.session_state['message_history'] = []
    st.session_state['thread_id']=str(uuid.uuid4())

if version =='v2':
    st.sidebar.header('Past Conversations')
    chats = requests.get(f"{st.secrets['API_BASE_URL']}/chats").json()
    for chat in chats["threads"]:
        if st.sidebar.button(chat['name'], key=chat["thread_id"]):
            st.session_state['thread_id']=chat['thread_id']
            st.session_state['message_history']=requests.get(f"{st.secrets['API_BASE_URL']}/chats/{chat['thread_id']}").json()['messages']

#------initialising the messages-history in session-state (so that they don't disappear)
if "message_history" not in st.session_state:
    st.session_state['message_history'] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

if "current_version" not in st.session_state:
      st.session_state["current_version"] = version
  
if st.session_state["current_version"] != version:
    st.session_state["message_history"] = []
    st.session_state["thread_id"] = str(uuid.uuid4())
    st.session_state["current_version"] = version

# ---- input and more----

user_input = st.chat_input("What do you want to talk about?..")

for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.text(message["content"])

if user_input:
    st.session_state['message_history'].append({"role": "user", "content": user_input}) # appending the messages to the session.state
    st.chat_message("user").write(user_input)

    payload = {
      "message": user_input,
      "thread_id": st.session_state["thread_id"]
    }

    response = requests.post(
          f"{st.secrets['API_BASE_URL']}/{version}/chat?stream={str(is_streaming).lower()}",
          json=payload,
          stream = is_streaming

      )
    
    if is_streaming:
      with st.chat_message("assistant"):
          ai_response = st.write_stream(
              response.iter_content(chunk_size=None, decode_unicode=True)
          )
    else:   
        ai_response = response.json()["response"]
        st.chat_message("assistant").write(ai_response)
        
    st.session_state['message_history'].append({"role": "assistant", "content": ai_response})
    st.rerun()  