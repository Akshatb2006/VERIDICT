#!/bin/bash

# SentenexAI Backend Deployment Script for Render

# Exit on error
set -e

echo "🚀 Starting SentenexAI Backend Deployment..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create cache directory if it doesn't exist
echo "📁 Creating cache directory..."
mkdir -p cache

# Verify environment variables
echo "🔍 Verifying environment variables..."
if [ -z "$CMC_API_KEY" ]; then
    echo "⚠️ WARNING: CMC_API_KEY not set!"
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️ WARNING: GEMINI_API_KEY not set!"
fi

echo "✅ Deployment preparation complete!"
echo "🎯 Starting server with Uvicorn..."
