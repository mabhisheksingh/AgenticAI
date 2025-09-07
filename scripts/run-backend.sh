#!/bin/bash

# Script to run the backend service

echo "Starting AgenticAI Backend Service..."
echo "Make sure you have activated your virtual environment and installed dependencies"
echo "If not, run: pipenv shell (or activate your venv) and pip install -r requirements.txt"

# Check if pipenv is available
if command -v pipenv &> /dev/null
then
    echo "Using pipenv to run backend..."
    pipenv run python -m app.main
else
    echo "Using direct python to run backend..."
    python -m app.main
fi