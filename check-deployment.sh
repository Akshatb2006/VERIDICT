#!/bin/bash

# SentenexAI Quick Deployment Helper
# This script helps you quickly check if you're ready to deploy

echo "🚀 SentenexAI Deployment Readiness Check"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "render.yaml" ] || [ ! -f "netlify.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "✅ Configuration files found"
echo ""

# Check Git status
echo "📊 Git Status:"
if command -v git &> /dev/null; then
    if [ -d ".git" ]; then
        UNCOMMITTED=$(git status --porcelain | wc -l)
        if [ $UNCOMMITTED -eq 0 ]; then
            echo "✅ All changes committed"
        else
            echo "⚠️  You have $UNCOMMITTED uncommitted files"
            echo "   Run: git add . && git commit -m 'Ready for deployment' && git push"
        fi
        
        BRANCH=$(git branch --show-current)
        echo "📌 Current branch: $BRANCH"
    else
        echo "❌ Not a git repository. Initialize with: git init"
    fi
else
    echo "⚠️  Git not installed"
fi
echo ""

# Check environment files
echo "🔑 Environment Configuration:"
if [ -f "backend/.env" ]; then
    echo "✅ backend/.env exists"
    if grep -q "CMC_API_KEY=YOUR_" backend/.env; then
        echo "⚠️  CMC_API_KEY not configured (still has placeholder)"
    else
        echo "✅ CMC_API_KEY configured"
    fi
    
    if grep -q "GEMINI_API_KEY=YOUR_" backend/.env; then
        echo "⚠️  GEMINI_API_KEY not configured (still has placeholder)"
    else
        echo "✅ GEMINI_API_KEY configured"
    fi
else
    echo "⚠️ backend/.env not found (you'll set env vars on Render)"
fi
echo ""

# Check API URL configuration
echo "🌐 Frontend API Configuration:"
if grep -q "your-backend-app.onrender.com" frontend/dashboard.html; then
    echo "⚠️  Update frontend/dashboard.html line ~1035 with your Render URL"
    echo "   (You can do this after deploying the backend)"
else
    echo "✅ API URL configured in frontend"
fi
echo ""

# Deployment checklist
echo "📋 Deployment Checklist:"
echo ""
echo "BACKEND (Render):"
echo "  1. Go to https://render.com and sign up"
echo "  2. Create new Web Service from GitHub repo"
echo "  3. Use these settings:"
echo "     - Build: cd backend && pip install -r requirements.txt"
echo "     - Start: cd backend && uvicorn app:app --host 0.0.0.0 --port \$PORT"
echo "  4. Add environment variables (CMC_API_KEY, GEMINI_API_KEY)"
echo "  5. Deploy and note the URL"
echo ""
echo "FRONTEND (Netlify):"
echo "  1. Update frontend/dashboard.html with your Render backend URL"
echo "  2. Commit: git add . && git commit -m 'Update API URL'"
echo "  3. Push: git push origin main"
echo "  4. Go to https://netlify.com and sign up"
echo "  5. Deploy from GitHub (base directory: frontend)"
echo ""
echo "FINAL STEPS:"
echo "  1. Add Netlify URL to Render env var: ALLOWED_ORIGINS"
echo "  2. Test: Visit your Netlify URL and activate the agent"
echo ""
echo "📖 Full instructions: See DEPLOYMENT_INSTRUCTIONS.md"
echo ""
echo "✨ Good luck with your deployment!"
