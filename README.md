# VERDICT - AI-Powered Crypto Trading Analyzer with Sentiment Analysis

A FastAPI-based real-time trading analyzer that combines market data, AI-powered sentiment analysis, and on-chain metrics to provide LONG/SHORT/HOLD recommendations for perpetual DEX trading on Aptos.

## Features

- 🚀 **FastAPI REST API**: Single analysis endpoint
- 🔄 **Real-time WebSocket Streaming**: Get recommendations every second
- 📊 **Real-time Market Data**: Fetches live price, volume, and market cap from CoinMarketCap
- 🤖 **AI Sentiment Analysis**: Uses OpenAI GPT-4 to analyze market sentiment
- ⛓️ **On-Chain Analysis**: Analyzes Aptos blockchain data for trading signals
- 🎯 **Smart Recommendations**: Combines all signals to suggest LONG, SHORT, or HOLD
- 💰 **Perp DEX Integration**: Provides leverage suggestions and calculates potential PnL based on your token amount

## Setup

1. **Navigate to Backend Directory**
   ```bash
   cd backend
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   
   Create a `.env` file in the backend directory:
   ```env
   CMC_API_KEY=your_coinmarketcap_api_key
   GEMINI_API_KEY=your_gemini_api_key
   FLARE_RPC_URL=your_flare_rpc_url
   VERIFIER_CONTRACT_ADDRESS=your_contract_address
   ```

4. **Get API Keys**
   - **CoinMarketCap**: Sign up at https://coinmarketcap.com/api/
   - **Gemini AI**: Get your API key from Google AI Studio

## Running the API

### Start the FastAPI Server
```bash
cd backend
python app.py
```

Or using uvicorn directly:
```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### 1. Single Analysis (REST)
**POST** `/api/analyze`

Get a one-time analysis for a token.

**Request Body:**
```json
{
  "token": "APT",
  "amount": 100.0
}
```

**Response:**
```json
{
  "token": "APT",
  "amount": 100.0,
  "timestamp": "2024-01-15T10:30:00",
  "recommendation": "LONG",
  "confidence": 78.5,
  "signal_score": 35.67,
  "market_data": {
    "price": 8.5234,
    "market_cap": 1234567890,
    "volume_24h": 45234567,
    "percent_change_1h": 0.5,
    "percent_change_24h": 2.45,
    "percent_change_7d": 5.67
  },
  "sentiment_data": {
    "overall_sentiment": 45.23,
    "short_term_sentiment": 38.67,
    "risk_level": "Medium",
    "key_factors": ["Strong volume", "Positive momentum"]
  },
  "onchain_data": {
    "onchain_signal": 25.50,
    "activity_score": 0.75,
    "liquidity_score": 0.68
  },
  "leverage_suggestion": {
    "suggested_leverage": 10,
    "max_safe_leverage": 20
  },
  "perp_trade_example": {
    "collateral_usd": 852.34,
    "suggested_leverage": 10,
    "position_size_usd": 8523.40,
    "current_price": 8.5234,
    "token_amount": 100.0,
    "if_price_moves_5pct_up": {
      "pnl": 426.17,
      "roi_pct": 50.0
    },
    "if_price_moves_5pct_down": {
      "pnl": -426.17,
      "roi_pct": -50.0
    }
  },
  "reasoning": "Overall signal score: 35.67 | 24h price change: +2.45%"
}
```

### 2. Real-time Streaming (WebSocket)
**WebSocket** `/ws/stream`

Get continuous updates every second with LONG/SHORT/HOLD recommendations.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');

// Send initial message
ws.send(JSON.stringify({
  "token": "APT",
  "amount": 100.0
}));

// Receive updates every second
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Recommendation:', data.recommendation);
  console.log('Confidence:', data.confidence);
  // ... process data
};
```

**Python Example:**
```python
import asyncio
import websockets
import json

async def stream():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "token": "APT",
            "amount": 100.0
        }))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Recommendation: {data['recommendation']}")
            print(f"Confidence: {data['confidence']}%")

asyncio.run(stream())
```

### 3. Health Check
**GET** `/api/health`

Check API health and service status.

## Testing

### Test WebSocket Stream
```bash
python test_client.py
```

### Test REST Endpoint
```bash
python test_client.py rest
```

Or using curl:
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "amount": 100.0}'
```

## Understanding Recommendations

### LONG Recommendation
- Open a long position (buy)
- Profit when price goes up
- Example: With 100 APT at $8.52, 10x leverage = $8,523 position
  - If price ↑ 5%: Profit $426 (50% ROI)
  - If price ↓ 5%: Loss $426 (-50% ROI)

### SHORT Recommendation
- Open a short position (sell)
- Profit when price goes down
- Example: With 100 APT at $8.52, 10x leverage = $8,523 position
  - If price ↓ 5%: Profit $426 (50% ROI)
  - If price ↑ 5%: Loss $426 (-50% ROI)

