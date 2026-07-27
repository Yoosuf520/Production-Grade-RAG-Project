🚀 Enterprise Agentic RAG Engine (Kubernetes Assistant)An enterprise-ready, multi-agent Retrieval-Augmented Generation (RAG) platform specializing in Kubernetes, Intel Hardware, and Enterprise Networking.This system features a LangGraph orchestrator, NeMo Guardrails for security, Portkey Gateway for resilient LLM routing, Qdrant Cloud for vector retrieval, and Pydantic Logfire for end-to-end distributed tracing.🏛 System Architecture                                 ┌─────────────────────────────────────────────────────────┐
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
Key FeaturesMulti-Agent Orchestration: Powered by LangGraph with dynamic node routing (Planner $\rightarrow$ Retriever $\rightarrow$ Responder).Zero-Token Memory Lookup: Built-in exact-match state history lookup in planner_node that bypasses LLM calls and retrieval loops on repeated queries.Input Safety & Guardrails: Integrated NVIDIA NeMo Guardrails (colang + yaml) blocking prompt injections, jailbreaks, and out-of-scope queries prior to agent invocation.Gateway Fallback & Resilience: Unified LLM proxy execution via Portkey Gateway, seamlessly managing failover between primary (Llama-3.3-70b-versatile) and fallback (Llama-3.1-8b-instant) models on Groq.Production Observability: Instrumented end-to-end with Pydantic Logfire, delivering distributed trace spans from UI interactions down to vector embeddings and LLM calls.Automated Evaluation Suite: Streamlit-powered evaluation app executing RAGAS metrics (Faithfulness, Answer Relevancy, Context Precision, Context Recall, Answer Correctness, Tool Correctness) against a golden dataset.Repository Structure.
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
🛠 Local Setup & Development1. PrerequisitesPython 3.11+uv package manager (or standard pip)Docker Desktop2. Environment VariablesCreate a .env file in the root directory:Ini, TOML# Core LLM & Gateway Keys
GROQ_API_KEY=your_groq_api_key
GROQ_FALLBACK_API_KEY=your_groq_fallback_key
PORTKEY_API_KEY=your_portkey_api_key
PORTKEY_GATEWAY_URL=https://api.portkey.ai/v1

# Vector Database (Qdrant)
QDRANT_CLUSTER_ENDPOINT=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key

# Embeddings & Judge
GEMINI_API_KEY=your_gemini_api_key
JUDGE_GROQ=your_judge_groq_api_key

# Observability
LOGFIRE_TOKEN=your_logfire_token

# Network Connections
BACKEND_URL=http://localhost:8080
3. Local ExecutionOption A: Running via Python (uv)Bash# Install dependencies
uv pip install -r pyproject.toml

# Start Backend API
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Start Chat UI (in separate terminal)
streamlit run ui/app.py --server.port 8501

# Start Evaluation Dashboard (in separate terminal)
streamlit run evals/app.py --server.port 8502
Option B: Running via DockerBash# Build unified image
docker build -t k8s-rag-app:latest .

# Run container with environment variables
docker run -d \
  --name k8s-rag-container \
  --env-file .env \
  -p 8080:8080 \
  -p 8501:8501 \
  -p 8502:8502 \
  k8s-rag-app:latest
AWS Deployment ArchitectureThis application deploys to an AWS EC2 instance backed by Amazon ECR using a containerized architecture managed by supervisord.                  ┌─────────────────────────────────────────┐
                  │          GITHUB REPOSITORY              │
                  └────────────────────┬────────────────────┘
                                       │
                               git push main
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │         GITHUB ACTIONS CI/CD            │
                  │  1. Build Docker image using `uv`      │
                  │  2. Push image to Amazon ECR            │
                  │  3. SSH into AWS EC2 Instance           │
                  │  4. Restart container with secrets     │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │           AWS EC2 INSTANCE              │
                  │  ┌───────────────────────────────────┐  │
                  │  │       SUPERVISORD CONTAINER       │  │
                  │  │  [8080] FastAPI Backend           │  │
                  │  │  [8501] Streamlit Chat UI         │  │
                  │  │  [8502] Streamlit Eval Suite      │  │
                  │  └───────────────────────────────────┘  │
                  └─────────────────────────────────────────┘
Security Group Inbound Port MappingPortServiceAccess StrategyDescription22SSHMy IPAdministrative server maintenance8501Streamlit Chat UI0.0.0.0/0 (Public)Public user chat interface8502Streamlit Eval SuiteMy IP (Creator Only)Restricted evaluation metric execution8080FastAPI BackendInternal / PrivateInternal container communication🧪 Evaluation & Quality AssuranceThe system includes a 3-step evaluation suite running in evals/app.py:Ground Truth Validation: Inspects golden Q&A pairs extracted from official Kubernetes documentation.Live Pipeline Execution: Runs tests against /query to capture responses, context sources, and node execution paths.RAGAS Scoring: Executes 6 metrics with custom rate-limiting to prevent Groq TPM exhaustion:FaithfulnessAnswer RelevancyContext PrecisionContext RecallAnswer CorrectnessTool Correctness📊 Distributed ObservabilityAll traces are automatically emitted to Pydantic Logfire:Input Analysis: Visualizes NeMo Guardrail policy decisions.Agent Flow: Traces time elapsed per node (planner, retriever, responder).Retrieval Diagnostics: Logs Qdrant search vector timing and payload metadata.Gateway Performance: Monitors LLM token generation throughput and Portkey cache hits.LicenseThis project is licensed under the MIT License - see the LICENSE file for details.