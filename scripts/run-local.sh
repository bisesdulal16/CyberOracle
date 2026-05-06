#!/bin/bash

# CyberOracle Local Development Runner
# This script starts both the backend and frontend for local development

echo "Starting CyberOracle Local Development Environment"
echo "=================================================="

# Start backend services
echo "Starting backend services..."
cd ..
docker-compose up -d db
docker-compose up -d api

# Wait a moment for services to start
sleep 3

# Check if backend is running
if docker ps | grep -q cyberoracle-api; then
    echo "✅ Backend API is running"
else
    echo "❌ Backend API failed to start"
    exit 1
fi

# Start frontend
echo "Starting frontend..."
cd ui/ui
npm install > /dev/null 2>&1
npm run dev &

echo "✅ Frontend is running on http://localhost:3000"
echo ""
echo "CyberOracle is ready for development!"
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "To stop the services, run: docker-compose down"