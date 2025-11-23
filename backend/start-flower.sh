#!/bin/bash
# Start Flower monitoring dashboard

echo "Starting Flower dashboard..."
echo "Access at: http://localhost:5555"
celery -A celery_app flower
