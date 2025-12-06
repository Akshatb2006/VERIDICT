#!/bin/bash

# Continuous Analysis Checker using curl (simulates WebSocket by polling)
# Usage: ./continuous_check.sh [TOKEN] [AMOUNT] [INTERVAL]

TOKEN=${1:-APT}
AMOUNT=${2:-100.0}
INTERVAL=${3:-1}  # seconds between checks

echo "🚀 Starting Continuous Analysis Checker"
echo "Token: $TOKEN | Amount: $AMOUNT | Interval: ${INTERVAL}s"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    # Get current timestamp
    TIMESTAMP=$(date '+%H:%M:%S')
    
    # Make API call
    RESPONSE=$(curl -s -X POST "http://localhost:8001/api/analyze" \
        -H "Content-Type: application/json" \
        -d "{\"token\": \"$TOKEN\", \"amount\": $AMOUNT}")
    
    # Extract key information
    RECOMMENDATION=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('recommendation', 'UNKNOWN'))" 2>/dev/null)
    CONFIDENCE=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('confidence', 0))" 2>/dev/null)
    SCORE=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d.get('signal_score', 0):.2f}\")" 2>/dev/null)
    PRICE=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"\${d.get('market_data', {}).get('price', 0):.4f}\")" 2>/dev/null)
    ACTION_MSG=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('action_message', ''))" 2>/dev/null)
    
    # Clear line and display
    echo -ne "\r\033[K"
    
    # Color-coded display
    if [ "$RECOMMENDATION" = "LONG" ]; then
        echo -e "⏰ $TIMESTAMP | 🟢 $RECOMMENDATION | Confidence: ${CONFIDENCE}% | Score: $SCORE | Price: $PRICE"
    elif [ "$RECOMMENDATION" = "SHORT" ]; then
        echo -e "⏰ $TIMESTAMP | 🔴 $RECOMMENDATION | Confidence: ${CONFIDENCE}% | Score: $SCORE | Price: $PRICE"
    else
        echo -e "⏰ $TIMESTAMP | 🟡 $RECOMMENDATION | Confidence: ${CONFIDENCE}% | Score: $SCORE | Price: $PRICE"
    fi
    
    # Wait before next check
    sleep $INTERVAL
done

