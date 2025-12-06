# Frontend Deactivation Guide

## 🎯 Deactivate Agent from Frontend

### JavaScript/TypeScript

```javascript
const deactivateAgent = async (token, stablecoin, portfolioAmount) => {
  try {
    const response = await fetch('http://localhost:8001/api/deactivate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: token,
        stablecoin: stablecoin,
        portfolio_amount: portfolioAmount
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('✅ Agent deactivated:', data);
      return data;
    } else {
      console.error('❌ Failed to deactivate:', data);
      throw new Error(data.detail || 'Failed to deactivate agent');
    }
  } catch (error) {
    console.error('Error deactivating agent:', error);
    throw error;
  }
};

// Usage
deactivateAgent('APT', 'USDC', 100.0);
```

### React Example

```javascript
import { useState } from 'react';

function TradingAgent() {
  const [isActive, setIsActive] = useState(false);
  const [agentConfig, setAgentConfig] = useState({
    token: 'APT',
    stablecoin: 'USDC',
    portfolio_amount: 100.0,
    risk_level: 'aggressive'
  });

  const deactivateAgent = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/deactivate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: agentConfig.token,
          stablecoin: agentConfig.stablecoin,
          portfolio_amount: agentConfig.portfolio_amount
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setIsActive(false);
        // Stop polling if you have a polling interval
        if (pollingInterval) {
          clearInterval(pollingInterval);
        }
        alert('Agent deactivated successfully');
      }
    } catch (error) {
      console.error('Error deactivating:', error);
      alert('Failed to deactivate agent');
    }
  };

  return (
    <div>
      {isActive ? (
        <button onClick={deactivateAgent}>
          Deactivate Agent
        </button>
      ) : (
        <button onClick={activateAgent}>
          Activate Agent
        </button>
      )}
    </div>
  );
}
```

### React Hook with Deactivation

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
    // Stop polling first
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    try {
      const response = await fetch('http://localhost:8001/api/deactivate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          stablecoin,
          portfolio_amount: portfolioAmount
        })
      });
      
      const result = await response.json();
      setIsActive(false);
      setData(null); // Clear data
      return result;
    } catch (error) {
      console.error('Error deactivating:', error);
      throw error;
    }
  };
  
  // Polling effect
  useEffect(() => {
    if (!isActive) return;
    
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
    
    poll();
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
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

### Axios Example

```javascript
import axios from 'axios';

const deactivateAgent = async (token, stablecoin, portfolioAmount) => {
  try {
    const response = await axios.post('http://localhost:8001/api/deactivate', {
      token,
      stablecoin,
      portfolio_amount: portfolioAmount
    });
    
    return response.data;
  } catch (error) {
    console.error('Error deactivating agent:', error);
    throw error;
  }
};

// Usage
await deactivateAgent('APT', 'USDC', 100.0);
```

### Complete Frontend Example

```javascript
class PerpAgentController {
  constructor(config) {
    this.token = config.token;
    this.stablecoin = config.stablecoin;
    this.portfolioAmount = config.portfolioAmount;
    this.riskLevel = config.riskLevel;
    this.isActive = false;
    this.pollingInterval = null;
  }
  
  async activate() {
    const response = await fetch('http://localhost:8001/api/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: this.token,
        stablecoin: this.stablecoin,
        portfolio_amount: this.portfolioAmount,
        risk_level: this.riskLevel
      })
    });
    
    const data = await response.json();
    this.isActive = true;
    this.startPolling();
    return data;
  }
  
  async deactivate() {
    // Stop polling
    this.stopPolling();
    
    // Call deactivate API
    const response = await fetch('http://localhost:8001/api/deactivate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: this.token,
        stablecoin: this.stablecoin,
        portfolio_amount: this.portfolioAmount
      })
    });
    
    const data = await response.json();
    this.isActive = false;
    return data;
  }
  
  startPolling(callback) {
    this.pollingInterval = setInterval(async () => {
      const response = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: this.token,
          stablecoin: this.stablecoin,
          portfolio_amount: this.portfolioAmount,
          risk_level: this.riskLevel
        })
      });
      const data = await response.json();
      if (callback) callback(data);
    }, 1000);
  }
  
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }
}

// Usage
const agent = new PerpAgentController({
  token: 'APT',
  stablecoin: 'USDC',
  portfolioAmount: 100.0,
  riskLevel: 'aggressive'
});

// Activate
await agent.activate();

// Deactivate
await agent.deactivate();
```

## 📡 API Endpoint

**POST** `/api/deactivate`

**Request Body:**
```json
{
  "token": "APT",
  "stablecoin": "USDC",
  "portfolio_amount": 100.0
}
```

**Response:**
```json
{
  "status": "deactivated",
  "message": "Agent deactivated for APT trading",
  "session_id": "APT_USDC_100.0",
  "deactivated_at": "2025-11-30T10:35:00"
}
```

## ✅ Best Practices

1. **Stop polling first** - Clear your polling interval before deactivating
2. **Handle errors** - Wrap in try/catch
3. **Update UI** - Set `isActive` to false after successful deactivation
4. **Clear data** - Reset your state/data after deactivation

## 🔄 Complete Flow

```javascript
// 1. Activate
const activate = async () => {
  await fetch('/api/activate', {
    method: 'POST',
    body: JSON.stringify({token: 'APT', stablecoin: 'USDC', portfolio_amount: 100.0, risk_level: 'aggressive'})
  });
  startPolling();
};

// 2. Poll (every 1 second)
const startPolling = () => {
  const interval = setInterval(async () => {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({token: 'APT', stablecoin: 'USDC', portfolio_amount: 100.0, risk_level: 'aggressive'})
    });
    const data = await response.json();
    updateUI(data);
  }, 1000);
  
  // Store interval ID
  window.pollingInterval = interval;
};

// 3. Deactivate
const deactivate = async () => {
  // Stop polling
  if (window.pollingInterval) {
    clearInterval(window.pollingInterval);
  }
  
  // Call deactivate API
  await fetch('/api/deactivate', {
    method: 'POST',
    body: JSON.stringify({token: 'APT', stablecoin: 'USDC', portfolio_amount: 100.0})
  });
  
  // Update UI
  setIsActive(false);
};
```

