#!/bin/bash

# LinkedIn Job Scraper Frontend Startup Script

echo "🚀 Starting LinkedIn Job Tracker Frontend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run the scraper first to set up the environment."
    exit 1
fi

# Check if database exists
if [ ! -f "data/linkedin_jobs.db" ]; then
    echo "❌ Database not found. Please run the scraper first to create the database."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Start API server in background
echo "🔌 Starting API server on http://localhost:5000..."
python api_server.py &
API_PID=$!

# Wait for API server to start
echo "⏳ Waiting for API server to start..."
sleep 3

# Check if API server is running
if ! curl -s http://localhost:5000/api/stats > /dev/null; then
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo "✅ API server is running!"

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start React frontend
echo "🌐 Starting React frontend on http://localhost:3001..."
cd frontend
PORT=3001 npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 LinkedIn Job Tracker is now running!"
echo ""
echo "📊 API Server: http://localhost:5000"
echo "🌐 Frontend:   http://localhost:3001"
echo ""
echo "📋 Available endpoints:"
echo "   - GET  /api/jobs          - List all jobs"
echo "   - GET  /api/jobs/:id      - Get specific job"
echo "   - POST /api/jobs/:id/toggle-like - Toggle job like"
echo "   - POST /api/jobs/:id/mark-applied - Mark job as applied"
echo "   - GET  /api/stats         - Get job statistics"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait 