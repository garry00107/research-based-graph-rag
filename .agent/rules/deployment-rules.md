# Deployment & Infrastructure Rules

## Docker Configuration
- All services must be defined in `docker-compose.yml`
- Backend runs on port 8002, Frontend on 3000
- Redis is required for Chat History and Async Ingestion
- Data persistence paths:
  - ChromaDB: `./backend/chroma_db`
  - Redis: `redis-data` volume
  - Papers: `./backend/data/papers`

## Environment Variables
- `REDIS_ENABLED` must be `true` for production features
- `NVIDIA_API_KEY` is required for all RAG operations
- `CHROMA_PERSIST_DIR` should point to a mounted volume in Docker

## Async Processing (Celery)
- Long-running tasks (ingestion) must use Celery
- Worker must be started separately in dev: `./start-celery.sh`
- Flower dashboard available on port 5555 for monitoring
- Task status endpoints: `/task-status/{task_id}`

## Caching Strategy
- Embeddings: Cached in Redis (TTL: 24h)
- Chat History: Cached in Redis (TTL: 24h)
- Papers Library: Cached in Redis + JSON file backup
- Cache keys must follow `prefix:id` pattern (e.g., `conv:default`, `papers:library`)
