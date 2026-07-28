# NCERT Class 12 AI Tutor

## Overview
This repository contains my implementation for the local AI tutor capable of answering Class 12 CBSE Mathematics, Physics, and Chemistry questions. 

The core requirements have been met by ingesting the official NCERT PDFs into a lightweight local vector database, utilizing Retrieval-Augmented Generation (RAG) to ensure accuracy, and implementing strict guardrails to politely refuse out-of-scope questions.

---

## Architecture & Data Flow

To solve this while strictly adhering to the design guidelines (specifically, avoiding over-engineering and heavy frameworks like LangChain), the solution implements a clean, linear flow:

1. **Data Ingestion (`data/ingest.py`)**: 
   - A standalone script that reads `data/manifest.json`.
   - Extracts text page-by-page from the NCERT PDFs using `PyMuPDF`.
   - Chunks the text using `tiktoken`.
   - Generates embeddings using **`fastembed`** (`BAAI/bge-small-en-v1.5`), running 100% locally and for free, and stores them in a highly efficient `faiss-cpu` vector index (`data/index.faiss`).
2. **Backend Retrieval (`backend/agent.py`)**: 
   - The FastAPI server loads the FAISS index into memory on startup.
   - When a user asks a question, the `StarterAgent` locally embeds the query and performs a lightning-fast vector search to retrieve the top 5 most relevant context chunks.
3. **Guardrails & Generation (`backend/constants.py`)**:
   - The retrieved chunks (with source citations) are injected into the `SYSTEM_PROMPT`.
   - We use the **Groq API** (via the `groq` Python SDK) for blazing-fast and free LLM inference (`llama-3.1-8b-instant`).
   - Instead of using a separate latency-heavy LLM call for routing, the system prompt strictly instructs the LLM to refuse out-of-scope queries (like cricket or general knowledge) and answer syllabus questions using *only* the injected textbook context.
4. **Kid-Friendly Frontend (`frontend/`)**:
   - A highly polished, custom React application built with Vite.
   - It implements a space-themed, glassmorphism design system using Vanilla CSS (no Tailwind) to ensure the UI is extremely engaging for students while keeping the codebase aligned with simple design guidelines.

### ⚖️ Tradeoffs & Design Decisions
- **Groq API vs OpenAI**: We switched from OpenAI to Groq for text generation. *Tradeoff*: Groq offers significantly faster inference and a generous free tier for open-source models like Llama 3.1, which is ideal for a local tutor.
- **Local Embeddings vs API Embeddings**: Since Groq doesn't offer embedding models, we switched to `fastembed` running locally. *Tradeoff*: Zero API costs and complete data privacy, completely avoiding PyTorch bloat, at the cost of a small initial download for the ONNX model weights when first running the ingestion script.
- **FAISS vs Persistent DB**: We chose `faiss-cpu` for extreme simplicity. It runs purely locally without requiring a dedicated database server (like Postgres) or container.
- **Guardrails via Prompting**: Out-of-scope refusal is handled efficiently via the main system prompt routing rather than wasting latency on a separate preceding LLM classification call.
- **React Frontend vs Vanilla JS**: We opted for a lightweight React app over Vanilla JS to cleanly manage chat state (message history, loading spinners). We intentionally avoided Tailwind CSS to maintain total control over the custom glassmorphism aesthetics as requested.

---

## Setup & Installation

**1. Create Virtual Environment & Install Dependencies**
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

**2. Configure Environment Variables**
Copy the example environment file and add your Groq API Key:
```bash
cp backend/.env.example backend/.env
# Open backend/.env and set GROQ_API_KEY=your_key_here
```

**3. Setup Frontend Dependencies**
```bash
cd frontend
npm install
cd ..
```

---

## Data Ingestion (Required First Step)

> **IMPORTANT:** Because the NCERT textbooks and the resulting vector databases are extremely large files, they are intentionally excluded from this repository via `.gitignore`. You must generate the local database yourself before running the API!

1. Download the 6 required Class 12 NCERT books (Mathematics Part I & II, Physics Part I & II, Chemistry Part I & II) from the official website.
2. Place the PDFs (or folders of chapter PDFs) directly into the `data/raw/` directory. Ensure the files or folders are named exactly as follows (matching `data/manifest.json`):
   - `mathematics_part_1` (or `.pdf`)
   - `mathematics_part_2` (or `.pdf`)
   - `physics_part_1` (or `.pdf`)
   - `physics_part_2` (or `.pdf`)
   - `chemistry_part_1` (or `.pdf`)
   - `chemistry_part_2` (or `.pdf`)
3. Run the ingestion script to parse the textbooks and build the local knowledge base:

```bash
source backend/.venv/bin/activate
python data/ingest.py
```
*(This script uses a local `fastembed` ONNX model to extract, chunk, and embed the books entirely on your machine. Once finished, it will generate the `data/index.faiss` and `data/metadata.json` files needed by the API.)*

---

## Running the Application End-to-End

To use the AI Tutor, you will need to run the backend and frontend simultaneously in two separate terminals.

**Terminal 1 (Start the Backend API):**
```bash
source backend/.venv/bin/activate
PYTHONPATH=. uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Start the Frontend UI):**
```bash
cd frontend
npm run dev
```

Once both are running, open `http://localhost:5173` in your browser to interact with the AI Tutor!

### Chat API (Manual Testing)
You can test the bot manually using `curl` while the API is running:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Explain definite integrals."}]}'
```

---

## Evaluations

With the backend server running, open a **new terminal window** and run the evaluation suite to verify behavior against the syllabus and out-of-scope prompts:
```bash
source backend/.venv/bin/activate
PYTHONPATH=. python -m evals.run_evals
```
Reports are written to `evals/reports/`.
