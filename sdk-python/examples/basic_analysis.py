"""
Basic example: Single analysis with VERDICT SDK

This example shows how to perform a one-time trading analysis.
"""

import asyncio
from verdict_sdk import VerdictClient


async def main():
    # Initialize client with your API keys
    client = VerdictClient(
        api_url="http://localhost:8000",  # Change to your VERDICT API URL
        cmc_api_key="YOUR_CMC_API_KEY",  # Your CoinMarketCap API key
        gemini_api_key="YOUR_GEMINI_API_KEY",  # Your Google Gemini API key
    )
    
    try:
        # Perform analysis
        print("🔍 Analyzing BTC...")
        result = await client.analyze(
            token="BTC",
            stablecoin="USDC",
            portfolio_amount=1000.0,
            risk_level="moderate"
        )
        
        # Print results
        print(f"\n{'='*60}")
        print(f"Token: {result.token}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Confidence: {result.confidence}%")
        print(f"Signal Score: {result.signal_score}")
        print(f"{'='*60}\n")
        
        print(f"📊 Market Data:")
        print(f"  Price: ${result.market_data.price:,.2f}")
        print(f"  24h Change: {result.market_data.percent_change_24h:+.2f}%")
        print(f"  24h Volume: ${result.market_data.volume_24h:,.0f}")
        
        print(f"\n🤖 AI Sentiment:")
        print(f"  Overall Sentiment: {result.sentiment_data.overall_sentiment:.2f}")
        print(f"  Risk Level: {result.sentiment_data.risk_level}")
        print(f"  Key Factors: {', '.join(result.sentiment_data.key_factors[:3])}")
        
        print(f"\n⚡ Leverage Suggestion:")
        print(f"  Suggested Leverage: {result.leverage_suggestion.suggested_leverage}x")
        print(f"  Max Safe Leverage: {result.leverage_suggestion.max_safe_leverage}x")
        
        print(f"\n💰 Perp Trade Details:")
        print(f"  Collateral: ${result.perp_trade_details.collateral_stablecoin:,.2f} {result.perp_trade_details.stablecoin}")
        print(f"  Position Size: ${result.perp_trade_details.position_size_usd:,.2f}")
        print(f"  Token Exposure: {result.perp_trade_details.token_exposure:.4f} {result.token}")
        
        print(f"\n📈 If price moves +5%:")
        print(f"  PnL: ${result.perp_trade_details.if_price_moves_5pct_up['pnl']:+,.2f}")
        print(f"  ROI: {result.perp_trade_details.if_price_moves_5pct_up['roi_pct']:+.2f}%")
        
        print(f"\n📉 If price moves -5%:")
        print(f"  PnL: ${result.perp_trade_details.if_price_moves_5pct_down['pnl']:+,.2f}")
        print(f"  ROI: {result.perp_trade_details.if_price_moves_5pct_down['roi_pct']:+.2f}%")
        
        print(f"\n🔐 Flare Verification:")
        print(f"  Verified: {'✅' if result.verified else '❌'}")
        print(f"  FTSO Price: ${result.ftso_price:,.2f}")
        print(f"  FDC Verified: {'✅' if result.fdc_verified else '❌'}")
        print(f"  Contract Verified: {'✅' if result.contract_verified else '❌'}")
        
        print(f"\n💡 Reasoning:")
        print(f"  {result.reasoning}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
