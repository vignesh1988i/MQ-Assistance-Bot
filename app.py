"""Streamlit UI for IBM MQ Assistant Bot - CPU Optimized"""

import streamlit as st
import uuid
from datetime import datetime, timedelta
from agent import session_manager
import config

# ============= PAGE CONFIG =============
st.set_page_config(
    page_title="IBM MQ Assistant Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= CUSTOM CSS =============
st.markdown("""
<style>
    .stChatMessage {padding: 1rem; border-radius: 0.5rem;}
    .main-header {font-size: 2. 5rem; font-weight: bold; color: #0f62fe;}
    .sub-header {font-size: 1rem; color: #6f6f6f;}
</style>
""", unsafe_allow_html=True)

# ============= SESSION INITIALIZATION =============
if "session_id" not in st. session_state:
    st. session_state.session_id = str(uuid.uuid4())

if "user_id" not in st.session_state:
    # Get user from URL params or generate
    st.session_state.user_id = st.query_params.get("user", f"user_{uuid.uuid4().hex[:8]}")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.now()

# ============= HELPER FUNCTIONS =============
def new_conversation():
    """Start a new conversation"""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.start_time = datetime.now()

def add_example(question:  str):
    """Add example question to chat"""
    st.session_state.messages.append({"role":  "user", "content": question})

# ============= HEADER =============
col1, col2 = st. columns([4, 1])

with col1:
    st.markdown('<p class="main-header">🤖 IBM MQ Assistant Bot</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Powered by MCP Architecture | Ask me anything about your IBM MQ environment</p>', unsafe_allow_html=True)

with col2:
    st.metric("⏱️ Active Since", st.session_state.start_time.strftime("%H:%M:%S"))

# ============= SIDEBAR =============
with st.sidebar:
    st. header("⚙️ Controls")
    
    if st.button("🔄 New Conversation", use_container_width=True, type="primary"):
        new_conversation()
        st.rerun()
    
    st.divider()
    
    # Session Info
    st.subheader("📊 Session Info")
    st.text(f"Session:  {st.session_state.session_id[:8]}...")
    st.text(f"User: {st.session_state.user_id}")
    st.text(f"Messages: {len(st.session_state.messages)}")
    
    # Get stats
    stats = session_manager. get_stats()
    st.text(f"Active Sessions: {stats['active_sessions']}")
    st.text(f"Total Sessions: {stats['total_sessions']}")
    
    st.divider()
    
    # Example Questions
    st.subheader("💡 Example Questions")
    
    examples = [
        ("🔍 Status", "Is SRVIG running?"),
        ("📊 Queue Count", "How many queues in SRVIG?"),
        ("🔎 Search Queues", "Show me SYSTEM queues in SRVIG"),
        ("📋 Queue Details", "Tell me about DEV. QUEUE. 1 in SRVIG"),
        ("🌐 Channels", "How many channels does SRVIG have?"),
        ("📚 List QMgrs", "List all queue managers"),
    ]
    
    for emoji_label, question in examples:
        if st.button(emoji_label, key=question, use_container_width=True):
            add_example(question)
            st.rerun()
    
    st.divider()
    
    # Configuration
    with st.expander("⚙️ Configuration"):
        st.code(f"""Bridge:  {config.MCP_BRIDGE_URL}
Model: {config.LLM_MODEL}
Max History: {config.MAX_CONVERSATION_HISTORY}
Session Timeout: {config.SESSION_TIMEOUT_MINUTES} min""", language="yaml")
    
    # Help
    with st.expander("❓ Help & Tips"):
        st.markdown("""
**How to use:**
1. Type your question in the chat box
2. Be specific with queue manager names
3. The bot remembers context within a session

**Tips:**
- ✅ "Is SRVIG running?"
- ✅ "How many queues in SRVIG?"
- ✅ "Show me queues in SRVIG"
- ❌ "What's the status?" (too vague)

**Features:**
- 🔒 Isolated user sessions
- 🧠 Context-aware conversations
- 🔄 Automatic queue manager tracking
- 👥 Multi-user support
        """)

# ============= CHAT INTERFACE =============

# Display chat history
for message in st.session_state. messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your IBM MQ environment... "):
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get agent for this session
    agent = session_manager.get_agent(
        st.session_state.session_id,
        st.session_state.user_id
    )
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking...  (This may take 1-3 minutes for complex queries)"):
            try:
                response = agent.chat(prompt)
                st.markdown(response)
            except Exception as e:
                error_msg = f"❌ **Error:** {str(e)}\n\nPlease check if MCP bridge is running at `{config.MCP_BRIDGE_URL}`"
                st.error(error_msg)
                response = error_msg
    
    # Add response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# ============= FOOTER =============
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.caption(f"🔗 Bridge: `{config.MCP_BRIDGE_URL}`")

with col2:
    st. caption(f"🤖 Model: `{config.LLM_MODEL}`")

with col3:
    st.caption(f"💾 History: `{config.MAX_CONVERSATION_HISTORY} exchanges`")

with col4:
    st.caption(f"⏱️ Timeout: `{config.SESSION_TIMEOUT_MINUTES}min`")

# ============= BACKGROUND CLEANUP =============
# Cleanup expired sessions every 5 minutes
if "last_cleanup" not in st.session_state:
    st.session_state.last_cleanup = datetime.now()

if datetime.now() - st.session_state.last_cleanup > timedelta(minutes=5):
    session_manager.cleanup_expired()
    st.session_state.last_cleanup = datetime.now()