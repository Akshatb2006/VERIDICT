"""
Simple trading bot example using VERDICT SDK

This bot demonstrates:
- Real-time signal monitoring
- Automated trade decisions based on confidence thresholds
- Risk management
"""

import asyncio
from verdict_sdk import VerdictClient


class SimpleVerdictBot:
    """Simple trading bot using VERDICT signals."""
    
    def __init__(self, client: VerdictClient, confidence_threshold: float = 70.0):
        self.client = client
        self.confidence_threshold = confidence_threshold
        self.position = None  # Track current position
    
    async def execute_trade(self, action: str, analysis):
        """
        Execute a trade (this is a simulation - replace with real exchange API).
        """
        print(f"\n🎯 EXECUTING TRADE:")
        print(f"   Action: {action}")
        print(f"   Token: {analysis.token}")
        print(f"   Price: ${analysis.market_data.price:,.2f}")
        print(f"   Leverage: {analysis.leverage_suggestion.suggested_leverage}x")
        print(f"   Position Size: ${analysis.perp_trade_details.position_size_usd:,.2f}")
        
        # In a real bot, you would call exchange API here:
        # exchange.create_order(...)
        
        self.position = {
            "type": action,
            "entry_price": analysis.market_data.price,
            "token": analysis.token,
            "size": analysis.perp_trade_details.position_size_usd,
        }
    
    async def close_position(self, analysis):
        """Close current position."""
        if not self.position:
            return
        
        entry_price = self.position["entry_price"]
        exit_price = analysis.market_data.price
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        if self.position["type"] == "SHORT":
            pnl_pct = -pnl_pct
        
        print(f"\n🔒 CLOSING POSITION:")
        print(f"   Type: {self.position['type']}")
        print(f"   Entry: ${entry_price:,.2f}")
        print(f"   Exit: ${exit_price:,.2f}")
        print(f"   PnL: {pnl_pct:+.2f}%")
        
        self.position = None
    
    async def run(self, token: str, portfolio_amount: float = 1000.0):
        """Run the trading bot."""
        print(f"🤖 VERDICT Trading Bot Started")
        print(f"   Token: {token}")
        print(f"   Portfolio: ${portfolio_amount:,.2f}")
        print(f"   Confidence Threshold: {self.confidence_threshold}%")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            async for analysis in self.client.stream_agent(
                token=token,
                portfolio_amount=portfolio_amount,
                risk_level="moderate",
                interval=2.0
            ):
                # Print current status
                print(f"\r[{analysis.timestamp}] Price: ${analysis.market_data.price:,.2f} | "
                      f"{analysis.recommendation} ({analysis.confidence:.1f}%)", end='')
                
                # Check if signal is verified
                if not analysis.verified:
                    continue
                
                # Decision logic
                if self.position is None:
                    # No position - check if we should open one
                    if analysis.confidence >= self.confidence_threshold:
                        if analysis.recommendation in ["LONG", "SHORT"]:
                            await self.execute_trade(analysis.recommendation, analysis)
                else:
                    # Have position - check if we should close
                    current_type = self.position["type"]
                    
                    # Close on opposite signal with high confidence
                    if (analysis.recommendation != current_type and 
                        analysis.confidence >= self.confidence_threshold):
                        await self.close_position(analysis)
                    
                    # Close on HOLD with high confidence (neutral market)
                    elif analysis.recommendation == "HOLD" and analysis.confidence >= 60:
                        await self.close_position(analysis)
        
        except KeyboardInterrupt:
            print("\n\n👋 Stopping bot...")
            if self.position:
                print("⚠️  You have an open position. Remember to close it manually!")
        finally:
            await self.client.close()


async def main():
    # Initialize client
    client = VerdictClient(
        api_url="http://localhost:8000",
        cmc_api_key="YOUR_CMC_API_KEY",
        gemini_api_key="YOUR_GEMINI_API_KEY",
    )
    
    # Create and run bot
    bot = SimpleVerdictBot(client, confidence_threshold=75.0)
    await bot.run(token="BTC", portfolio_amount=1000.0)


if __name__ == "__main__":
    asyncio.run(main())
