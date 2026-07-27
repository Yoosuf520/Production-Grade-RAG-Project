import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI

from app.config import settings


# Production gateway config:
#   - Fallback: primary @rag/llama-3.3-70b-versatile → @brag/llama-3.1-8b-instant on failure
#   - Cache: semantic mode (requires Portkey Enterprise — silently falls back to simple on free/starter)
#   - Retry: 2 attempts on rate limit / server error before triggering the fallback target
DYNAMIC_GATEWAY_CONFIG = {
    "strategy": {"mode": "fallback"},
    "cache": {"mode": "simple"},
    "retry": {
        "attempts": 2,
        "on_status_codes": [429, 503]  # Triggers fallback on rate limits or server errors
    },
    "targets": [
        {
            "virtual_key": settings.GROQ_SLUG,      # Primary: Pulls "rag1" slug string safely
            "override_params": {"model": "llama-3.3-70b-versatile"} # Clean model name
        },
        {
            "virtual_key": settings.GROQ_SLUG_2,    # Fallback: Pulls "rag3" slug string safely
            "override_params": {"model": "llama-3.1-8b-instant"}    # Clean fallback model[cite: 2]
        }
    ]
}

# Initialize the native client with the corrected robust configuration dictionary
portkey_client = Portkey(
    api_key=settings.PORTKEY_API_KEY,
    config=settings.DYNAMIC_GATEWAY_CONFIG
)


def get_langchain_llm(feature: str = "rag1") -> ChatOpenAI:
    """
    Returns a Portkey-backed ChatOpenAI — a drop-in for ChatGroq in LangChain nodes.

    Why ChatOpenAI and not ChatGroq:
      Portkey is a proxy. It exposes an OpenAI-compatible endpoint at PORTKEY_GATEWAY_URL.
      ChatGroq is hardwired to Groq's API and does not support routing through a proxy.
      ChatOpenAI supports base_url (points at Portkey) and default_headers (passes Portkey
      auth + config). The @rag/model-name format is Portkey-specific — Groq's own client
      does not understand it. You are still using Groq models; Portkey is just in the middle.
    """
    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model="llama-3.3-70b-versatile",  # Set the primary model entry name cleanly[cite: 2]
        temperature=0,
        default_headers=createHeaders(
            api_key=settings.PORTKEY_API_KEY,
            config=settings.DYNAMIC_GATEWAY_CONFIG, # Passes the functional multi-target routing map[cite: 2]
            metadata={
                "feature": feature,
                "_user": "rag-system",
                "environment": "production"
            }
        )
    )

def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey native client response headers.
    Tries multiple attribute paths defensively — returns 'MISS' if not found.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"