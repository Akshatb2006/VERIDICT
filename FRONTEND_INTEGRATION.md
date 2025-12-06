# Frontend Integration Guide - Polling System

## 🎯 Simple Polling-Based System

No WebSocket needed! Just use standard HTTP requests.

## 📡 Complete Workflow

### 1. Activate Agent

```javascript
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
  console.log('Agent activated:', data);
  return data;
};
```

### 2. Poll for Updates (Frontend Loop)

```javascript
let pollingInterval;

const startPolling = () => {
  pollingInterval = setInterval(async () => {
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
    
    // Update your UI with the data
    updateUI(data);
  }, 1000); // Poll every 1 second
};

const updateUI = (data) => {
  // Example: Update recommendation display
  document.getElementById('recommendation').textContent = data.recommendation;
  document.getElementById('confidence').textContent = `${data.confidence}%`;
  document.getElementById('signal-score').textContent = data.signal_score;
  
  // Check execution signals
  if (data.execution_signal?.should_open) {
    showNotification(`Position opened: ${data.execution_signal.action}`);
  }
  
  if (data.execution_signal?.should_close) {
    showNotification(`Position closed: ${data.execution_signal.exit_conditions.join(', ')}`);
  }
  
  // Show position info
  if (data.position_info?.status === 'open') {
    updatePositionDisplay(data.position_info);
  }
};
```

### 3. Deactivate Agent

```javascript
const deactivateAgent = async () => {
  // Stop polling
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
  
  const response = await fetch('http://localhost:8001/api/deactivate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token: 'APT',
      stablecoin: 'USDC',
      portfolio_amount: 100.0
    })
  });
  const data = await response.json();
  console.log('Agent deactivated:', data);
};
```

## 🔄 React Hook Example

```javascript
import { useState, useEffect, useRef } from 'react';

function usePerpAgent(token, stablecoin, portfolioAmount, riskLevel) {
  const [data, setData] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const intervalRef = useRef(null);
  
  const activate = async () => {
    const response = await fetch('http://localhost:8001/api/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token,
        stablecoin,
        portfolio_amount: portfolioAmount,
        risk_level: riskLevel
      })
    });
    const result = await response.json();
    setIsActive(true);
    return result;
  };
  
  const deactivate = async () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    await fetch('http://localhost:8001/api/deactivate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token,
        stablecoin,
        portfolio_amount: portfolioAmount
      })
    });
    setIsActive(false);
  };
  
  useEffect(() => {
    if (!isActive) return;
    
    // Poll immediately
    const poll = async () => {
      const response = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          stablecoin,
          portfolio_amount: portfolioAmount,
          risk_level: riskLevel
        })
      });
      const result = await response.json();
      setData(result);
    };
    
    poll(); // First poll
    
    // Then poll every second
    intervalRef.current = setInterval(poll, 1000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isActive, token, stablecoin, portfolioAmount, riskLevel]);
  
  return { data, isActive, activate, deactivate };
}

// Usage in component
function TradingDashboard() {
  const { data, isActive, activate, deactivate } = usePerpAgent('APT', 'USDC', 100.0, 'aggressive');
  
  return (
    <div>
      {!isActive ? (
        <button onClick={activate}>Activate Agent</button>
      ) : (
        <>
          <button onClick={deactivate}>Deactivate Agent</button>
          {data && (
            <div>
              <h2>Recommendation: {data.recommendation}</h2>
              <p>Confidence: {data.confidence}%</p>
              <p>Signal Score: {data.signal_score}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

## 📊 Response Data Structure

The response is the same format as before:

```json
{
  "token": "APT",
  "stablecoin": "USDC",
  "portfolio_amount": 100.0,
  "risk_level": "aggressive",
  "recommendation": "LONG",
  "confidence": 78.5,
  "signal_score": 35.67,
  "execution_signal": {
    "action": "OPENED_LONG",
    "should_open": true
  },
  "position_info": {
    "status": "open",
    "type": "LONG",
    "pnl_usd": 5.25,
    "pnl_pct": 5.25
  },
  "perp_trade_details": {...},
  "market_data": {...}
}
```

## ✅ Benefits

- ✅ **Simple**: Standard HTTP requests
- ✅ **No WebSocket**: Works everywhere
- ✅ **Easy to debug**: Just check network tab
- ✅ **Reliable**: Standard REST API
- ✅ **Same data format**: No changes needed

## 🧪 Test It

```bash
# Test the polling system
python test_polling.py
```

This simulates what your frontend will do!

