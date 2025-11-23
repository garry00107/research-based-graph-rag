# Graph RAG Agent

A RAG agent using NVIDIA models and Graph-based retrieval to answer questions about ArXiv papers.

## Prerequisites

- Python 3.10+
- Node.js 18+
- NVIDIA NIM API Key

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# IMPORTANT: Set your API Key
cp .env.example .env
# Open .env and paste your NVIDIA_API_KEY
```

Start the server:
```bash
python main.py
```
Server runs on `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
```

Start the development server:
```bash
npm run dev
```
Frontend runs on `http://localhost:3000`.

## Usage

1. Open the Frontend.
2. Click the **Settings** icon (top right) to open the Admin Panel.
3. Enter an ArXiv ID (e.g., `1706.03762` for "Attention is All You Need") and click Upload.
4. Wait for ingestion to complete.
5. Ask questions in the chat interface.
