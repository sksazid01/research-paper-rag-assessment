#!/bin/bash
# ⚠️  WARNING: Frontend REQUIRES Port 3456 to be FREE!
# Quick Port Conflict Handler for Port 3456

echo "⚠️  WARNING: You MUST free port 3456 to run the frontend!"
echo ""
echo "🔍 Checking port 3456..."

if lsof -i :3456 >/dev/null 2>&1; then
    echo "❌ Port 3456 is BUSY!"
    echo ""
    echo "Process using port 3456:"
    lsof -i :3456 | grep LISTEN
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Choose an action:"
    echo "  1. Kill the process and free port 3456"
    echo "  2. Just show the command (manual)"
    echo "  3. Cancel"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            echo ""
            echo "🔪 Killing process on port 3456..."
            sudo kill -9 $(lsof -t -i:3456)
            sleep 1
            if lsof -i :3456 >/dev/null 2>&1; then
                echo "❌ Failed to kill process"
            else
                echo "✅ Port 3456 is now free!"
                echo ""
                echo "Now run: docker compose up --build"
            fi
            ;;
        2)
            echo ""
            echo "Run this command manually:"
            echo "  sudo kill -9 \$(lsof -t -i:3456)"
            ;;
        3)
            echo "Cancelled."
            ;;
        *)
            echo "Invalid choice."
            ;;
    esac
else
    echo "✅ Port 3456 is FREE - ready for Docker!"
    echo ""
    echo "You can now run:"
    echo "  docker compose up --build"
fi
