"""
Test the polling-based agent system
Simulates frontend polling behavior
"""
import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_polling_system():
    """Test the complete polling workflow"""
    
    token = "APT"
    stablecoin = "USDC"
    portfolio_amount = 100.0
    risk_level = "aggressive"
    
    print("="*80)
    print("🧪 TESTING POLLING-BASED AGENT SYSTEM")
    print("="*80)
    
    # Step 1: Activate
    print("\n1️⃣ Activating agent...")
    activate_response = requests.post(
        f"{BASE_URL}/api/activate",
        json={
            "token": token,
            "stablecoin": stablecoin,
            "portfolio_amount": portfolio_amount,
            "risk_level": risk_level
        }
    )
    print(f"Status: {activate_response.status_code}")
    print(f"Response: {json.dumps(activate_response.json(), indent=2)}")
    
    if activate_response.status_code != 200:
        print("❌ Failed to activate agent")
        return
    
    # Step 2: Poll for updates (simulate frontend)
    print("\n2️⃣ Polling for updates (simulating frontend)...")
    print("   Polling every 1 second for 10 updates...\n")
    
    for i in range(10):
        poll_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "token": token,
                "stablecoin": stablecoin,
                "portfolio_amount": portfolio_amount,
                "risk_level": risk_level
            }
        )
        
        if poll_response.status_code == 200:
            data = poll_response.json()
            rec = data.get('recommendation', 'UNKNOWN')
            score = data.get('signal_score', 0)
            confidence = data.get('confidence', 0)
            iteration = data.get('iteration', 0)
            
            if rec == "LONG":
                emoji = "🟢"
            elif rec == "SHORT":
                emoji = "🔴"
            else:
                emoji = "🟡"
            
            print(f"   Update #{i+1}: {emoji} {rec} | Score: {score:+.2f} | Confidence: {confidence:.1f}% | Iteration: {iteration}")
            
            # Show execution signals
            exec_signal = data.get('execution_signal', {})
            if exec_signal.get('should_open'):
                print(f"      ⚡ EXECUTION: {exec_signal.get('action')}")
            if exec_signal.get('should_close'):
                print(f"      🔴 CLOSING: {exec_signal.get('exit_conditions', [])}")
            
            # Show position if open
            position = data.get('position_info', {})
            if position.get('status') == 'open':
                print(f"      📊 Position: {position.get('type')} | PnL: ${position.get('pnl_usd', 0):+.2f}")
        else:
            print(f"   Update #{i+1}: Error {poll_response.status_code}")
        
        time.sleep(1)
    
    # Step 3: Deactivate
    print("\n3️⃣ Deactivating agent...")
    deactivate_response = requests.post(
        f"{BASE_URL}/api/deactivate",
        json={
            "token": token,
            "stablecoin": stablecoin,
            "portfolio_amount": portfolio_amount
        }
    )
    print(f"Status: {deactivate_response.status_code}")
    print(f"Response: {json.dumps(deactivate_response.json(), indent=2)}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    try:
        test_polling_system()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("   Make sure the server is running on http://localhost:8001")
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")