### HOLD Recommendation
- Conditions are neutral
- Wait for clearer signals before entering a position

## How It Works

### 1. Market Data Collection
- Fetches real-time price, volume, and market metrics from CoinMarketCap
- Tracks 1h, 24h, and 7d price changes

### 2. Sentiment Analysis
- Uses OpenAI GPT-4 to analyze market conditions
- Generates sentiment scores (-100 to +100)
- Identifies key factors influencing the token
- Assesses risk levels (Low/Medium/High)

### 3. On-Chain Analysis
- Analyzes Aptos blockchain activity
- Tracks transaction volume and liquidity metrics
- Generates on-chain trading signals

### 4. Decision Engine
- Combines all signals with weighted scoring:
  - Sentiment: 35%
  - Market Momentum: 30%
  - On-Chain Signals: 20%
  - Risk Assessment: 15%
- Generates final recommendation (LONG/SHORT/HOLD)
- Suggests appropriate leverage based on confidence and risk
- Calculates potential PnL based on your token amount

## Project Structure

```
SentenexAI/
├── backend/                   # Backend API Server
│   ├── app.py                 # Main FastAPI application
│   ├── app_flare.py          # Flare Network integration
│   ├── main.py               # CLI version 
│   ├── market_data.py        # CoinMarketCap API integration
│   ├── sentiment_analyzer.py # AI sentiment analysis
│   ├── aptos_analyzer.py     # Aptos on-chain data analysis
│   ├── decision_engine.py    # Signal combination & recommendation
│   ├── position_manager.py   # Position management
│   ├── flare_verifier.py     # Flare verification logic
│   ├── flare_data_connector.py # FDC integration
│   ├── ftso_price_feed.py    # FTSO price feeds
│   ├── component_monitor.py  # Component health monitoring
│   ├── attack_simulator.py   # Security testing
│   ├── rules_engine.py       # Verification rules engine
│   ├── websocket_client.py   # WebSocket support
│   ├── test_*.py             # Test files
│   ├── .env                  # Environment variables
│   ├── requirements.txt      # Python dependencies
│   ├── verification_rules.yaml # Rules configuration
│   ├── scripts/              # Utility scripts
│   │   ├── setup.sh
│   │   ├── continuous_check.sh
│   │   ├── poll_agent.sh
│   │   └── test_api.sh
│   ├── cache/                # Cache directory
│   └── artifacts/            # Build artifacts
│
├── frontend/                  # Web Dashboard
│   ├── dashboard.html        # Main trading dashboard
│   └── verification.html     # Flare verification UI
│
├── contracts/                 # Smart Contracts
│   ├── VerifierContract.sol  # Flare verifier contract
│   └── scripts/              # Deployment scripts
│
├── sdk-python/               # Python SDK
│   ├── verdict_sdk/          # SDK source code
│   ├── examples/             # Usage examples
│   ├── setup.py              # Package setup
│   └── README.md             # SDK documentation
│
├── README.md                 # This file
├── CURL_COMMANDS.md          # API examples
├── SDK_USAGE_GUIDE.md        # SDK usage guide
├── DEPLOYMENT_GUIDE.md       # Deployment instructions
└── *.md                      # Other documentation
```

## Frontend Integration Example

### JavaScript/TypeScript
```typescript
const ws = new WebSocket('ws://localhost:8000/ws/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    token: 'APT',
    amount: 100.0
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Update UI with recommendation
  updateRecommendation(data.recommendation);
  updateConfidence(data.confidence);
  updatePrice(data.market_data.price);
  updatePnL(data.perp_trade_example);
};
```

### React Hook Example
```typescript
import { useEffect, useState } from 'react';

function usePerpDEXStream(token: string, amount: number) {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/stream');
    
    ws.onopen = () => {
      ws.send(JSON.stringify({ token, amount }));
    };
    
    ws.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };
    
    return () => ws.close();
  }, [token, amount]);
  
  return data;
}
```

## Risk Disclaimer

⚠️ **This tool is for informational purposes only. Trading cryptocurrencies, especially with leverage on perpetual DEX platforms, carries significant risk. Always:**

- Do your own research (DYOR)
- Never invest more than you can afford to lose
- Understand the risks of leverage trading
- Consider using stop-loss orders
- Start with small positions

## Future Enhancements

- Integration with actual Aptos indexer APIs for real on-chain data
- Social media sentiment analysis (Twitter, Reddit, etc.)
- Historical performance tracking
- Multi-token portfolio analysis
- Alert system for significant signal changes
- Integration with actual DEX APIs for real-time liquidity data
- Authentication and rate limiting
- Database for storing analysis history

## License

This project is provided as-is for educational and research purposes.
