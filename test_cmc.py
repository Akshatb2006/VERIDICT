"""
Test script to debug CoinMarketCap API issues
"""
import os
from dotenv import load_dotenv
from market_data import CoinMarketCapAPI

load_dotenv()

cmc_api_key = os.getenv('CMC_API_KEY')

if not cmc_api_key:
    print("❌ CMC_API_KEY not found in .env file")
    exit(1)

print(f"✅ CMC API Key found: {cmc_api_key[:10]}...{cmc_api_key[-4:]}")
print("\n" + "="*80)
print("Testing CoinMarketCap API...")
print("="*80 + "\n")

cmc = CoinMarketCapAPI(cmc_api_key)

# Test with APT
print("1. Testing with APT token:")
print("-" * 80)
result = cmc.get_token_info("APT")
if result:
    print(f"✅ Success! Got data for {result['name']} ({result['symbol']})")
    print(f"   Price: ${result['price']:,.4f}")
    print(f"   24h Change: {result['percent_change_24h']:+.2f}%")
    print(f"   Market Cap: ${result['market_cap']:,.0f}")
else:
    print("❌ Failed to get data for APT")

print("\n" + "="*80)
print("2. Testing with BTC token:")
print("-" * 80)
result = cmc.get_token_info("BTC")
if result:
    print(f"✅ Success! Got data for {result['name']} ({result['symbol']})")
    print(f"   Price: ${result['price']:,.4f}")
    print(f"   24h Change: {result['percent_change_24h']:+.2f}%")
else:
    print("❌ Failed to get data for BTC")

print("\n" + "="*80)
print("Debugging complete!")
print("="*80)

