import os
import streamlit as st
import requests
import time
import uuid
import logfire
from dotenv import load_dotenv

# Load environment variables explicitly from the root directory
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=env_path)

# Initialize Logfire
try:
    token = os.getenv("LOGFIRE_TOKEN")
    if not token:
        print("ERROR: LOGFIRE_TOKEN is empty or None!")
    logfire.configure(token=token)
    LOGFIRE_STATUS = "Connected & Tracing"
except Exception as e:
    print(f"Logfire Init Error in UI: {e}")
    LOGFIRE_STATUS = f"Standby (Error: {e})"
    
# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Enterprise Agentic RAG",
    page_icon="🤖",
    layout="wide",
)

# --- AVATARS ---
AI_AVATAR = "🤖"
USER_AVATAR = "👤"

# --- SESSION MANAGEMENT ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    logfire.info(f"✨ New User Session Created: {st.session_state.session_id}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 Agent OS")
    st.markdown("---")
    st.success(f"Logfire: {LOGFIRE_STATUS}")
    st.info(f"Memory ID: {st.session_state.session_id[:8]}")
    
    if st.button("🗑️ Clear History & Memory", width="stretch", type="primary"):
        logfire.warn(f"🗑️ Memory Wipe Triggered for session: {st.session_state.session_id}")
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# --- MAIN CHAT ---
st.title("🤖 Enterprise Agentic Assistant")

# Display history
for message in st.session_state.messages:
    avatar = AI_AVATAR if message["role"] == "assistant" else USER_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask about your documentation..."):
    # START TRACE: User Interaction
    with logfire.span("💬 User Chat Interaction", user_query=prompt, session_id=st.session_state.session_id):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        data = None

        # Assistant Response
        with st.chat_message("assistant", avatar=AI_AVATAR):
            with st.status("🔍 Agent is thinking...", expanded=True) as status:
                try:
                    # DISTRIBUTED TRACE: Calling Backend
                    with logfire.span("📡 Calling RAG Backend"):
                        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                        if not base_url:
                            base_url = "http://localhost:8000"
                        base_url = base_url.rstrip("/")
                        url = f"{base_url}/query"
                        
                        # ✅ FIX 1: Send exact Pydantic contract keys matching main.py 
                        # Passes down local session chat history logs to make the zero-token cache work!
                        payload = {
                            "session_id": str(st.session_state.session_id),
                            "user_query": str(prompt),
                            "messages": st.session_state.messages
                        }
                        
                        response = requests.post(url, json=payload, timeout=60)
                        response.raise_for_status()
                        data = response.json()
                    
                    # ✅ FIX 2: Map to the backend's "plan" key
                    steps = data.get("plan", [])
                    for step in steps:
                        st.write(f"⚙️ {step}")
                    
                    status.update(label=f"✅ {data.get('status', 'Answer Synthesized')}", state="complete", expanded=False)
                    
                    # ✅ FIX 3: Map to the backend's "documents" key
                    sources = data.get("documents", [])
                    if sources:
                        with st.expander("📄 View Retrieved Context (Sources)"):
                            for i, source in enumerate(sources):
                                preview = source[:100].replace("\n", " ") + "..."
                                with st.expander(f"Chunk {i+1}: {preview}"):
                                    st.info(source)
                                    
                except Exception as e:
                    logfire.error(f"❌ UI-Backend Connection Failed: {e}")
                    status.update(label="❌ Connection Failed", state="error")
                    st.error(f"The RAG backend returned an error or is offline: {e}")
                    data = None

            # --- SAFE FINAL RESPONSE RENDERING ---
            if data is not None:
                answer_placeholder = st.empty()
                # ✅ FIX 4: Map to the backend's "final_answer" key
                full_answer = data.get("final_answer", "No response payload received.")
                
                curr_text = ""
                for char in full_answer:
                    curr_text += char
                    answer_placeholder.markdown(curr_text + "▌")
                    time.sleep(0.002)
                
                answer_placeholder.markdown(full_answer)
                st.session_state.messages.append({"role": "assistant", "content": full_answer})
                logfire.info("✅ Chat cycle completed successfully.")
            else:
                st.warning("Skipped text synthesis because the backend did not respond successfully.")