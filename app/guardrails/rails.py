import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS


_rails = None


def initialize_rails() -> None:
    """
    Build the NeMo LLMRails singleton at app startup.
    Uses llama-3.1-8b-instant for fast intent classification at the gate —
    the heavier llama-3.3-70b-versatile is reserved for the RAG pipeline.
    """
    global _rails

    # 1. Create the LangChain LLM instance
    guard_llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT
    )

    # The constructor accepts the LangChain object framework cleanly
    _rails = LLMRails(config, llm=ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0
    ))
    logfire.info("🛡️ NeMo Guardrails initialised (llama-3.1-8b-instant).")
    
    


# Async coroutine handles non-blocking requests inside FastAPI loops
async def guard(message: str) -> tuple[bool, str | None]:
    if _rails is None:
        return False, None
        
    with logfire.span("Guardrails Check"):
        # Executes non-blocking async generation
        result = await _rails.generate_async(messages=[{"role": "user", "content": message}])
        
        content = result.get("content", "") if isinstance(result, dict) else str(result)
        
        fired = any(indicator.lower() in content.lower() for indicator in RAIL_INDICATORS)
        if fired or "i can't help with that" in content.lower() or "i maintain consistent guidelines" in content.lower():
            logfire.info(f"Guardrails strictly blocked: {message[:50]}")
            return True, content
            
        return False, None