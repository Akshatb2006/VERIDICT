"""
Flare Time Series Oracle (FTSO) Integration
Provides decentralized price feeds from Flare network
"""

import aiohttp
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FTSOPrice:
    """Represents a price from FTSO with metadata"""
    symbol: str
    price: float
    timestamp: int
    decimals: int
    provider: str
    confidence: float


class FTSOPriceFeed:
    """
    Flare Time Series Oracle (FTSO) - Decentralized price feeds
    Provides prices attested by multiple independent data providers
    """
    
    # FTSO contract addresses on Coston2 testnet
    FTSO_CONTRACTS = {
        "BTC/USD": "0x...",  # TODO: Add actual contract addresses
        "ETH/USD": "0x...",
        "FLR/USD": "0x...",
        "XRP/USD": "0x...",
        "DOGE/USD": "0x...",
    }
    
    def __init__(
        self,
        rpc_url: str = "https://coston2-api.flare.network/ext/C/rpc",
        network: str = "coston2"
    ):
        self.rpc_url = rpc_url
        self.network = network
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_price(self, symbol: str) -> FTSOPrice:
        """
        Get current price from FTSO
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            
        Returns:
            FTSOPrice with current price and metadata
        """
        logger.info(f"[FTSO] Requesting price for {symbol}")
        
        try:
            # Normalize symbol
            normalized_symbol = self._normalize_symbol(symbol)
            
            # Get price from FTSO API
            session = await self._get_session()
            
            async with session.get(
                f"https://fdc-api.flare.network/ftso/v1/price/{normalized_symbol}",
                timeout=5
            ) as response:
                if response.status != 200:
                    logger.error(f"[FTSO] Price request failed: {response.status}")
                    return self._create_fallback_price(symbol)
                
                data = await response.json()
                
                price_data = data.get("data", {})
                
                ftso_price = FTSOPrice(
                    symbol=symbol,
                    price=float(price_data.get("price", 0)) / (10 ** price_data.get("decimals", 0)),
                    timestamp=price_data.get("timestamp", int(datetime.now().timestamp())),
                    decimals=price_data.get("decimals", 2),
                    provider="FTSO",
                    confidence=price_data.get("confidence", 0.95)
                )
                
                logger.info(f"[FTSO] Price received: ${ftso_price.price:,.2f}")
                
                return ftso_price
                
        except Exception as e:
            logger.error(f"[FTSO] Error fetching price: {e}")
            return self._create_fallback_price(symbol)
    
    async def get_price_with_timestamp(self, symbol: str) -> Tuple[FTSOPrice, int]:
        """
        Get price with explicit timestamp
        
        Args:
            symbol: Trading pair
            
        Returns:
            Tuple of (FTSOPrice, timestamp)
        """
        price = await self.get_price(symbol)
        return (price, price.timestamp)
    
    async def verify_price_proof(self, symbol: str, claimed_price: float) -> bool:
        """
        Verify that a claimed price matches FTSO data
        
        Args:
            symbol: Trading pair
            claimed_price: Price to verify
            
        Returns:
            True if price is within acceptable range of FTSO price
        """
        try:
            ftso_price = await self.get_price(symbol)
            
            # Allow 1% deviation
            deviation = abs(ftso_price.price - claimed_price) / ftso_price.price
            
            if deviation < 0.01:  # 1% tolerance
                logger.info(f"[FTSO] Price verification passed for {symbol}")
                return True
            else:
                logger.warning(
                    f"[FTSO] Price verification failed - "
                    f"FTSO: ${ftso_price.price:.2f}, Claimed: ${claimed_price:.2f}"
                )
                return False
                
        except Exception as e:
            logger.error(f"[FTSO] Price verification error: {e}")
            return False
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to FTSO format
        
        Args:
            symbol: Input symbol (BTC, BTC/USD, etc.)
            
        Returns:
            Normalized symbol (BTC/USD)
        """
        symbol = symbol.upper().strip()
        
        # If already in pair format, return
        if "/" in symbol:
            return symbol
        
        # Default to USD pair
        return f"{symbol}/USD"
    
    def _create_fallback_price(self, symbol: str) -> FTSOPrice:
        """Create fallback price when FTSO fails"""
        return FTSOPrice(
            symbol=symbol,
            price=0.0,
            timestamp=int(datetime.now().timestamp()),
            decimals=2,
            provider="FTSO_FALLBACK",
            confidence=0.0
        )
    
    async def get_multiple_prices(self, symbols: list[str]) -> Dict[str, FTSOPrice]:
        """
        Get prices for multiple symbols
        
        Args:
            symbols: List of trading pairs
            
        Returns:
            Dictionary mapping symbol to FTSOPrice
        """
        results = {}
        
        for symbol in symbols:
            try:
                price = await self.get_price(symbol)
                results[symbol] = price
            except Exception as e:
                logger.error(f"[FTSO] Error fetching {symbol}: {e}")
                results[symbol] = self._create_fallback_price(symbol)
        
        return results
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
