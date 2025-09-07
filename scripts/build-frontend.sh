#!/bin/bash

# Build script for frontend
# This script builds the React frontend and copies the output to the dist directory

set -e  # Exit on any error

echo "Building frontend..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Please run this script from the ui directory."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the frontend
echo "Running build..."
npm run build

# Create dist directory if it doesn't exist
mkdir -p dist

# Copy build output to dist directory
echo "Copying build output to dist directory..."
cp -r build/* dist/

echo "Frontend build completed successfully!"