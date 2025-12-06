#!/bin/bash

# Test API Endpoints for Sentenex Backend
# Make sure your FastAPI server is running on localhost:8001

BASE_URL="http://localhost:8001"
TOKEN="APT"
STABLECOIN="USDC"
AMOUNT=100.0
RISK="moderate"

echo "=========================================="
echo "Testing Sentenex API Endpoints"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Testing Health Check..."
echo "curl -X GET $BASE_URL/api/health"
curl -X GET "$BASE_URL/api/health" | jq .
echo ""
echo "Press Enter to continue..."
read

# 2. Root Endpoint
echo "2. Testing Root Endpoint..."
echo "curl -X GET $BASE_URL/"
curl -X GET "$BASE_URL/" | jq .
echo ""
echo "Press Enter to continue..."
read

# 3. One-time Analysis (without activating agent)
echo "3. Testing One-time Analysis (agent NOT activated)..."
echo "curl -X POST $BASE_URL/api/analyze -H 'Content-Type: application/json' -d '{...}'"
curl -X POST "$BASE_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"stablecoin\": \"$STABLECOIN\",
    \"portfolio_amount\": $AMOUNT,
    \"risk_level\": \"$RISK\"
  }" | jq .
echo ""
echo "Press Enter to continue..."
read

# 4. Activate Agent
echo "4. Activating Agent..."
echo "curl -X POST $BASE_URL/api/activate -H 'Content-Type: application/json' -d '{...}'"
curl -X POST "$BASE_URL/api/activate" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"stablecoin\": \"$STABLECOIN\",
    \"portfolio_amount\": $AMOUNT,
    \"risk_level\": \"$RISK\"
  }" | jq .
echo ""
echo "Waiting 3 seconds for agent to start..."
sleep 3
echo "Press Enter to continue..."
read

# 5. Poll Analysis (get results from activated agent)
echo "5. Polling Analysis (agent activated - should return cached result)..."
echo "curl -X POST $BASE_URL/api/analyze -H 'Content-Type: application/json' -d '{...}'"
curl -X POST "$BASE_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"stablecoin\": \"$STABLECOIN\",
    \"portfolio_amount\": $AMOUNT,
    \"risk_level\": \"$RISK\"
  }" | jq .
echo ""
echo "Press Enter to continue..."
read

# 6. Check Status
echo "6. Checking Agent Status..."
echo "curl -X GET $BASE_URL/api/status/$TOKEN/$STABLECOIN/$AMOUNT"
curl -X GET "$BASE_URL/api/status/$TOKEN/$STABLECOIN/$AMOUNT" | jq .
echo ""
echo "Press Enter to continue..."
read

# 7. Poll Again (should see updated data)
echo "7. Polling Again (should see updated timestamp)..."
curl -X POST "$BASE_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"stablecoin\": \"$STABLECOIN\",
    \"portfolio_amount\": $AMOUNT,
    \"risk_level\": \"$RISK\"
  }" | jq '.timestamp, .iteration, .market_data.price, .recommendation, .confidence'
echo ""
echo "Press Enter to continue..."
read

# 8. Get Historical Data
echo "8. Getting Historical Data..."
echo "curl -X GET $BASE_URL/api/historical/$TOKEN?days=7"
curl -X GET "$BASE_URL/api/historical/$TOKEN?days=7" | jq '.count, .data[0:3]'
echo ""
echo "Press Enter to continue..."
read

# 9. Deactivate Agent
echo "9. Deactivating Agent..."
echo "curl -X POST $BASE_URL/api/deactivate -H 'Content-Type: application/json' -d '{...}'"
curl -X POST "$BASE_URL/api/deactivate" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"stablecoin\": \"$STABLECOIN\",
    \"portfolio_amount\": $AMOUNT
  }" | jq .
echo ""
echo "=========================================="
echo "Testing Complete!"
echo "=========================================="

