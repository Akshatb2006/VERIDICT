"""
Test client for the FastAPI WebSocket endpoint
Example usage of the real-time streaming API
"""
import asyncio
import json
import websockets
from datetime import datetime


async def test_websocket_stream():
    """Test the WebSocket streaming endpoint"""
    uri = "ws://localhost:8001/ws/stream"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send initial request
            request = {
                "token": "APT",  # Change to your token
                "amount": 100.0  # Amount of tokens you have
            }
            
            print(f"📤 Sending request: {json.dumps(request, indent=2)}")
            await websocket.send(json.dumps(request))
            
            # Receive and print responses
            print("\n🔄 Starting real-time stream...\n")
            count = 0
            
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    count += 1
                    
                    print(f"\n{'='*80}")
                    print(f"📊 Update #{count} - {datetime.now().strftime('%H:%M:%S')}")
                    print(f"{'='*80}")
                    
                    if "error" in data:
                        print(f"❌ Error: {data['error']}")
                        continue
                    
                    if "status" in data:
                        print(f"✅ {data['message']}")
                        continue
                    
                    # Display clear action message (most important!)
                    action_message = data.get('action_message', '')
                    clear_action = data.get('clear_action', 'HOLD')
                    recommendation = data.get('recommendation', 'HOLD')
                    confidence = data.get('confidence', 0)
                    score = data.get('signal_score', 0)
                    
                    # Big, clear display of what to do
                    print("\n" + "="*80)
                    print("🎯 WHAT TO DO RIGHT NOW:")
                    print("="*80)
                    
                    if recommendation == "LONG":
                        print(f"\n🟢🟢🟢  GO LONG - BUY {data.get('token', 'TOKEN')}  🟢🟢🟢")
                        print(f"   Confidence: {confidence}% | Signal Score: {score:+.2f}")
                        print(f"   ⚠️  ACTION REQUIRED: Open a LONG position")
                    elif recommendation == "SHORT":
                        print(f"\n🔴🔴🔴  GO SHORT - SELL {data.get('token', 'TOKEN')}  🔴🔴🔴")
                        print(f"   Confidence: {confidence}% | Signal Score: {score:+.2f}")
                        print(f"   ⚠️  ACTION REQUIRED: Open a SHORT position")
                    else:
                        print(f"\n🟡🟡🟡  HOLD - WAIT  🟡🟡🟡")
                        print(f"   Confidence: {confidence}% | Signal Score: {score:+.2f}")
                        print(f"   ✅ NO ACTION: Wait for LONG or SHORT signal")
                    
                    print(f"\n💬 {action_message}")
                    print("="*80)
                    
                    # Market data (compact)
                    market = data.get('market_data', {})
                    print(f"\n📊 Quick Stats:")
                    print(f"   Price: ${market.get('price', 0):,.4f} | 24h: {market.get('percent_change_24h', 0):+.2f}%")
                    
                    # Only show detailed info if LONG or SHORT (action required)
                    if recommendation in ["LONG", "SHORT"]:
                        leverage = data.get('leverage_suggestion', {})
                        perp = data.get('perp_trade_example', {})
                        
                        print(f"\n⚡ Suggested Leverage: {leverage.get('suggested_leverage', 1)}x")
                        print(f"\n💼 Your Position ({data.get('amount', 0)} tokens):")
                        print(f"   Collateral: ${perp.get('collateral_usd', 0):,.2f}")
                        print(f"   Position Size: ${perp.get('position_size_usd', 0):,.2f}")
                        
                        print(f"\n📊 Potential PnL (5% price move):")
                        up = perp.get('if_price_moves_5pct_up', {})
                        down = perp.get('if_price_moves_5pct_down', {})
                        print(f"   If price ↑ 5%: ${up.get('pnl', 0):+,.2f} ({up.get('roi_pct', 0):+.2f}%)")
                        print(f"   If price ↓ 5%: ${down.get('pnl', 0):+,.2f} ({down.get('roi_pct', 0):+.2f}%)")
                    
                    print(f"\n⏰ Update #{count} | {datetime.now().strftime('%H:%M:%S')}")
                    print("="*80 + "\n")
                    
                    # Stream continuously - no limit
                
                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ Connection closed by server")
                    break
                except Exception as e:
                    print(f"\n❌ Error receiving data: {e}")
                    break
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8001")


def test_rest_endpoint():
    """Test the REST API endpoint"""
    import requests
    
    url = "http://localhost:8001/api/analyze"
    payload = {
        "token": "APT",
        "amount": 100.0
    }
    
    print(f"📤 Sending POST request to {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print("✅ Response received:")
        print(json.dumps(data, indent=2))
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rest":
        # Test REST endpoint
        test_rest_endpoint()
    else:
        # Test WebSocket endpoint
        print("🚀 Starting WebSocket test client...")
        print("Press Ctrl+C to stop\n")
        asyncio.run(test_websocket_stream())

