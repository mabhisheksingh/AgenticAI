#!/bin/bash

# Test script for Docker setup
# This script tests the Docker build and run process

set -e  # Exit on any error

echo "Testing Docker setup..."

# Test single container build
echo "Building single container..."
docker build -t agenticai-test .

# Test docker-compose build
echo "Building with docker-compose..."
docker-compose build

# Test simplified docker-compose build
echo "Building with simplified docker-compose..."
docker-compose -f docker-compose.simple.yml build

echo "Docker setup test completed successfully!"