#!/usr/bin/env python3
"""Test which Gemini models are available with your API key"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✅ API Key found: {api_key[:20]}...")
print("\n📋 Available Gemini models:\n")

# Configure and list models
genai.configure(api_key=api_key)

try:
    for model in genai.list_models():
        if 'generate Content' in model.supported_generation_methods:
            print(f"  ✓ {model.name}")
    print("\n✅ Done! Use one of the models above in your code.")
except Exception as e:
    print(f"\n❌ Error listing models: {e}")
    print("\nℹ️  This might mean:")
    print("   1. Invalid API key")
    print("   2. Network issue")
    print("   3. API quota exceeded")
