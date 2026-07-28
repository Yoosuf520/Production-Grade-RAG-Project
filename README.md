# 🚀 Enterprise Agentic RAG Engine

A production-grade, distributed **Agentic Retrieval-Augmented Generation (RAG)** system built with **FastAPI**, **LangGraph**, **NeMo Guardrails**, **Portkey LLM Gateway**, **Qdrant Vector Database**, and **Streamlit**. 

The system leverages state-machine orchestration, zero-token local session caching, multi-model fallback gateways, semantic reranking, and full-suite RAGAS telemetry.

---

## 🌐 Live Cloud Endpoints

The application is deployed live on AWS EC2 (`ap-south-1`):

* 💬 **Live Chat Application (Streamlit UI):** [http://3.109.208.157:8501](http://3.109.208.157:8501)

---

## ✨ Key System Features

* 🛡️ **Dual-Stage NeMo Guardrails:** Input intent evaluation with `llama-3.1-8b-instant` to block off-topic queries and prompt injections early.
* 🤖 **Agentic Graph Orchestration:** Multi-node state workflow using `LangGraph` (`Planner` → `Retriever` → `Responder`).
* ⚡ **Zero-Token Memory Cache:** Identical conversational history lookups served directly from memory state checkpointers without token overhead.
* 🔄 **Portkey LLM Gateway:** Production multi-target routing, failover, and automated retries (`rag1` @ `llama-3.3-70b-versatile` → `rag3` @ `llama-3.1-8b-instant`).
* 🔍 **Hybrid Vector Search & Reranking:** Qdrant Cloud vector search paired with local ONNX Cross-Encoder (`FlashRank`).
* 📊 **RAGAS Evaluation Pipeline:** 6 metric evaluation suite measuring Faithfulness, Answer Relevancy, Context Precision/Recall, Answer Correctness, and Tool Correctness.
* 🐳 **Containerized & CI/CD Ready:** Automated AWS ECR push and EC2 deployment using GitHub Actions and Docker Supervisord multi-process management.

---

## 🏗️ System Architecture Overview

```text
                               ┌─────────────────────────┐
                               │ Streamlit UI / Client   │
                               │  (Port 8501 / 8502)     │
                               └────────────┬────────────┘
                                            │ HTTP Post /query
                                            ▼
                               ┌─────────────────────────┐
                               │   FastAPI Backend API   │
                               │       (Port 8080)       │
                               └────────────┬────────────┘
                                            │
                               ┌────────────▼────────────┐
                               │  NeMo Input Guardrails  │
                               └────────────┬────────────┘
                                            │ Passed
                                            ▼
                               ┌─────────────────────────┐
                               │ LangGraph Agent State   │
                               │  (Memory Checkpointer)  │
                               └────────────┬────────────┘
                                            │
                 ┌──────────────────────────┼──────────────────────────┐
                 │                          │                          │
                 ▼                          ▼                          ▼
       ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
       │   Planner Node   │       │  Retriever Node  │       │  Responder Node  │
       │ (Intent / Cache) │       │   (Qdrant DB)    │       │ (Portkey Gateway)│
       └──────────────────┘       └──────────────────┘       └──────────────────┘


.
├── .github/workflows/
│   └── deploy.yml            # GitHub Actions CI/CD deployment pipeline
├── app/
│   ├── agents/               # LangGraph state machine & node topology
│   │   ├── nodes/            # Planner, Retriever, Responder execution nodes
│   │   ├── graph.py          # StateGraph compilation & checkpointer setup
│   │   └── state.py          # AgentState Pydantic definitions
│   ├── gateway/              # Portkey client configuration & header routing
│   ├── guardrails/           # NeMo Guardrails Colang rules & rails engine
│   ├── ingestion/            # PDF, HTML, Office document parsers & splitters
│   ├── services/             # Qdrant client & FlashRank reranker wrappers
│   ├── config.py             # System settings & environment management
│   └── main.py               # FastAPI application entrypoint
├── evals/                    # Golden Q&A dataset & RAGAS evaluation runner
├── ui/                       # Streamlit interactive chat interface
├── Dockerfile                # Multi-stage production container build
├── supervisord.conf          # Process manager config for FastAPI & Streamlit
├── requirements.txt          # Unified project dependency specs
└── README.md                 # Project documentation




🛠️ Local Environment Setup
1. Prerequisites
Python 3.11+
Docker Desktop (optional for local containerization)

2. Installation
Clone the repository:
Bash
git clone [https://github.com/Yoosuf520/Production-Grade-RAG-Project.git](https://github.com/Yoosuf520/Production-Grade-RAG-Project.git)
cd Production-Grade-RAG-Project

Create a virtual environment and install dependencies:
Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

3. Environment Variables Setup
Create a .env file in the root directory:Code snippet

# Reasoning Engines & LLM Gateway
GROQ_API_KEY="your_groq_api_key"
GROQ_FALLBACK_API_KEY="your_fallback_groq_api_key"
PORTKEY_API_KEY="your_portkey_api_key"

# Vector Database
QDRANT_CLUSTER_ENDPOINT="[https://your-cluster.qdrant.tech](https://your-cluster.qdrant.tech)"
QDRANT_API_KEY="your_qdrant_api_key"

# Embeddings & Observability
GEMINI_API_KEY="your_gemini_api_key"
LOGFIRE_TOKEN="your_logfire_token"
JUDGE_GROQ="your_judge_groq_api_key"

# Application Settings
BACKEND_URL="http://localhost:8080"

🚀 Running the Project Locally
Option A: Direct Python Execution
Start the FastAPI Backend:
Bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

Start the Streamlit Chat UI:
Bash
streamlit run ui/app.py --server.port 8501

Start the Evaluation Suite Dashboard:
Bash
streamlit run evals/app.py --server.port 8502

Option B: Docker Containerization
Build and run all services in a single isolated container managed by Supervisord:
Bash# 
Build the Docker image
docker build -t enterprise-rag-app .

# Run container exposing all service ports
docker run -d \
  --name rag-container \
  -p 8080:8080 \
  -p 8501:8501 \
  -p 8502:8502 \
  --env-file .env \
  enterprise-rag-app

🔄 CI/CD & Deployment StrategyThe project utilizes GitHub Actions for continuous integration and deployment to AWS EC2 via Amazon ECR:

Code Push: Triggered automatically when commits land on the main branch.

Docker Build: GitHub runner builds the image using astral-sh/uv for fast dependency caching.

Registry Push: Authenticates with AWS ECR (ap-south-1) and tags the latest container build.

SSH Execution: Connects to the EC2 host via SSH, pulls the new image from ECR, and re-launches the container via Supervisord.

## 🧪 Evaluation & Benchmarking

The system incorporates an automated benchmarking framework powered by **RAGAS** across 6 core criteria:

| Metric | Target / Score Range | Evaluation Focus |
| :--- | :--- | :--- |
| **Faithfulness** | 0.0 - 1.0 | Verifies generated answer is strictly derived from retrieved context. |
| **Answer Relevancy** | 0.0 - 1.0 | Ensures directness and completeness without extra filler. |
| **Context Precision** | 0.0 - 1.0 | Assesses density of ground truth info in retrieved chunks. |
| **Context Recall** | 0.0 - 1.0 | Measures overall retrieval percentage of relevant context. |
| **Answer Correctness** | 0.0 - 1.0 | Semantic agreement against golden reference answers. |
| **Tool Correctness** | 0.0 - 1.0 | Jaccard similarity score on intended state graph node routing. |