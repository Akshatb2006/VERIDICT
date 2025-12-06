"""
Real-time streaming example with VERDICT SDK

This example shows how to stream live trading signals.
"""

import asyncio
from verdict_sdk import VerdictClient


async def main():
    client = VerdictClient(
        api_url="http://localhost:8000",
        cmc_api_key="YOUR_CMC_API_KEY",
        gemini_api_key="YOUR_GEMINI_API_KEY",
    )
    
    try:
        print("🚀 Starting real-time analysis stream for BTC...")
        print("Press Ctrl+C to stop\n")
        
        iteration = 0
        async for analysis in client.stream_agent(
            token="BTC",
            portfolio_amount=1000.0,
            risk_level="moderate",
            interval=2.0  # Update every 2 seconds
        ):
            iteration += 1
            
            # Clear previous line (simple console animation)
            print(f"\r{'='*80}", end='')
            print(f"\nIteration #{iteration} - {analysis.timestamp}")
            print(f"{'='*80}")
            
            # Real-time price
            price = analysis.market_data.price
            change_24h = analysis.market_data.percent_change_24h
            change_emoji = "📈" if change_24h > 0 else "📉"
            
            print(f"\n💰 Price: ${price:,.2f} {change_emoji} ({change_24h:+.2f}% 24h)")
            
            # Recommendation with emoji
            rec_emoji = {
                "LONG": "🟢",
                "SHORT": "🔴",
                "HOLD": "🟡"
            }.get(analysis.recommendation, "⚪")
            
            print(f"{rec_emoji} {analysis.recommendation} - Confidence: {analysis.confidence:.1f}%")
            
            # Signal strength bar
            signal_strength = int(analysis.confidence / 10)
            bar = "█" * signal_strength + "░" * (10 - signal_strength)
            print(f"Signal Strength: [{bar}] {analysis.confidence:.1f}%")
            
            # Sentiment
            sentiment = analysis.sentiment_data.overall_sentiment
            sentiment_emoji = "😊" if sentiment > 0 else "😟" if sentiment < 0 else "😐"
            print(f"{sentiment_emoji} Sentiment: {sentiment:.2f}")
            
            # Verification status
            verification = "✅ VERIFIED" if analysis.verified else "❌ NOT VERIFIED"
            print(f"🔐 {verification}")
            
            # Trading suggestion
            if analysis.recommendation != "HOLD":
                print(f"\n💡 Suggestion:")
                print(f"   Open {analysis.recommendation} position")
                print(f"   Leverage: {analysis.leverage_suggestion.suggested_leverage}x")
                print(f"   Position Size: ${analysis.perp_trade_details.position_size_usd:,.2f}")
            
            print()
            
    except KeyboardInterrupt:
        print("\n\n👋 Stopping stream...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
