"""
Simple WebSocket client to display real-time trading recommendations
Shows clear LONG/SHORT/HOLD signals every second
"""
import asyncio
import json
import websockets
from datetime import datetime
import sys


async def stream_recommendations(token="APT", stablecoin="USDC", portfolio_amount=100.0, 
                                 risk_level="aggressive", port=8001):
    """Stream real-time perp trading with auto-execution"""
    uri = f"ws://localhost:{port}/ws/stream"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send initial request with new format
            request = {
                "token": token.upper(),
                "stablecoin": stablecoin.upper(),
                "portfolio_amount": float(portfolio_amount),
                "risk_level": risk_level.lower()
            }
            await websocket.send(json.dumps(request))
            
            print("\n" + "="*80)
            print("🚀 PERP DEX AUTO-TRADING AGENT")
            print("="*80)
            print(f"📊 Token: {token.upper()} | Collateral: {portfolio_amount} {stablecoin.upper()}")
            print(f"🎲 Risk Level: {risk_level.upper()}")
            print(f"🔄 Auto-execution: ENABLED | Updates every 1 second")
            print("="*80 + "\n")
            
            count = 0
            
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    count += 1
                    
                    # Skip connection confirmation
                    if "status" in data:
                        print(f"✅ {data['message']}\n")
                        continue
                    
                    if "error" in data:
                        print(f"❌ Error: {data['error']}\n")
                        continue
                    
                    # Extract key data
                    recommendation = data.get('recommendation', 'HOLD')
                    confidence = data.get('confidence', 0)
                    score = data.get('signal_score', 0)
                    price = data.get('market_data', {}).get('price', 0)
                    change_24h = data.get('market_data', {}).get('percent_change_24h', 0)
                    
                    # Execution signals
                    execution = data.get('execution_signal', {})
                    exec_action = execution.get('action', 'WAIT')
                    should_open = execution.get('should_open', False)
                    should_close = execution.get('should_close', False)
                    
                    # Position info
                    position_info = data.get('position_info', {})
                    position_status = position_info.get('status', 'none')
                    position_type = position_info.get('type', '')
                    pnl_usd = position_info.get('pnl_usd', 0)
                    pnl_pct = position_info.get('pnl_pct', 0)
                    
                    # Clear, prominent display
                    print("\n" + "="*80)
                    print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | Update #{count}")
                    print("="*80)
                    
                    # EXECUTION SIGNALS (Most Important!)
                    if exec_action.startswith('OPENED_'):
                        pos_type = exec_action.replace('OPENED_', '')
                        print("\n" + "✅" * 25)
                        print(f"   ✅ POSITION OPENED: {pos_type} ✅")
                        print(f"   🎯 AUTO-EXECUTION: Position opened automatically!")
                        print("✅" * 25)
                    elif should_close:
                        print("\n" + "🔴" * 25)
                        print(f"   🔴 POSITION CLOSED 🔴")
                        print(f"   🎯 AUTO-EXECUTION: Position closed automatically!")
                        exit_reasons = execution.get('exit_conditions', [])
                        if exit_reasons:
                            print(f"   📋 Reason: {', '.join(exit_reasons)}")
                        print("🔴" * 25)
                    elif position_status == 'open':
                        print("\n" + "📊" * 25)
                        print(f"   📊 POSITION OPEN: {position_type}")
                        print(f"   💰 Current PnL: ${pnl_usd:+,.2f} ({pnl_pct:+.2f}%)")
                        print("📊" * 25)
                    elif exec_action == 'OPEN_LONG' or exec_action == 'OPEN_SHORT':
                        print("\n" + "⚠️" * 25)
                        print(f"   ⚠️  READY TO OPEN: {exec_action.replace('OPEN_', '')}")
                        print(f"   🎯 Waiting for confirmation...")
                        print("⚠️" * 25)
                    else:
                        # Recommendation display
                        if recommendation == "LONG":
                            print("\n" + "🟢" * 20)
                            print("   🟢 SIGNAL: LONG 🟢")
                            print("   ⏳ Monitoring for entry...")
                            print("🟢" * 20)
                        elif recommendation == "SHORT":
                            print("\n" + "🔴" * 20)
                            print("   🔴 SIGNAL: SHORT 🔴")
                            print("   ⏳ Monitoring for entry...")
                            print("🔴" * 20)
                        else:
                            print("\n" + "🟡" * 20)
                            print("   🟡 HOLD - WAIT 🟡")
                            print("   ✅ No position - Waiting for signal")
                            print("🟡" * 20)
                    
                    # Key metrics
                    print(f"\n📊 Signal: {score:+.2f} | Confidence: {confidence}%")
                    print(f"💰 Price: ${price:,.4f} | 24h: {change_24h:+.2f}%")
                    
                    # Position details if open
                    if position_status == 'open':
                        entry_price = position_info.get('entry_price', 0)
                        leverage = position_info.get('leverage', 1)
                        position_size = position_info.get('position_size', 0)
                        collateral = position_info.get('collateral', 0)
                        
                        print(f"\n💼 Position Details:")
                        print(f"   Type: {position_type}")
                        print(f"   Entry: ${entry_price:,.4f} | Current: ${price:,.4f}")
                        print(f"   Leverage: {leverage}x")
                        print(f"   Size: ${position_size:,.2f} (Collateral: ${collateral:,.2f})")
                        print(f"   PnL: ${pnl_usd:+,.2f} ({pnl_pct:+.2f}%)")
                    else:
                        # Show potential trade details
                        leverage = data.get('leverage_suggestion', {}).get('suggested_leverage', 1)
                        perp = data.get('perp_trade_details', {})
                        position_size = perp.get('position_size_usd', 0)
                        collateral = perp.get('collateral_stablecoin', 0)
                        token_exposure = perp.get('token_exposure', 0)
                        
                        print(f"\n💼 Potential Trade:")
                        print(f"   Leverage: {leverage}x")
                        print(f"   Position Size: ${position_size:,.2f}")
                        print(f"   Token Exposure: {token_exposure:,.4f} {token.upper()}")
                        
                        up = perp.get('if_price_moves_5pct_up', {})
                        down = perp.get('if_price_moves_5pct_down', {})
                        print(f"\n📈 Potential PnL (5% move):")
                        print(f"   ↑ +5%: ${up.get('pnl', 0):+,.2f} ({up.get('roi_pct', 0):+.2f}%)")
                        print(f"   ↓ -5%: ${down.get('pnl', 0):+,.2f} ({down.get('roi_pct', 0):+.2f}%)")
                    
                    print("="*80)
                    
                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ Connection closed")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    break
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print(f"Make sure server is running on port {port}")
        sys.exit(1)


if __name__ == "__main__":
    # Get parameters from command line or use defaults
    token = sys.argv[1] if len(sys.argv) > 1 else "APT"
    stablecoin = sys.argv[2] if len(sys.argv) > 2 else "USDC"
    portfolio_amount = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
    risk_level = sys.argv[4] if len(sys.argv) > 4 else "aggressive"
    port = int(sys.argv[5]) if len(sys.argv) > 5 else 8001
    
    print(f"\n🚀 Starting Perp DEX Auto-Trading Agent...")
    print(f"Token: {token} | Collateral: {portfolio_amount} {stablecoin}")
    print(f"Risk Level: {risk_level} | Port: {port}")
    print("\n💡 Examples:")
    print("   python websocket_client.py APT USDC 100.0 aggressive")
    print("   python websocket_client.py BTC USDC 1000.0 moderate")
    print("   python websocket_client.py ETH USDT 500.0 conservative")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        asyncio.run(stream_recommendations(token, stablecoin, portfolio_amount, risk_level, port))
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user")

