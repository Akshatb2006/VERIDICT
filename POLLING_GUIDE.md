# Polling-Based Agent System Guide

## 🎯 How It Works

Instead of WebSocket, the system now uses **polling**:
1. **Activate** agent → Starts background loop
2. **Poll** `/api/analyze` → Get latest results
3. **Deactivate** agent → Stops background loop

## 📡 Complete Workflow

### 1. Activate the Agent

```bash
curl -X POST "http://localhost:8001/api/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0,
    "risk_level": "aggressive"
  }'
```

**Response:**
```json
{
  "status": "activated",
  "message": "Agent activated for APT trading. Start polling /api/analyze",
  "session_id": "APT_USDC_100.0",
  "token": "APT",
  "stablecoin": "USDC",
  "portfolio_amount": 100.0,
  "risk_level": "aggressive",
  "activated_at": "2025-11-30T10:30:00",
  "polling_endpoint": "/api/analyze"
}
```

### 2. Poll for Updates (Frontend Loop)

Poll this endpoint every 1 second (or your preferred interval):

```bash
# Keep polling this endpoint
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0,
    "risk_level": "aggressive"
  }'
```

**Response:** Same format as before - you get the latest analysis result.

### 3. Deactivate the Agent

```bash
curl -X POST "http://localhost:8001/api/deactivate" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0
  }'
```

## 💻 Frontend Implementation Example

### JavaScript/React

```javascript
// State
const [agentActive, setAgentActive] = useState(false);
const [analysisData, setAnalysisData] = useState(null);

// Activate agent
const activateAgent = async () => {
  const response = await fetch('http://localhost:8001/api/activate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token: 'APT',
      stablecoin: 'USDC',
      portfolio_amount: 100.0,
      risk_level: 'aggressive'
    })
  });
  const data = await response.json();
  setAgentActive(true);
  startPolling();
};

// Polling function
const startPolling = () => {
  const pollInterval = setInterval(async () => {
    if (!agentActive) {
      clearInterval(pollInterval);
      return;
    }
    
    const response = await fetch('http://localhost:8001/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: 'APT',
        stablecoin: 'USDC',
        portfolio_amount: 100.0,
        risk_level: 'aggressive'
      })
    });
    const data = await response.json();
    setAnalysisData(data);
  }, 1000); // Poll every 1 second
};

// Deactivate agent
const deactivateAgent = async () => {
  await fetch('http://localhost:8001/api/deactivate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token: 'APT',
      stablecoin: 'USDC',
      portfolio_amount: 100.0
    })
  });
  setAgentActive(false);
};
```

### Python Example

```python
import requests
import time

# Activate
response = requests.post('http://localhost:8001/api/activate', json={
    'token': 'APT',
    'stablecoin': 'USDC',
    'portfolio_amount': 100.0,
    'risk_level': 'aggressive'
})
print("Activated:", response.json())

# Poll loop
while True:
    response = requests.post('http://localhost:8001/api/analyze', json={
        'token': 'APT',
        'stablecoin': 'USDC',
        'portfolio_amount': 100.0,
        'risk_level': 'aggressive'
    })
    data = response.json()
    print(f"Recommendation: {data.get('recommendation')} | Score: {data.get('signal_score')}")
    time.sleep(1)  # Poll every 1 second
```

## 🔄 How It Works

1. **Activation**: Starts a background task that analyzes every 1 second
2. **Polling**: Frontend polls `/api/analyze` → Returns latest cached result
3. **Deactivation**: Stops background task, polling returns one-time analysis

## 📊 Response Format

The response format is **exactly the same** as before:

```json
{
  "token": "APT",
  "stablecoin": "USDC",
  "portfolio_amount": 100.0,
  "risk_level": "aggressive",
  "recommendation": "LONG",
  "confidence": 78.5,
  "signal_score": 35.67,
  "execution_signal": {...},
  "position_info": {...},
  "perp_trade_details": {...}
}
```

## ✅ Benefits

- ✅ **Simple**: No WebSocket complexity
- ✅ **Easy Frontend**: Just use fetch/axios
- ✅ **Same Data Format**: No changes needed
- ✅ **Reliable**: Standard HTTP polling
- ✅ **Works Everywhere**: Browser, mobile, etc.

## 🎯 Quick Test

```bash
# 1. Activate
curl -X POST "http://localhost:8001/api/activate" \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0, "risk_level": "aggressive"}'

# 2. Poll (run multiple times)
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0, "risk_level": "aggressive"}'

# 3. Deactivate
curl -X POST "http://localhost:8001/api/deactivate" \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0}'
```

Perfect for frontend integration! 🚀

