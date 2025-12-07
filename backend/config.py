"""
Production-ready configuration for SentenexAI/VERDICT API
"""
import os

# Environment detection
ENV = os.getenv("ENVIRONMENT", "production")
IS_PRODUCTION = ENV == "production"

# CORS Settings
# In production, restrict to your frontend domain
# In development, allow all origins for testing
ALLOWED_ORIGINS = [
    "https://your-app-name.netlify.app",  # Replace with your Netlify URL
    "https://www.your-custom-domain.com",  # Replace with your custom domain if any
    "http://localhost:8080",  # Local development
    "http://localhost:3000",  # Alternative local port
    "http://127.0.0.1:8080",
]

# If in development, allow all origins
if not IS_PRODUCTION:
    ALLOWED_ORIGINS = ["*"]

# API Configuration
API_RATE_LIMIT = {
    "calls": 100,
    "period": 60  # 100 calls per 60 seconds
}

# Caching Configuration
CACHE_ENABLED = True
CACHE_TTL_SECONDS = {
    "market_data": 30,  # Cache market data for 30 seconds
    "sentiment": 300,   # Cache sentiment analysis for 5 minutes
    "onchain": 60       # Cache on-chain data for 1 minute
}

# Logging Configuration
LOG_LEVEL = "INFO" if IS_PRODUCTION else "DEBUG"

# Health Check Settings
HEALTH_CHECK_PATH = "/health"
