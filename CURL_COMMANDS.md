# API Testing Curl Commands

Test the VERDICT backend API endpoints one at a time. Make sure your FastAPI server is running on `localhost:8001`.

## Base URL
```bash
BASE_URL="http://localhost:8001"
```

## 1. Health Check
```bash
curl -X GET http://localhost:8001/api/health
```

## 2. Root Endpoint (API Info)
```bash
curl -X GET http://localhost:8001/
```

## 3. One-time Analysis (Agent NOT Activated)
This performs a single analysis without activating the background agent.

```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0,
    "risk_level": "moderate"
  }'
```

**Expected**: Returns analysis result immediately. Check for:
- `market_data.price` - should be current price
- `recommendation` - LONG/SHORT/HOLD
- `timestamp` - current timestamp

## 4. Activate Agent
Starts the background loop that analyzes every 1 second.

```bash
curl -X POST http://localhost:8001/api/activate \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0,
    "risk_level": "moderate"
  }'
```

**Expected**: Returns `{"status": "activated", ...}`

**Check backend logs** - You should see:
```
[Agent Loop] Iteration #1 - Fetching fresh data at ...
[CMC API] Making fresh API call for APT at ...
[OpenAI API] Making sentiment analysis call for APT at ...
```

## 5. Poll Analysis (Agent Activated)
After activating, poll this endpoint to get the latest cached results.

```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0,
    "risk_level": "moderate"
  }'
```

**Expected**: Returns cached result from background loop. Check:
- `timestamp` - should update every second
- `iteration` - should increment
- `market_data.price` - should reflect latest CMC API data
- `recommendation` - should reflect latest analysis

**Test multiple times** (run this command 3-5 times with 1-2 second intervals):
```bash
# First call
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0, "risk_level": "moderate"}' | jq '.timestamp, .iteration, .market_data.price'

sleep 2

# Second call - timestamp and iteration should change
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0, "risk_level": "moderate"}' | jq '.timestamp, .iteration, .market_data.price'
```

## 6. Check Agent Status
```bash
curl -X GET "http://localhost:8001/api/status/APT/USDC/100.0"
```

**Expected**: Returns agent status (activated/deactivated)

## 7. Get Historical Data
```bash
curl -X GET "http://localhost:8001/api/historical/APT?days=7"
```

**Expected**: Returns historical OHLC data for the token

## 8. Deactivate Agent
```bash
curl -X POST http://localhost:8001/api/deactivate \
  -H "Content-Type: application/json" \
  -d '{
    "token": "APT",
    "stablecoin": "USDC",
    "portfolio_amount": 100.0
  }'
```

**Expected**: Returns `{"status": "deactivated", ...}`

**Check backend logs** - You should see:
```
Agent APT_USDC_100.0 deactivated, stopping loop
```

---

## Quick Test Sequence

Run these commands in order to test the full flow:

```bash
# 1. Health check
curl -X GET http://localhost:8001/api/health

# 2. Activate agent
curl -X POST http://localhost:8001/api/activate \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0, "risk_level": "moderate"}'

# 3. Wait 3 seconds for first analysis
sleep 3

# 4. Poll multiple times (should see different timestamps/iterations)
for i in {1..5}; do
  echo "Poll #$i:"
  curl -s -X POST http://localhost:8001/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0, "risk_level": "moderate"}' \
    | jq '{timestamp, iteration, price: .market_data.price, recommendation, confidence}'
  sleep 2
done

# 5. Deactivate
curl -X POST http://localhost:8001/api/deactivate \
  -H "Content-Type: application/json" \
  -d '{"token": "APT", "stablecoin": "USDC", "portfolio_amount": 100.0}'
```

## What to Check

1. **Backend Console Logs**: Should show API calls every second:
   - `[CMC API] Making fresh API call...`
   - `[OpenAI API] Making sentiment analysis call...`
   - `[Agent Loop] Iteration #X...`

2. **Response Data**: Each poll should return:
   - Different `timestamp` (even if price is same)
   - Incrementing `iteration` number
   - Fresh `market_data` from CMC API
   - Updated `sentiment_data` from OpenAI API

3. **If data is "fixed"**:
   - Check backend logs - are APIs being called?
   - Check if CMC API is returning same price (normal if market hasn't moved)
   - Check if OpenAI is being called (might be slow/expensive)
   - The `timestamp` and `iteration` should still change every second

