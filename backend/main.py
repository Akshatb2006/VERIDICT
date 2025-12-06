"""
Sentiment Catcher & On-Chain Data Analyzer for Aptos Perp DEX
CLI version - for API version, use app.py
"""
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from market_data import CoinMarketCapAPI
from sentiment_analyzer import SentimentAnalyzer
from aptos_analyzer import AptosAnalyzer
from decision_engine import DecisionEngine


class PerpDEXAnalyzer:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize APIs
        cmc_api_key = os.getenv('CMC_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not cmc_api_key or not openai_api_key:
            raise ValueError("Please set CMC_API_KEY and OPENAI_API_KEY in your .env file")
        
        self.cmc = CoinMarketCapAPI(cmc_api_key)
        self.sentiment_analyzer = SentimentAnalyzer(openai_api_key)
        self.aptos_analyzer = AptosAnalyzer()
        self.decision_engine = DecisionEngine()
        
        self.update_interval = int(os.getenv('UPDATE_INTERVAL', 60))
    
    def analyze_token(self, token_symbol: str) -> dict:
        """
        Complete analysis pipeline for a token
        """
        print(f"\n{'='*80}")
        print(f"Analyzing {token_symbol} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Step 1: Fetch market data
        print("📊 Fetching market data from CoinMarketCap...")
        market_data = self.cmc.get_token_info(token_symbol)
        
        if not market_data:
            print(f"❌ Could not fetch market data for {token_symbol}")
            return None
        
        print(f"✅ Price: ${market_data['price']:,.4f}")
        print(f"   24h Change: {market_data['percent_change_24h']:+.2f}%")
        print(f"   24h Volume: ${market_data['volume_24h']:,.0f}")
        print(f"   Market Cap: ${market_data['market_cap']:,.0f}\n")
        
        # Step 2: Analyze sentiment
        print("🤖 Analyzing sentiment with OpenAI...")
        sentiment_data = self.sentiment_analyzer.analyze_token_sentiment(
            token_symbol, 
            market_data['name'], 
            market_data
        )
        
        print(f"✅ Overall Sentiment: {sentiment_data['overall_sentiment']:+.2f}")
        print(f"   Short-term Sentiment: {sentiment_data['short_term_sentiment']:+.2f}")
        print(f"   Risk Level: {sentiment_data['risk_level']}")
        print(f"   Key Factors: {', '.join(sentiment_data.get('key_factors', [])[:3])}\n")
        
        # Step 3: Analyze on-chain data
        print("⛓️  Analyzing Aptos on-chain data...")
        onchain_data = self.aptos_analyzer.analyze_onchain_signals(token_symbol)
        
        print(f"✅ On-chain Signal: {onchain_data['onchain_signal']:+.2f}")
        print(f"   Activity Score: {onchain_data['activity_score']:.2f}")
        print(f"   Liquidity Score: {onchain_data['liquidity_score']:.2f}\n")
        
        # Step 4: Generate final recommendation
        print("🎯 Generating trading recommendation...")
        decision = self.decision_engine.calculate_signal(
            market_data, 
            sentiment_data, 
            onchain_data
        )
        
        # Display recommendation
        self._display_recommendation(decision, market_data)
        
        return {
            'token': token_symbol,
            'market_data': market_data,
            'sentiment_data': sentiment_data,
            'onchain_data': onchain_data,
            'decision': decision,
            'timestamp': datetime.now().isoformat()
        }
    
    def _display_recommendation(self, decision: dict, market_data: dict):
        """Display formatted trading recommendation"""
        recommendation = decision['recommendation']
        confidence = decision['confidence']
        score = decision['final_score']
        leverage = decision['leverage_suggestion']
        
        print(f"\n{'='*80}")
        print("🎯 TRADING RECOMMENDATION")
        print(f"{'='*80}")
        
        # Color-coded recommendation
        if recommendation == "LONG":
            print(f"🟢 RECOMMENDATION: {recommendation} (BUY)")
        elif recommendation == "SHORT":
            print(f"🔴 RECOMMENDATION: {recommendation} (SELL)")
        else:
            print(f"🟡 RECOMMENDATION: {recommendation}")
        
        print(f"\n📈 Confidence: {confidence}%")
        print(f"📊 Signal Score: {score:.2f}")
        print(f"⚡ Suggested Leverage: {leverage['suggested_leverage']}x")
        print(f"⚠️  Max Safe Leverage: {leverage['max_safe_leverage']}x")
        
        print(f"\n📋 Signal Breakdown:")
        breakdown = decision['signal_breakdown']
        print(f"   Sentiment: {breakdown['sentiment_score']:+.2f}")
        print(f"   Market Momentum: {breakdown['market_momentum']:+.2f}")
        print(f"   On-chain Signal: {breakdown['onchain_signal']:+.2f}")
        print(f"   Risk Level: {breakdown['risk_level']}")
        
        print(f"\n💡 Reasoning:")
        print(f"   {decision['reasoning']}")
        
        # Perp DEX example calculation
        if recommendation in ["LONG", "SHORT"]:
            self._display_perp_example(recommendation, market_data, leverage['suggested_leverage'])
        
        print(f"{'='*80}\n")
    
    def _display_perp_example(self, recommendation: str, market_data: dict, leverage: int):
        """Display example perp DEX trade calculation"""
        print(f"\n💰 Example Perp DEX Trade ({recommendation}):")
        print(f"   Collateral: $100 USDC")
        print(f"   Leverage: {leverage}x")
        print(f"   Position Size: ${100 * leverage}")
        print(f"   Current Price: ${market_data['price']:,.4f}")
        
        if recommendation == "LONG":
            print(f"   If price goes up 5%:")
            print(f"      PnL: +${100 * leverage * 0.05:.2f}")
            print(f"      ROI: +{leverage * 5}%")
        else:
            print(f"   If price goes down 5%:")
            print(f"      PnL: +${100 * leverage * 0.05:.2f}")
            print(f"      ROI: +{leverage * 5}%")
    
    def monitor_token(self, token_symbol: str, duration_minutes: int = None):
        """
        Continuously monitor a token and provide updates
        """
        print(f"\n🚀 Starting continuous monitoring for {token_symbol}")
        print(f"   Update interval: {self.update_interval} seconds")
        if duration_minutes:
            print(f"   Duration: {duration_minutes} minutes")
        print(f"   Press Ctrl+C to stop\n")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n🔄 Update #{iteration}")
                
                result = self.analyze_token(token_symbol)
                
                if duration_minutes:
                    elapsed = (time.time() - start_time) / 60
                    if elapsed >= duration_minutes:
                        print(f"\n⏰ Monitoring duration completed ({duration_minutes} minutes)")
                        break
                
                # Wait before next update
                if iteration > 0:  # Don't sleep after last iteration
                    print(f"\n⏳ Waiting {self.update_interval} seconds until next update...")
                    time.sleep(self.update_interval)
        
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped by user")
            print(f"   Total updates: {iteration}")
    
    def analyze_once(self, token_symbol: str):
        """Perform a single analysis"""
        return self.analyze_token(token_symbol)


def main():
    """Main entry point"""
    try:
        analyzer = PerpDEXAnalyzer()
        
        # Get token symbol from environment or user input
        token_symbol = os.getenv('DEFAULT_TOKEN', 'APT')
        
        import sys
        if len(sys.argv) > 1:
            token_symbol = sys.argv[1].upper()
        
        # Check if user wants continuous monitoring
        monitor_mode = os.getenv('MONITOR_MODE', 'false').lower() == 'true'
        
        if monitor_mode or len(sys.argv) > 2 and sys.argv[2] == '--monitor':
            # Continuous monitoring
            duration = None
            if len(sys.argv) > 3:
                try:
                    duration = int(sys.argv[3])
                except ValueError:
                    pass
            analyzer.monitor_token(token_symbol, duration)
        else:
            # Single analysis
            analyzer.analyze_once(token_symbol)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

