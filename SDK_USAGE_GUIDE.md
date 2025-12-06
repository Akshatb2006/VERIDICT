# VERDICT SDK & API - Usage Guide

Complete guide for using VERDICT with your own API keys (BYOK model).

## 🚀 Quick Start

### Step 1: Get Your API Keys

You need two API keys:

1. **CoinMarketCap API Key**
   - Go to: https://coinmarketcap.com/api/
   - Sign up for a free account
   - Get your API key from the dashboard
   - Free tier: 333 calls/day (good for testing)

2. **Google Gemini API Key**
   - Go to: https://aistudio.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key
   - Free tier: 60 requests/minute

### Step 2: Install the SDK

```bash
cd sdk-python
pip install -e .
```

Or install from PyPI (once published):
```bash
pip install verdict-sdk
```

### Step 3: Use the SDK

Create a file `my_analysis.py`:

```python
import asyncio
from verdict_sdk import VerdictClient

async def main():
    client = VerdictClient(
        api_url="http://localhost:8000",  # or your deployed API URL
        cmc_api_key="YOUR_CMC_API_KEY_HERE",
        gemini_api_key="YOUR_GEMINI_API_KEY_HERE"
    )
    
    result = await client.analyze("BTC", portfolio_amount=1000)
    print(f"{result.recommendation} - Confidence: {result.confidence}%")
    
    await client.close()

asyncio.run(main())
```

Run it:
```bash
python my_analysis.py
```

---

## 📖 Direct API Usage (Without SDK)

If you prefer to use the API directly with curl or any HTTP client:

### Single Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "token": "BTC",
    "stablecoin": "USDC",
    "portfolio_amount": 1000,
    "risk_level": "moderate",
    "cmc_api_key": "YOUR_CMC_API_KEY",
    "gemini_api_key": "YOUR_GEMINI_API_KEY"
  }'
```

### JavaScript/Fetch Example

```javascript
const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    token: 'ETH',
    stablecoin: 'USDC',
    portfolio_amount: 500,
    risk_level: 'moderate',
    cmc_api_key: 'YOUR_CMC_API_KEY',
    gemini_api_key: 'YOUR_GEMINI_API_KEY'
  })
});

const data = await response.json();
console.log(`${data.recommendation} - ${data.confidence}%`);
```

### Python Requests Example

```python
import requests

response =requests.post('http://localhost:8000/api/analyze', json={
    'token': 'APT',
    'stablecoin': 'USDC',
    'portfolio_amount': 100,
    'risk_level': 'conservative',
    'cmc_api_key': 'YOUR_CMC_API_KEY',
    'gemini_api_key': 'YOUR_GEMINI_API_KEY'
})

data = response.json()
print(f"{data['recommendation']} - {data['confidence']}%")
```

---

## 🔄 Real-Time Polling

For real-time updates, poll the `/api/analyze` endpoint repeatedly:

```python
import time
import requests

while True:
    response = requests.post('http://localhost:8000/api/analyze', json={
        'token': 'BTC',
        'portfolio_amount': 1000,
        'cmc_api_key': 'YOUR_CMC_API_KEY',
        'gemini_api_key': 'YOUR_GEMINI_API_KEY'
    })
    
    data = response.json()
    print(f"Price: ${data['market_data']['price']:,.2f} | {data['recommendation']}")
    
    time.sleep(2)  # Poll every 2 seconds
```

---

## 🌐 Deploying the API

### Option 1: Render (Easiest - Free Tier)

1. Push your code to GitHub
2. Go to https://render.com
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Add Environment Variables (optional - leave empty for BYOK):
     - `CMC_API_KEY` (optional)
     - `GEMINI_API_KEY` (optional)
6. Deploy!

Your API will be available at: `https://your-app.onrender.com`

### Option 2: Railway

1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`

### Option 3: Docker (Any Platform)

```dockerfile
# Dockerfile already created in the project
docker build -t verdict-api .
docker run -p 8000:8000 verdict-api
```

Deploy to:
- **Fly.io**: `fly deploy`
- **DigitalOcean**: Use App Platform or Droplet
- **AWS**: ECS, Lambda, or EC2

### Option 4: Vercel/Netlify (Serverless)

For serverless deployment, you'll need to adapt the app to use serverless functions.

---

## 📊 SDK Examples

### 1. Basic Analysis

```python
from verdict_sdk import VerdictClient
import asyncio

