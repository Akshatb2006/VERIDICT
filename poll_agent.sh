#!/bin/bash

# Continuous polling script - keeps hitting /api/analyze every second
# Usage: ./poll_agent.sh [TOKEN] [STABLECOIN] [AMOUNT] [RISK]

TOKEN=${1:-APT}
STABLECOIN=${2:-USDC}
AMOUNT=${3:-100.0}
RISK=${4:-aggressive}

echo "🚀 Starting Agent Polling"
echo "Token: $TOKEN | Collateral: $AMOUNT $STABLECOIN | Risk: $RISK"
echo ""

# Step 1: Activate agent
echo "1️⃣ Activating agent..."
ACTIVATE_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/activate" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"stablecoin\": \"$STABLECOIN\",
    \"portfolio_amount\": $AMOUNT,
    \"risk_level\": \"$RISK\"
  }")

echo "$ACTIVATE_RESPONSE" | python3 -m json.tool
echo ""

# Step 2: Start polling loop
echo "2️⃣ Starting polling loop (every 1 second)..."
echo "Press Ctrl+C to stop"
echo ""

count=0

while true; do
  count=$((count + 1))
  timestamp=$(date '+%H:%M:%S')
  
  # Poll the API
  RESPONSE=$(curl -s -X POST "http://localhost:8001/api/analyze" \
    -H "Content-Type: application/json" \
    -d "{
      \"token\": \"$TOKEN\",
      \"stablecoin\": \"$STABLECOIN\",
      \"portfolio_amount\": $AMOUNT,
      \"risk_level\": \"$RISK\"
    }")
  
  # Extract key info
  REC=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('recommendation', 'UNKNOWN'))" 2>/dev/null)
  SCORE=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d.get('signal_score', 0):+.2f}\")" 2>/dev/null)
  CONF=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('confidence', 0))" 2>/dev/null)
  PRICE=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"\${d.get('market_data', {}).get('price', 0):,.4f}\")" 2>/dev/null)
  
  # Execution signals
  EXEC_ACTION=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('execution_signal', {}).get('action', ''))" 2>/dev/null)
  SHOULD_OPEN=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('execution_signal', {}).get('should_open', False))" 2>/dev/null)
  SHOULD_CLOSE=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('execution_signal', {}).get('should_close', False))" 2>/dev/null)
  
  # Position info
  POS_STATUS=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('position_info', {}).get('status', 'none'))" 2>/dev/null)
  PNL_USD=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('position_info', {}).get('pnl_usd', 0))" 2>/dev/null)
  PNL_PCT=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('position_info', {}).get('pnl_pct', 0))" 2>/dev/null)
  
  # Clear line and display
  echo -ne "\r\033[K"
  
  # Color-coded display
  if [ "$REC" = "LONG" ]; then
    echo -ne "⏰ $timestamp | 🟢 $REC | Score: $SCORE | Conf: ${CONF}% | Price: $PRICE"
  elif [ "$REC" = "SHORT" ]; then
    echo -ne "⏰ $timestamp | 🔴 $REC | Score: $SCORE | Conf: ${CONF}% | Price: $PRICE"
  else
    echo -ne "⏰ $timestamp | 🟡 $REC | Score: $SCORE | Conf: ${CONF}% | Price: $PRICE"
  fi
  
  # Show execution signals
  if [ "$SHOULD_OPEN" = "True" ]; then
    echo -ne " | ⚡ EXEC: $EXEC_ACTION"
  fi
  
  if [ "$SHOULD_CLOSE" = "True" ]; then
    echo -ne " | 🔴 CLOSING"
  fi
  
  # Show position if open
  if [ "$POS_STATUS" = "open" ]; then
    echo -ne " | 📊 PnL: \$${PNL_USD} (${PNL_PCT}%)"
  fi
  
  # Wait 1 second
  sleep 1
done

