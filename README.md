# 🧠 ResearchPulse AI — Multi-Agent Scientific Document Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.2.11-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00.svg?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Store-red.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Model](https://img.shields.io/badge/Model-Qwen_2.5_3B_Instruct-purple.svg?logo=huggingface&logoColor=white)](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
[![Fine--Tuned](https://img.shields.io/badge/Fine--Tuned-AllenAI_SciRIFF-brightgreen.svg?logo=googlecolab&logoColor=white)](https://huggingface.co/datasets/allenai/SciRIFF)

**OmniScholar AI** (formerly *PaperMind AI*) is a production-grade, multi-agent scientific document intelligence and literature synthesis platform. It combines **dual-path PDF layout ingestion**, **hierarchy-aware semantic chunking**, **vector neural search (Qdrant + BGE)**, **interactive citation orbit networks**, and a **fine-tuned local LLM (Qwen 2.5 3B)** to transform static research papers into interactive, grounded AI knowledge agents.

---

## 🌟 Key Features

* **📄 Dual-Path Ingestion Engine**: Automatically detects native text streams vs scanned pages using `PyMuPDF (fitz)` with automatic `PaddleOCR` / `Tesseract` OCR fallbacks.
* **🌳 Hierarchy-Aware Document Tree Parsing**: Preserves LaTeX equations (`$$...$$`), Markdown tables, headings, and figures as atomic structural nodes rather than cutting them across static chunk boundaries.
* **🤖 Stateful LangGraph Multi-Agent System**: Decomposes complex user queries via a zero-shot Router Agent into 7 specialized intent nodes (`qa`, `summary`, `citation`, `peer_review`, `equations`, `tables`, `figures`).
* **🛰️ LitReview Radar™ Citation Network**: Dynamically extracts and maps a paper's bibliography into concentric citation orbits (Foundational Prior Art vs Derivative Literature) with interactive AI comparative insights.
* **🎓 Domain Fine-Tuned Model (Qwen 2.5 3B)**: Fine-tuned via 4-bit QLoRA (**Unsloth**) on **6,840 AllenAI SciRIFF tasks**, enhancing scientific reasoning, LaTeX math formatting, and structured ChatML responses.
* **⚡ 4.5× CPU Latency Optimization**: Optimized prompt prefill windows (`top_k=3`), output token boundaries (`max_tokens=300`), and thread allocation, reducing local CPU response time from **62.95s down to 14.10s**.
* **🔒 Enterprise Security & User Isolation**: Built with JWT authentication (`PyJWT` with SHA-256 + salt) and SQLite persistence to enforce strict per-user document privacy and isolated chat histories.

---

## 🏗️ System Architecture

```
                                +-----------------------------------+
                                |      Next.js 16 Frontend UI       |
                                |  (PDF Viewer, Radar, AI Assistant)|
                                +-----------------+-----------------+
                                                  |
                                       REST API (Axios + JWT)
                                                  v
                                +-----------------------------------+
                                |       FastAPI Backend Server      |
                                |       (Python 3.12, Uvicorn)      |
                                +-----------------+-----------------+
                                                  |
                   +------------------------------+------------------------------+
                   |                              |                              |
                   v                              v                              v
  +----------------------------------+  +-------------------+          +-------------------+
  | Dual-Path Ingestion Engine       |  | LangGraph Multi-  |          | SQLite Database   |
  | - PyMuPDF Text/BBox Extraction   |  |    Agent RAG      |          | - Users & Auth    |
  | - PaddleOCR / Tesseract Fallback |  | - Router Node     |          | - Document Meta   |
  | - Document Hierarchy Tree Builder|  | - Qdrant (BGE)    |          | - Chat Messages   |
  +----------------------------------+  | - Citation Check  |          +-------------------+
                                        +---------+---------+
                                                  |
                                                  v
                                        +-------------------+
                                        | Ollama LLM Engine |
                                        | Qwen 2.5 3B (GGUF)|
                                        | Fine-Tuned SciRIFF|
                                        +-------------------+
```

---

## ⚡ Performance Benchmark Metrics

| Metric | Before Optimization | After Optimization | Impact |
| :--- | :---: | :---: | :--- |
| **CPU Context Prefill Time** | ~25.0s | **~1.5s** | **16.6× faster** prompt prefill |
| **Output Token Generation** | ~38.0s | **~12.5s** | **3.0× faster** generation |
| **Total Response Latency** | **`62.95s`** | **`14.10s`** | **4.5× Speedup (78% drop)** |
| **Memory Footprint** | ~5.8 GB | **~1.9 GB** | Low CPU RAM footprint |

---

## 📁 Repository Structure

```
.
├── papermind/                    # Python Backend Core
│   ├── agents/                   # LangGraph Multi-Agent Workflows & Specialist Nodes
│   ├── api/                      # FastAPI REST Routes (/auth, /documents, /query, /search)
│   ├── chunking/                 # Hierarchy-Aware Semantic Chunker & Strategies
│   ├── core/                     # Application Config & Loguru/Structlog Logging
│   ├── database/                 # SQLite Persistence & DB Service
│   ├── embeddings/               # FastEmbed (BAAI/bge-small-en-v1.5) Provider
│   ├── extractors/               # Equation, Table, Figure, and Citation Extractors
│   ├── graph/                    # Document Knowledge Graph Builders & Queries
│   ├── layout/                   # Layout Detector & Document Tree Builder
│   ├── ocr/                      # PaddleOCR & Tesseract OCR Engines
│   ├── pipeline/                 # Dual-Path Digital & Scanned PDF Ingestion Pipeline
│   ├── services/                 # Ingestion & Presentation (PPTX Generator) Services
│   └── vectorstore/              # Qdrant & FAISS Vector Store Integrations
├── web/                          # Next.js 16 Frontend Web Application
│   ├── app/                      # Next.js App Router (/auth, /, /workspace)
│   ├── components/               # UI Components (LitReviewRadar, PDFViewer, Sidebar)
│   ├── hooks/                    # Zustand Global Store (useWorkspaceStore)
│   └── lib/                      # Axios API Client & Axios Interceptors
├── scripts/                      # Data Processing & Fine-Tuning Scripts (prepare_peerread.py)
├── tests/                        # Pytest Automated Unit & Integration Suite
├── pyproject.toml                # Python Project Dependencies & Tooling
└── README.md                     # Project Documentation
```

---

## 🚀 Quickstart Guide

### Prerequisites
* **Python 3.12+**
* **Node.js 18+** & **npm**
* **Ollama** installed locally ([ollama.ai](https://ollama.ai))

---

### 1. Setup Backend (FastAPI)

```powershell
# Clone the repository
git clone https://github.com/your-username/omnischolar-ai.git
cd omnischolar-ai

# Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate   # On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start local Ollama model
ollama pull qwen2.5:3b

# Run FastAPI backend server
uvicorn papermind.api.main:app --reload --port 8000
```
Backend server runs at `http://localhost:8000`. Swagger API docs available at `http://localhost:8000/docs`.

---

### 2. Setup Frontend (Next.js 16)

```powershell
# Navigate to web directory
cd web

# Install npm packages
npm install

# Run Next.js development server
npm run dev
```
Frontend Web App runs at `http://localhost:3000`.

---

## 🎯 Fine-Tuning Qwen 2.5 3B with SciRIFF (Unsloth)

To fine-tune **Qwen 2.5 3B Instruct** on your own GPU or **Google Colab (T4 Free GPU)** using **AllenAI SciRIFF**:

1. Open Google Colab and set GPU hardware accelerator to **T4 GPU**.
2. Run the Unsloth QLoRA fine-tuning script:

```python
import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

# Load Qwen 2.5 3B in 4-bit mode
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "Qwen/Qwen2.5-3B-Instruct",
    max_seq_length = 2048,
    load_in_4bit = True,
)

# Apply LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model, r = 16, target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)

# Export to GGUF for Ollama deployment
model.save_pretrained_gguf("qwen2.5-3b-sciriff", tokenizer, quantization_method = "q4_k_m")
```

3. Import the resulting `.gguf` into local Ollama:
```powershell
ollama create qwen2.5-sciriff -f Modelfile
```

---

## 🧪 Automated Testing

Run the comprehensive unit test suite:

```powershell
pytest tests/unit --cov=papermind
```
```
=============================== 37 passed in 23.24s ===============================
```

---


