# Backend - VERDICT API Server

This directory contains the FastAPI backend server for VERDICT, which provides AI-powered trading analysis and verification.

## Structure

```
backend/
├── app.py                      # Main FastAPI application
├── app_flare.py               # Flare Network integration
├── main.py                    # Alternative entry point
├── market_data.py             # Market data fetching
├── sentiment_analyzer.py      # AI sentiment analysis
├── decision_engine.py         # Trading decision logic
├── position_manager.py        # Position management
├── aptos_analyzer.py          # Aptos blockchain integration
├── flare_verifier.py          # Flare verification logic
├── flare_data_connector.py    # Flare Data Connector integration
├── ftso_price_feed.py         # FTSO price feed integration
├── component_monitor.py       # Component health monitoring
├── attack_simulator.py        # Security testing
├── rules_engine.py            # Verification rules engine
├── websocket_client.py        # WebSocket support
├── .env                       # Environment variables (not in git)
├── .env.example              # Example environment variables
├── requirements.txt           # Python dependencies
├── verification_rules.yaml    # Verification rules configuration
├── test_*.py                  # Test files
├── scripts/                   # Utility scripts
│   ├── setup.sh
│   ├── continuous_check.sh
│   ├── poll_agent.sh
│   └── test_api.sh
├── cache/                     # Cache directory
└── artifacts/                 # Build artifacts
```

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the server:**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

See `.env.example` for required environment variables:
- `CMC_API_KEY` - CoinMarketCap API key
- `GEMINI_API_KEY` - Google Gemini API key
- `FLARE_RPC_URL` - Flare Network RPC endpoint
- `VERIFIER_CONTRACT_ADDRESS` - Deployed verifier contract address
- And more...

## API Endpoints

- `POST /api/analyze` - Single token analysis
- `POST /api/start-agent` - Start autonomous agent loop
- `POST /api/stop-agent` - Stop autonomous agent loop
- `GET /api/component-status` - Component health status
- `POST /api/simulate-attack` - Simulate security attack
- `GET /api/rules` - Get verification rules
- `WS /ws` - WebSocket real-time updates

## Testing

Run tests with:
```bash
# Test API endpoints
bash scripts/test_api.sh

# Run specific test
python test_client.py
```

## Documentation

For complete API documentation, see:
- `../CURL_COMMANDS.md` - API examples
- `../SDK_USAGE_GUIDE.md` - SDK usage
- `../DEPLOYMENT_GUIDE.md` - Deployment instructions
