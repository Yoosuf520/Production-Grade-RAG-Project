
import os
import logfire
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

# Force NeMo Guardrails to inherit LangChain configurations seamlessly
os.environ["NEMOGUARDRAILS_LLM_FRAMEWORK"] = "langchain"

from app.agents.graph import rag_agent
from app.guardrails.rails import initialize_rails, guard

# 1. Initialize Logfire Telemetry Tracking Suite
logfire.configure()

# 2. Build FastAPI Framework Instance
app = FastAPI(
    title="Enterprise IT RAG Engine Backend",
    description="Production pipeline utilizing Portkey, Groq, Qdrant, and LangGraph",
    version="1.0.0"
)

# 3. Configure Network Boundaries (CORS Sharing Rules)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Define API Request Schema Contract (Accepts full history context list)
class QueryRequest(BaseModel):
    session_id: str = Field(..., description="Unique thread target bucket identifier")
    user_query: str = Field(..., description="Raw text data entered by end-user")
    # ✅ FIX 1: Explicitly accept the history array payload stream from Streamlit UI
    messages: List[Dict[str, str]] = Field(default=[], description="Full conversation logs collection")

# 5. Application Lifecycle Hook Manager
@app.on_event("startup")
def startup_event():
    try:
        initialize_rails()
    except Exception as e:
        logfire.error(f"Failed to bootstrap NeMo Guardrail wrappers: {e}")
        raise e

# 6. Core RAG Execution Agent Endpoint Routing Node
@app.post("/query")
async def process_user_query(request: QueryRequest):
    clean_query = request.user_query.strip()
    session_key = request.session_id.strip()

    if not clean_query:
        raise HTTPException(status_code=400, detail="Query string payload cannot be empty.")

    # PHASE 1: Execute Structural Input NeMo Guardrails Check
    rails_fired, guardrail_response = await guard(clean_query) 
    
    if rails_fired:
        logfire.info(f"Guardrails blocked query step early: {clean_query[:40]}")
        return {
            "final_answer": guardrail_response,
            "status": "Blocked by system guardrails policy configuration.",
            "plan": ["Guardrails: Violations Fired", "Graph Engine: Bypassed"],
            "documents": []
        }

    # PHASE 2: Graph Context Orchestration & Checkpointer Invocation
    try:
        config = {
            "configurable": {
                "thread_id": session_key
            }
        }

        # ✅ FIX 2: Reconstruct complete history array cleanly if history array exists.
        # This makes the local Python memory loops inside planner.py bulletproof!
        if request.messages:
            formatted_messages = []
            for msg in request.messages:
                # Standardize format naming structures for state machine alignment
                role = "user" if msg.get("role") in ["user", "User"] else "assistant"
                formatted_messages.append({"role": role, "content": msg.get("content", "")})
            
            # Append the fresh incoming query at the tail of history array stream
            if not formatted_messages or formatted_messages[-1]["content"] != clean_query:
                formatted_messages.append({"role": "user", "content": clean_query})
                
            initial_state = {"messages": formatted_messages}
        else:
            # Fallback configuration if frontend passes only query data
            initial_state = {
                "messages": [{"role": "user", "content": clean_query}]
            }

        with logfire.span("Calling RAG Backend Agent Topology"):
            result = rag_agent.invoke(initial_state, config=config)

        return {
            "final_answer": result.get("final_answer", "No answer could be generated."),
            "status": result.get("status", "Completed successfully."),
            "plan": result.get("plan", []),
            "documents": result.get("documents", [])
        }

    except Exception as e:
        logfire.error(f"Graph orchestrator execution error caught: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred during pipeline execution steps: {str(e)}"
        )