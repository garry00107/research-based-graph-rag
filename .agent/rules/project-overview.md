# Research Paper Assistant - Project Overview

## Purpose
AI-powered research assistant for ArXiv papers using graph-based retrieval, NVIDIA models, and modern web technologies.

## Tech Stack
- Backend: FastAPI + LlamaIndex + ChromaDB + Redis
- Frontend: Next.js 14 + TypeScript + TailwindCSS
- LLM: NVIDIA meta/llama-3.2-3b-instruct
- Embeddings: NVIDIA nvidia/nv-embedqa-e5-v5

## Key Files
- backend/main.py - FastAPI endpoints
- backend/rag_engine.py - RAG with ChromaDB
- backend/cache.py - Redis caching
- frontend/components/chat-interface.tsx - Chat UI
- frontend/components/admin-panel.tsx - Search UI
- frontend/components/papers-library.tsx - Library UI
- frontend/components/chat-history.tsx - History UI

## Current Status
Phase 1 Complete: ChromaDB, Docker, Batch Embeddings, Redis Cache
Phase 2 Complete: Async ingestion, Streaming, Chat history, Papers Library
Phase 3 Planned: Advanced filters, Analytics
