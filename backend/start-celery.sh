#!/bin/bash
# Start Celery worker for async ingestion

echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info
