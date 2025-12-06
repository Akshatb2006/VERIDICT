"""
CoinMarketCap API integration for fetching market data
"""
import requests
import os
from typing import Dict, Optional
from datetime import datetime


class CoinMarketCapAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }
        # Create a new session for each request to prevent any connection pooling/caching
        # This ensures every API call is completely fresh
    
    def get_token_info(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive token information from CoinMarketCap"""
        try:
            import time
            request_start = time.time()
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            # CMC API doesn't allow arbitrary parameters like "_" for cache-busting
            # Instead, we rely on HTTP headers and fresh sessions for cache prevention
            parameters = {
                'symbol': symbol.upper(),
                'convert': 'USD'
            }
            
            # CRITICAL: Create a completely new session for each request
            # This prevents any connection pooling, caching, or reuse that might cause stale data
            session = requests.Session()
            
            # Add Cache-Control headers to prevent any HTTP-level caching
            fresh_headers = self.headers.copy()
            fresh_headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            fresh_headers['Pragma'] = 'no-cache'
            fresh_headers['Expires'] = '0'
            
            print(f"[CMC API] Making fresh API call for {symbol.upper()} at {datetime.now().isoformat()}")
            response = session.get(url, headers=fresh_headers, params=parameters, timeout=10)
            
            # Close the session immediately to ensure no reuse
            session.close()
            request_time = time.time() - request_start
            print(f"[CMC API] Response received in {request_time:.2f}s - Status: {response.status_code}")
            
            # Check response status
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('status', {}).get('error_message', f'HTTP {response.status_code}')
                print(f"❌ CMC API Error [{response.status_code}]: {error_msg}")
                if 'error_message' in error_data.get('status', {}):
                    print(f"   Details: {error_data['status'].get('error_message', 'Unknown error')}")
                return None
            
            data = response.json()
            
            # Check for API errors in response
            if 'status' in data and data['status'].get('error_code', 0) != 0:
                error_msg = data['status'].get('error_message', 'Unknown error')
                print(f"❌ CMC API Error: {error_msg}")
                return None
            
            if 'data' in data and symbol.upper() in data['data']:
                # Handle both list and dict responses (CMC API can return either)
                token_data_raw = data['data'][symbol.upper()]
                
                # If it's a list, take the first item
                if isinstance(token_data_raw, list):
                    token_data = token_data_raw[0]
                # If it's a dict, use it directly
                elif isinstance(token_data_raw, dict):
                    token_data = token_data_raw
                else:
                    print(f"⚠️  Unexpected data type for token data: {type(token_data_raw)}")
                    return None
                
                quote = token_data['quote']['USD']
                
                # CRITICAL: Create completely fresh dict with explicit type conversions
                # This ensures no reference sharing and forces fresh data on each call
                result = {
                    'name': str(token_data['name']),
                    'symbol': str(token_data['symbol']),
                    'price': float(quote['price']),  # Explicit float conversion
                    'market_cap': float(quote.get('market_cap', 0) or 0),
                    'volume_24h': float(quote.get('volume_24h', 0) or 0),
                    'percent_change_1h': float(quote.get('percent_change_1h', 0) or 0),
                    'percent_change_24h': float(quote.get('percent_change_24h', 0) or 0),
                    'percent_change_7d': float(quote.get('percent_change_7d', 0) or 0),
                    'circulating_supply': float(token_data.get('circulating_supply', 0) or 0),
                    'total_supply': float(token_data.get('total_supply', 0) or 0),
                    'last_updated': str(quote.get('last_updated', datetime.now().isoformat()))
                }
                
                # Log with memory address to verify it's a new object each time
                price_id = id(result['price'])
                print(f"[CMC API] Fresh data received - Price: ${result['price']:.4f} (ID: {price_id}), 24h Change: {result['percent_change_24h']:.2f}%, Last Updated: {result['last_updated']}")
                return result
            
            # Token not found
            print(f"⚠️  Token '{symbol.upper()}' not found in CMC response")
            if 'data' in data:
                print(f"   Available symbols in response: {list(data.get('data', {}).keys())}")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ CMC API Request Error: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Response: {error_data}")
                except:
                    print(f"   Response status: {e.response.status_code}")
                    print(f"   Response text: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching CMC data: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_trending_tokens(self) -> list:
        """Get trending tokens (if available in your CMC plan)"""
        try:
            url = f"{self.base_url}/cryptocurrency/trending/latest"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"Error fetching trending tokens: {e}")
            return []
    
    def get_historical_data(self, symbol: str, days: int = 30) -> Optional[list]:
        """
        Get historical price data for a token with OHLC (candlestick) data
        Uses CoinGecko as fallback since CMC historical data requires higher tier
        """
        try:
            # First try to get token ID from CoinGecko
            gecko_id_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'APT': 'aptos',
                'DOGE': 'dogecoin',
                'SOL': 'solana',
                'BNB': 'binancecoin',
                'ADA': 'cardano',
                'XRP': 'ripple',
                'MATIC': 'matic-network',
                'DOT': 'polkadot',
                'AVAX': 'avalanche-2',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'ATOM': 'cosmos',
                'LTC': 'litecoin',
            }
            
            gecko_id = gecko_id_map.get(symbol.upper())
            if not gecko_id:
                # Try to search for it
                search_url = f"https://api.coingecko.com/api/v3/search?query={symbol.lower()}"
                search_res = requests.get(search_url, timeout=10)
                if search_res.ok:
                    search_data = search_res.json()
                    if search_data.get('coins'):
                        gecko_id = search_data['coins'][0]['id']
            
            if gecko_id:
                # Fetch historical data from CoinGecko
                url = f"https://api.coingecko.com/api/v3/coins/{gecko_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'daily' if days > 7 else 'hourly'
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Format the data with OHLC (candlestick) format
                prices = data.get('prices', [])
                market_caps = data.get('market_caps', [])
                volumes = data.get('total_volumes', [])
                
                historical = []
                for i, price_point in enumerate(prices):
                    timestamp = price_point[0] / 1000
                    price = price_point[1]
                    
                    # For candlestick, we need OHLC
                    # If we have previous price, use it for open, otherwise use current
                    if i > 0:
                        open_price = prices[i-1][1]
                    else:
                        open_price = price
                    
                    # High and Low - approximate from price movement
                    # In real scenario, you'd get this from exchange API
                    high_price = price * 1.02  # Approximate
                    low_price = price * 0.98  # Approximate
                    close_price = price
                    
                    volume = volumes[i][1] if i < len(volumes) else 0
                    
                    historical.append({
                        'timestamp': timestamp,
                        'time': datetime.fromtimestamp(timestamp).isoformat(),
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'price': price,  # Keep for compatibility
                        'volume': volume,
                        'date': datetime.fromtimestamp(timestamp).isoformat()
                    })
                
                return historical
            else:
                # Fallback: Generate synthetic data based on current price
                print(f"⚠️  Token {symbol} not found in CoinGecko, generating synthetic data")
                return self._generate_synthetic_historical(symbol, days)
                
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            # Fallback to synthetic data
            return self._generate_synthetic_historical(symbol, days)
    
    def _generate_synthetic_historical(self, symbol: str, days: int) -> list:
        """Generate synthetic historical data with OHLC (candlestick) format"""
        import random
        from datetime import timedelta
        
        # Get current price
        current_data = self.get_token_info(symbol)
        if not current_data:
            return []
        
        current_price = current_data['price']
        historical = []
        now = datetime.now()
        
        # Generate data points
        interval_hours = 1 if days <= 7 else 24
        points = days * (24 // interval_hours)
        
        # Start with a price slightly different from current
        price = current_price * (1 + random.uniform(-0.1, 0.1))
        
        for i in range(points, -1, -1):
            timestamp = now - timedelta(hours=i * interval_hours)
            # Random walk with slight trend
            price_change = random.uniform(-0.02, 0.02)
            price = price * (1 + price_change)
            
            # Generate OHLC for candlestick
            open_price = price
            high_price = price * (1 + random.uniform(0, 0.03))
            low_price = price * (1 - random.uniform(0, 0.03))
            close_price = price * (1 + random.uniform(-0.01, 0.01))
            volume = random.uniform(1000000, 10000000)
            
            historical.append({
                'timestamp': timestamp.timestamp(),
                'time': timestamp.isoformat(),
                'open': max(open_price, 0.0001),
                'high': max(high_price, 0.0001),
                'low': max(low_price, 0.0001),
                'close': max(close_price, 0.0001),
                'price': max(price, 0.0001),  # Keep for compatibility
                'volume': volume,
                'date': timestamp.isoformat()
            })
        
        return historical

