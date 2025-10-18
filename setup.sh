#!/bin/bash
# HackNU Dropouts Backend - Quick Setup Script

set -e

echo "🚀 HackNU Dropouts Backend Setup"
echo "=================================="
echo ""

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create it first: python -m venv .venv"
    exit 1
fi

# Activate venv
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚙️  IMPORTANT: Edit .env and add your Higgsfield API credentials:"
    echo "   - HIGGSFIELD_API_KEY"
    echo "   - HIGGSFIELD_API_SECRET"
    echo ""
fi

# Test import
echo "🧪 Testing app import..."
python -c "from app.main import app; print('✅ App imports successfully')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env and add your Higgsfield API keys"
echo "   2. Run: uvicorn app.main:app --reload"
echo "   3. Visit: http://localhost:8000/docs"
echo ""
echo "📖 See QUICKSTART.md for more details"

