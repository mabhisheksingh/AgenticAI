#!/bin/bash

# Build script for AgenticAI
# This script builds both the backend and frontend

set -e  # Exit on any error

echo "Building AgenticAI..."

# Build backend
echo "Building backend..."
pip install -r requirements.txt

# Build frontend if ui directory exists
if [ -d "ui" ]; then
    echo "Building frontend..."
    cd ui
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    echo "Running frontend build..."
    npm run build
    cd ..
fi

echo "Build completed successfully!"