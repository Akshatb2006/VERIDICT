# How to Generate LONG/SHORT Signals

## 🔧 What I Fixed

I've made the system **more sensitive** to generate LONG/SHORT signals:

1. **Lowered thresholds**: 
   - LONG: Score > 15 (was 25)
   - SHORT: Score < -15 (was -25)

2. **More sensitive market momentum**: Price changes are amplified by 1.5x

3. **Lowered execution requirements**:
   - Confidence: ≥ 60% (was 70%)
   - Signal Score: ≥ 15 (was 25)

## 🧪 Test Scenarios

### Quick Test Script
```bash
# Test a specific token
python test_scenarios.py BTC 1000.0 aggressive

# Test multiple tokens to find signals
python test_scenarios.py multi
```

### Manual Testing

#### Bitcoin (High volatility - more likely to get signals)
```bash
python websocket_client.py BTC USDC 1000.0 aggressive
```

#### Ethereum (Also high volatility)
```bash
python websocket_client.py ETH USDC 500.0 aggressive
```

#### Solana (Volatile altcoin)
```bash
python websocket_client.py SOL USDC 200.0 aggressive
```

## 📊 What Triggers LONG/SHORT

### LONG Signal Triggers When:
- **Price is rising** (24h change > 2-3%)
- **Strong positive sentiment** from AI
- **High volume** activity
- **Combined score > 15**

### SHORT Signal Triggers When:
- **Price is falling** (24h change < -2-3%)
- **Strong negative sentiment** from AI
- **High volume** activity
- **Combined score < -15**

## 🎯 Best Tokens for Testing

Tokens with **high volatility** are more likely to generate signals:

1. **BTC** - Bitcoin (most liquid, good signals)
2. **ETH** - Ethereum (high volume)
3. **SOL** - Solana (volatile)
4. **BNB** - Binance Coin
5. **XRP** - Ripple (often volatile)

## 💡 Tips to Get Signals

1. **Use aggressive risk level**: Higher leverage = more sensitivity
2. **Test during market hours**: More volatility = more signals
3. **Try volatile tokens**: BTC, ETH, SOL are good choices
4. **Wait a few seconds**: Market conditions change, signals appear

## 🔍 Check Current Market Conditions

The system analyzes:
- **24h price change**: If > 3% up = likely LONG, < -3% down = likely SHORT
- **1h price change**: Recent momentum
- **Volume**: High volume = stronger signals
- **AI Sentiment**: Analyzes market conditions

## 📈 Example: Getting a LONG Signal

If BTC is up 5% in 24h:
- Market momentum: +5% × 1.5 = +7.5 points
- If sentiment is positive: +10-20 points
- Combined score: ~20-30 points
- **Result: LONG signal** ✅

## 📉 Example: Getting a SHORT Signal

If BTC is down 5% in 24h:
- Market momentum: -5% × 1.5 = -7.5 points
- If sentiment is negative: -10-20 points
- Combined score: ~-20-30 points
- **Result: SHORT signal** ✅

## 🚀 Quick Start

1. **Start server**:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Run test script**:
   ```bash
   python test_scenarios.py BTC 1000.0 aggressive
   ```

3. **Or use WebSocket client**:
   ```bash
   python websocket_client.py BTC USDC 1000.0 aggressive
   ```

The system is now **more sensitive** and should generate LONG/SHORT signals more frequently, especially with volatile tokens like BTC, ETH, or SOL during active market hours.

