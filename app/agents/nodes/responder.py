import logfire
from app.agents.state import AgentState
from app.gateway.client import portkey_client, extract_cache_status

def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.
    Uses the native Portkey client so we can read the x-portkey-cache-status 
    response header and surface execution states back to the application pipeline.
    """

    # 1. ✅ FAST-FAIL: Handle Off-Topic Intent Immediately
    if state.get("current_query") == "OFF_TOPIC":
        refusal_msg = "I can't help with that topic. Please ask a question related to Kubernetes, Intel hardware, or networking."
        return {
            "final_answer": refusal_msg,
            "status": "Execution halted: Off-topic request.",
            "plan": state["plan"] + ["Action: Enforced Refusal"],
            "messages": [{"role": "assistant", "content": refusal_msg}]
        }

    user_msg = state["messages"][-1]["content"].strip() if state["messages"] else ""

    # 2. ✅ ZERO-TOKEN CACHE HIT: Serve identical responses directly from state history
    if state.get("status") == "CACHED_MEMORY_HIT":
        past_messages = state["messages"][:-1]
        for i, msg in enumerate(past_messages):
            # Locate the historical question that matches the exact text string
            if msg["role"] == "user" and msg["content"].strip().lower() == user_msg.lower():
                # Ensure the assistant successfully generated a matching answer right next to it
                if i + 1 < len(past_messages) and past_messages[i + 1]["role"] == "assistant":
                    cached_answer = past_messages[i + 1]["content"]
                    logfire.info("⚡ Token Saver Hit: Serving identical response from state history.")
                    
                    return {
                        "final_answer": cached_answer,
                        "status": "Served from memory cache (0 tokens used).",
                        "plan": state["plan"] + ["Cache: Local History Hit ⚡"],
                        "messages": [{"role": "assistant", "content": cached_answer}]
                    }

    # 3. Regular Flow Pipeline Execution (When the user query is new/unique)
    query = state["current_query"]
    
    # Reconstruct the text history block for conversational prompt awareness
    history_str = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    # Route prompt construction depending on the classification intent
    if query == "CONVERSATIONAL":
        logfire.info("Generating a professional conversational or gratitude response.")
        prompt = f"""
        You are a highly professional, direct, and formal Enterprise IT AI Assistant specializing strictly in Kubernetes, Intel hardware, and enterprise networking.
        
        CRITICAL RULES:
        1. Never use casual human filler phrases like "I'm doing great" or "Thanks for asking".
        
        2. IF THE USER SAYS A GREETING (e.g., "hi", "hello"):
           - Reply with a formal greeting and state your role.
           - Example: "Hello. I am an Enterprise IT Assistant specializing in Kubernetes, Intel hardware, and enterprise networking. How can I assist you with these technologies today?"
        
        3. IF THE USER SAYS THANK YOU OR CLOSES THE CHAT (e.g., "thank you", "thanks", "useful"):
           - Acknowledge their gratitude formally and warmly reinforce your value to invite them back.
           - Example: "You are very welcome. It is my pleasure to assist you with your infrastructure needs. Please let me know whenever you need further help with Kubernetes, Intel hardware, or networking."
           
        4. IF THE USER SAYS THEY UNDERSTOOD (e.g., "good, I got it", "clear", "perfect"):
           - Reply with a formal acknowledgment of success.
           - Example: "Excellent. It is my pleasure to help you resolve your technical queries. Please feel free to reach out anytime you have further questions regarding your environment."
        
        5. Keep the entire output to ONE or TWO sentences maximum. Never write long paragraphs.
        
        CONVERSATION HISTORY:
        {history_str}
        
        LATEST MESSAGE:
        "{user_msg}"
        """
    else:
        logfire.info("Generating technical RAG response.")
        max_context_chars = 18000
        full_context = ""

        # Safely parse down target token counts within limits
        for doc in state.get("documents", []):
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break

        prompt = f"""
        You are a Senior Technical Architect specializing strictly in Kubernetes, Intel, and Networking.
        
        CRITICAL RULES:
        1. Answer the question using ONLY the provided TECHNICAL CONTEXT.
        2. If the user question is unrelated to the technical context, or asks for code/tasks outside of enterprise infrastructure (e.g., writing simple math formulas, random scripting, email generation), you MUST completely refuse to answer. Do not provide a courtesy answer. 
        3. Respond strictly with: "I can't help with that topic. Please ask a question related to Kubernetes, Intel hardware, or networking."
        
        TECHNICAL CONTEXT:
        {full_context}
        
        CONVERSATION HISTORY:
        {history_str}
        
        USER QUESTION:
        "{user_msg}"
        """

    # 4. Invoke LLM payload through the secure cloud gateway client
    with logfire.span("✍️ LLM Synthesis"):
        try:
            response = portkey_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content
            cache_status = extract_cache_status(response)
            is_cache_hit = cache_status == "HIT"

            if is_cache_hit:
                logfire.info("⚡ Gateway Cache Hit — response served from Portkey cache.")
                plan_update = state["plan"] + ["Cache: Hit ⚡"]
                status = "Cache hit — instant response."
            else:
                logfire.info("✅ Response synthesised via LLM.")
                plan_update = state["plan"]
                status = "Response generated."

            return {
                "final_answer": content,
                "status": status,
                "plan": plan_update,
                "messages": [{"role": "assistant", "content": content}]
            }

        except Exception as e:
            logfire.error(f"LLM Generation failed: {e}")
            raise e