async def analyze_token(token: str):
    client = VerdictClient(
        api_url="http://localhost:8000",
        cmc_api_key="YOUR_CMC_KEY",
        gemini_api_key="YOUR_GEMINI_KEY"
    )
    
    result = await client.analyze(token, portfolio_amount=1000)
    
    print(f"\n{'='*60}")
    print(f"Token: {result.token}")
    print(f"Price: ${result.market_data.price:,.2f}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Confidence: {result.confidence}%")
    print(f"Verified: {'✅' if result.verified else '❌'}")
    print(f"{'='*60}\n")
    
    await client.close()

# Run
asyncio.run(analyze_token("BTC"))
```

### 2. Compare Multiple Tokens

```python
async def compare_tokens():
    client = VerdictClient(
        api_url="http://localhost:8000",
        cmc_api_key="YOUR_CMC_KEY",
        gemini_api_key="YOUR_GEMINI_KEY"
    )
    
    tokens = ["BTC", "ETH", "APT", "SOL"]
    
    print("\n📊 Token Comparison\n")
    
    for token in tokens:
        result = await client.analyze(token, portfolio_amount=1000)
        print(f"{token:6} | ${result.market_data.price:>10,.2f} | "
              f"{result.recommendation:5} | {result.confidence:5.1f}%")
    
    await client.close()

asyncio.run(compare_tokens())
```

### 3. Real-Time Monitoring

```python
async def monitor_token(token: str):
    client = VerdictClient(
        api_url="http://localhost:8000",
        cmc_api_key="YOUR_CMC_KEY",
        gemini_api_key="YOUR_GEMINI_KEY"
    )
    
    print(f"🔍 Monitoring {token}...\n")
    
    async for analysis in client.stream_agent(
        token=token,
        portfolio_amount=1000,
        interval=2.0  # Update every 2 seconds
    ):
        print(f"[{analysis.timestamp}] "
              f"${analysis.market_data.price:,.2f} | "
              f"{analysis.recommendation} ({analysis.confidence:.1f}%)")

asyncio.run(monitor_token("BTC"))
```

---

## 🔐 API Key Management Best Practices

### Use Environment Variables

Never hardcode API keys! Use environment variables:

```python
import os
from verdict_sdk import VerdictClient

client = VerdictClient(
    api_url=os.getenv("VERDICT_API_URL", "http://localhost:8000"),
    cmc_api_key=os.getenv("CMC_API_KEY"),
    gemini_api_key=os.getenv("GEMINI_API_KEY")
)
```

Create a `.env` file:
```
CMC_API_KEY=your_cmc_key_here
GEMINI_API_KEY=your_gemini_key_here
VERDICT_API_URL=http://localhost:8000
```

Load with `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Rate Limits

**CoinMarketCap (Free Tier):**
- 333 calls/day
- ~14 calls/hour
- Poll every 4+ minutes to stay safe

**Google Gemini (Free Tier):**
- 60 requests/minute
- 1500 requests/day

---

## 📝 Response Structure

Every analysis returns comprehensive data:

```json
{
  "token": "BTC",
  "recommendation": "LONG",
  "confidence": 78.5,
  "market_data": {
    "price": 45000.50,
    "percent_change_24h": 2.45,
    "volume_24h": 25000000000
  },
  "sentiment_data": {
    "overall_sentiment": 0.65,
    "risk_level": "Medium",
    "key_factors": ["Strong momentum", "Institutional interest"]
  },
  "leverage_suggestion": {
    "suggested_leverage": 10,
    "max_safe_leverage": 20
  },
  "perp_trade_details": {
    "position_size_usd": 10000,
    "if_price_moves_5pct_up": {
      "pnl": 500,
      "roi_pct": 50
    }
  },
  "verified": true,
  "ftso_price": 45001.20
}
```

---

## 🆘 Troubleshooting

### "Token not found"
- Check token symbol is correct
- Verify CMC API key is valid
- Ensure API key has quote endpoint access

### "Authentication failed"
- Double-check your API keys
- Ensure no extra spaces in keys
- Verify keys are not expired

### "Rate limit exceeded"
- CMC free tier: max 333 calls/day
- Wait before making more requests
- Consider upgrading CMC plan

### Connection errors
- Check if API is running (`python app.py`)
- Verify API URL is correct
- Check firewall/network settings

---

## 📚 More Examples

Check the `examples/` directory for:
- `basic_analysis.py` - Simple one-time analysis
- `real_time_stream.py` - Live price monitoring
- `trading_bot.py` - Automated trading bot

---

## 🤝 Support

- Issues: https://github.com/yourusername/verdict/issues
- Documentation: See README.md files
- Discord: Coming soon!
