"""
Test scenarios to generate LONG/SHORT signals
Simulates different market conditions to test the system
"""
import asyncio
import json
import websockets
from datetime import datetime


async def test_scenario(token="BTC", stablecoin="USDC", portfolio=1000.0, risk="aggressive"):
    """Test a scenario and show if we get LONG/SHORT signals"""
    uri = "ws://localhost:8001/ws/stream"
    
    try:
        async with websockets.connect(uri) as ws:
            # Activate agent
            await ws.send(json.dumps({
                "token": token,
                "stablecoin": stablecoin,
                "portfolio_amount": portfolio,
                "risk_level": risk
            }))
            
            print(f"\n{'='*80}")
            print(f"🧪 TESTING SCENARIO: {token} with {portfolio} {stablecoin}")
            print(f"{'='*80}\n")
            
            count = 0
            long_count = 0
            short_count = 0
            hold_count = 0
            
            while count < 20:  # Test 20 updates
                try:
                    response = await ws.recv()
                    data = json.loads(response)
                    count += 1
                    
                    if "status" in data:
                        print(f"✅ {data['message']}\n")
                        continue
                    
                    if "error" in data:
                        print(f"❌ Error: {data['error']}\n")
                        continue
                    
                    rec = data.get('recommendation', 'HOLD')
                    score = data.get('signal_score', 0)
                    confidence = data.get('confidence', 0)
                    exec_signal = data.get('execution_signal', {})
                    
                    if rec == "LONG":
                        long_count += 1
                        emoji = "🟢"
                    elif rec == "SHORT":
                        short_count += 1
                        emoji = "🔴"
                    else:
                        hold_count += 1
                        emoji = "🟡"
                    
                    print(f"{emoji} Update #{count}: {rec} | Score: {score:+.2f} | Confidence: {confidence:.1f}%")
                    
                    if exec_signal.get('should_open'):
                        print(f"   ⚡ EXECUTION: {exec_signal.get('action')}")
                    
                    if data.get('position_info', {}).get('status') == 'open':
                        pos = data['position_info']
                        print(f"   📊 Position: {pos.get('type')} | PnL: ${pos.get('pnl_usd', 0):+.2f} ({pos.get('pnl_pct', 0):+.2f}%)")
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    break
            
            print(f"\n{'='*80}")
            print("📊 RESULTS SUMMARY")
            print(f"{'='*80}")
            print(f"🟢 LONG signals: {long_count}")
            print(f"🔴 SHORT signals: {short_count}")
            print(f"🟡 HOLD signals: {hold_count}")
            print(f"Total updates: {count}")
            
            if long_count > 0 or short_count > 0:
                print(f"\n✅ SUCCESS: Got {long_count + short_count} trading signals!")
            else:
                print(f"\n⚠️  All HOLD signals. Try different tokens or wait for market movement.")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")


async def test_multiple_tokens():
    """Test multiple tokens to find ones with signals"""
    tokens = ["BTC", "ETH", "SOL", "APT", "BNB", "XRP", "ADA", "AVAX"]
    
    print("\n" + "="*80)
    print("🔍 TESTING MULTIPLE TOKENS FOR SIGNALS")
    print("="*80 + "\n")
    
    for token in tokens:
        print(f"\n📊 Testing {token}...")
        try:
            async with websockets.connect("ws://localhost:8001/ws/stream") as ws:
                await ws.send(json.dumps({
                    "token": token,
                    "stablecoin": "USDC",
                    "portfolio_amount": 1000.0,
                    "risk_level": "aggressive"
                }))
                
                # Wait for connection
                await ws.recv()
                
                # Get 5 updates
                for i in range(5):
                    response = await ws.recv()
                    data = json.loads(response)
                    
                    if "recommendation" in data:
                        rec = data['recommendation']
                        score = data.get('signal_score', 0)
                        if rec != "HOLD":
                            print(f"   ✅ {token}: {rec} (Score: {score:+.2f})")
                            break
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ Error testing {token}: {e}")
        
        await asyncio.sleep(2)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "multi":
        # Test multiple tokens
        asyncio.run(test_multiple_tokens())
    else:
        # Test single scenario
        token = sys.argv[1] if len(sys.argv) > 1 else "BTC"
        portfolio = float(sys.argv[2]) if len(sys.argv) > 2 else 1000.0
        risk = sys.argv[3] if len(sys.argv) > 3 else "aggressive"
        
        print(f"\n🧪 Testing scenario: {token} with {portfolio} USDC ({risk} risk)")
        print("This will show if we get LONG/SHORT signals...\n")
        
        asyncio.run(test_scenario(token, "USDC", portfolio, risk))

