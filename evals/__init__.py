import sys
import types

# Stub missing ChatVertexAI import for ragas compatibility
if "langchain_community.chat_models.vertexai" not in sys.modules:
    dummy_chat = types.ModuleType("langchain_community.chat_models.vertexai")
    dummy_chat.ChatVertexAI = type("ChatVertexAI", (object,), {})
    sys.modules["langchain_community.chat_models.vertexai"] = dummy_chat


from evals.pipeline import run_pipeline, load_golden_dataset
from evals.guardrails_eval import run_guardrails_eval, compute_guardrails_metrics
from evals.metrics import run_all_metrics