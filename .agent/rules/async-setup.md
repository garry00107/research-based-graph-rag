# Async Ingestion Setup

## Services Required

### 1. Redis (Message Broker)
```bash
# Option A: Install and run locally
brew install redis
redis-server

# Option B: Use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Celery Worker
```bash
cd backend
./start-celery.sh
# OR
celery -A celery_app worker --loglevel=info
```

### 3. Flower Dashboard (Optional)
```bash
cd backend
./start-flower.sh
# OR
celery -A celery_app flower
# Access at http://localhost:5555
```

## Testing Async Ingestion

### Using curl:
```bash
# Start async ingestion
curl -X POST http://localhost:8002/ingest-async \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "1706.03762"}'

# Check task status
curl http://localhost:8002/task-status/{task_id}
```

## Without Redis
Sync endpoints still work:
- POST /ingest
- POST /ingest-batch
