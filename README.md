# 🚀 Enterprise Agentic RAG Engine (Kubernetes Assistant)

An enterprise-ready, multi-agent Retrieval-Augmented Generation (RAG) platform specializing in **Kubernetes, Intel Hardware, and Enterprise Networking**.

This system features a **LangGraph** orchestrator, **NeMo Guardrails** for security, **Portkey Gateway** for resilient LLM routing, **Qdrant Cloud** for vector retrieval, and **Pydantic Logfire** for end-to-end distributed tracing.

---

## 🏛 System Architecture

<pre>
                                 ┌─────────────────────────────────────────────────────────┐
                                 │                   STREAMLIT FRONTEND                    │
                                 │  [Port 8501: Chat UI]     [Port 8502: Eval Suite]      │
                                 └────────────────────────────┬────────────────────────────┘
                                                              │ REST API (/query)
                                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                 FASTAPI BACKEND ENGINE                                                 │
│                                                                                                                        │
│   ┌────────────────────────┐         ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │    NEMO GUARDRAILS     │ ──Pass─>│                             LANGGRAPH AGENT                                 │   │
│   │ (Off-topic/Jailbreak)  │         │                                                                             │   │
│   └───────────┬────────────┘         │  ┌─────────────────┐       ┌─────────────────┐       ┌───────────────────┐  │   │
│               │ Block                │  │  PLANNER NODE   │ ────> │ RETRIEVER NODE  │ ────> │  RESPONDER NODE   │  │   │
│               ▼                      │  │ (Intent & Cache)│       │ (Qdrant Search) │       │ (Synthesis/Portkey│  │   │
│      [Enforced Refusal]              │  └─────────────────┘       └─────────────────┘       └───────────────────┘  │   │
│                                      └─────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                            ▼                                   ▼
                                ┌──────────────────────┐            ┌──────────────────────┐
                                │    QDRANT VECTOR     │            │   PORTKEY GATEWAY    │
                                │   (Enterprise DB)    │            │    (Groq/LLMs)       │
                                └──────────────────────┘            └──────────────────────┘
</pre>

---

## ✨ Key Features

* **Multi-Agent Orchestration:** Powered by **LangGraph** with dynamic node routing (`Planner` ➔ `Retriever` ➔ `Responder`).
* **Zero-Token Memory Lookup:** Built-in exact-match state history lookup in `planner_node` that bypasses LLM calls and retrieval loops on repeated queries.
* **Input Safety & Guardrails:** Integrated NVIDIA **NeMo Guardrails** (`colang` + `yaml`) blocking prompt injections, jailbreaks, and out-of-scope queries prior to agent invocation.
* **Gateway Fallback & Resilience:** Unified LLM proxy execution via **Portkey Gateway**, seamlessly managing failover between primary (`Llama-3.3-70b-versatile`) and fallback (`Llama-3.1-8b-instant`) models on Groq.
* **Production Observability:** Instrumented end-to-end with **Pydantic Logfire**, delivering distributed trace spans from UI interactions down to vector embeddings and LLM calls.
* **Automated Evaluation Suite:** Streamlit-powered evaluation app executing RAGAS metrics (**Faithfulness, Answer Relevancy, Context Precision, Context Recall, Answer Correctness, Tool Correctness**) against a golden dataset.

---

## 📁 Repository Structure

```text
.
├── app/
│   ├── agents/            # LangGraph state machine, nodes, and graph topology
│   │   ├── nodes/         # Planner, Retriever, and Responder execution nodes
│   │   ├── graph.py       # Compiled state graph with checkpointer memory
│   │   └── state.py       # Agent state schemas
│   ├── gateway/           # Portkey gateway client & fallback strategy mapping
│   ├── guardrails/        # NeMo Guardrails configuration & intent definitions
│   ├── ingestion/         # Document parsing (PDF, DOCX, PPTX, HTML) & chunking
│   ├── services/          # Qdrant client & FlashRank local reranker
│   ├── config.py          # Environment settings loader
│   └── main.py            # FastAPI REST backend entry point
├── ui/
│   └── app.py             # Streamlit primary chat user interface
├── evals/
│   ├── app.py             # Streamlit automated evaluation dashboard
│   ├── metrics.py         # RAGAS metric runner with Groq TPM rate-limit protection
│   └── golden_dataset.json# Golden Q&A ground truth dataset
├── .github/
│   └── workflows/
│       └── deploy.yml     # GitHub Actions CI/CD deployment pipeline to AWS
├── Dockerfile             # Unified multi-stage container build via `uv`
├── supervisord.conf       # Process control configuration (Backend + UI + Evals)
├── pyproject.toml         # Dependency declarations
└── README.md