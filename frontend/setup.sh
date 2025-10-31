#!/bin/bash

echo "🚀 Setting up Research Paper RAG Frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Frontend setup complete!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Make sure the backend API is running on http://localhost:8000"
    echo "   2. Run: npm run dev"
    echo "   ⚠️  WARNING: Port 3456 MUST be free!"
    echo "   3. Open: http://localhost:3456"
    echo ""
else
    echo ""
    echo "❌ Failed to install dependencies"
    exit 1
fi
