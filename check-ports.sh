#!/bin/bash
# Port Conflict Resolution Script

echo "🔍 Checking for port conflicts..."
echo ""

# Function to check and handle port conflicts
check_port() {
    local port=$1
    local service=$2
    
    echo "Checking port $port ($service)..."
    
    # Check if port is in use
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is BUSY"
        
        # Show what's using it
        echo "Used by:"
        lsof -i :$port | grep LISTEN
        
        echo ""
        echo "Options:"
        echo "  1. Kill the process: sudo kill \$(lsof -t -i:$port)"
        echo "  2. Stop npm dev server: pkill -f 'next dev'"
        echo "  3. Use different port in docker-compose.yml"
        echo ""
        return 1
    else
        echo "✅ Port $port is FREE"
        return 0
    fi
}

# Check all required ports
echo "=== Frontend Port ==="
check_port 3000 "Frontend"
frontend_status=$?

echo ""
echo "=== Backend Port ==="
check_port 8000 "Backend API"
api_status=$?

echo ""
echo "=== Database Ports ==="
check_port 5433 "PostgreSQL"
check_port 6333 "Qdrant"

echo ""
echo "==================================="

if [ $frontend_status -eq 1 ]; then
    echo ""
    echo "🔧 Quick Fixes for Port 3000 Conflict:"
    echo ""
    echo "Fix 1: Kill conflicting process"
    echo "  sudo kill \$(lsof -t -i:3000)"
    echo ""
    echo "Fix 2: Stop your local npm dev server"
    echo "  cd frontend && pkill -f 'next dev'"
    echo ""
    echo "Fix 3: Change Docker frontend port to 3001"
    echo "  Edit docker-compose.yml:"
    echo "  ports:"
    echo "    - \"3001:3000\"  # Access at http://localhost:3001"
    echo ""
fi

if [ $api_status -eq 1 ]; then
    echo ""
    echo "🔧 Quick Fix for Port 8000 Conflict:"
    echo "  docker compose down  # Stop all containers"
    echo ""
fi

echo "==================================="
echo ""
echo "After fixing conflicts, run:"
echo "  docker compose up --build"
