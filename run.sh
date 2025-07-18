#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Set default values if not provided in .env
FLASK_HOST=${FLASK_HOST:-0.0.0.0}
FLASK_PORT=${FLASK_PORT:-8084}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the Gunicorn server
echo "🚀 Starting Gunicorn server on ${FLASK_HOST}:${FLASK_PORT} with ${GUNICORN_WORKERS} workers..."
gunicorn --workers ${GUNICORN_WORKERS} --bind ${FLASK_HOST}:${FLASK_PORT} app:app 