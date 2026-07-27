from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # ✅ NEW IMPORT
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retriever import retrieve_node
from app.agents.nodes.responder import generate_node

# 1. Initialize the State Graph
workflow = StateGraph(AgentState)

# 2. Define the Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retrieve_node)
workflow.add_node("responder", generate_node)

# 3. Define the Edges & Routing Logic
def route_planner(state: AgentState):
    query = state["current_query"]
    
    if query == "OFF_TOPIC":
        return "responder"
        
    if query == "CONVERSATIONAL":
        return "responder"
        
    return "retriever"

workflow.set_entry_point("planner")

workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "retriever": "retriever",
        "responder": "responder"
    }
)

workflow.add_edge("retriever", "responder")
workflow.add_edge("responder", END)

# ✅ FIX: Initialize Memory Saver checkpointer
memory = MemorySaver()

# 4. Compile the Graph with Checkpointer Memory
# This preserves state history internally so the Python loops can catch duplicate queries!
rag_agent = workflow.compile(checkpointer=memory)