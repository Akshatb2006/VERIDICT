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
    
    # Flare PriceReader System Contract (Coston2) - THE authoritative source!
    PRICE_READER_ADDRESS = "0x1000000000000000000000000000000000000003"
    
    # Asset IDs for FTSO feeds on Coston2
    ASSET_IDS = {
        "BTC": 1,
        "ETH": 2,
        "XRP": 3,
        "DOGE": 4,
        "ADA": 5,
        "FLR": 6,
    }
    
    def __init__(
        self,
        rpc_url: str = "https://coston2-api.flare.network/ext/C/rpc",
        network: str = "coston2"
    ):
        self.rpc_url = rpc_url
        self.network = network
        self.session: Optional[aiohttp.ClientSession] = None
        self.w3 = None
        self.price_reader = None  # PriceReader contract
    
    async def _init_web3(self):
        """Initialize Web3 connection and PriceReader contract"""
        # STEP 1: Initialize Web3 if needed
        if self.w3 is None:
            from web3 import Web3
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Verify connection
            if not self.w3.is_connected():
                raise ConnectionError(f"Cannot connect to Flare RPC: {self.rpc_url}")
            
            # Verify chain ID (Coston2 = 114)
            chain_id = self.w3.eth.chain_id
            if chain_id != 114:
                logger.warning(f"[FTSO] Chain ID is {chain_id}, expected 114 for Coston2")
            
            logger.info(f"[FTSO] ✅ Connected to Flare Coston2 (Chain ID: {chain_id})")
        
        # STEP 2: Initialize PriceReader if needed
        if self.price_reader is None:
            from web3 import Web3
            
            # PriceReader ABI - simple and direct!
            price_reader_abi = [{
                "inputs": [{"name": "_asset", "type": "uint256"}],
                "name": "getCurrentPrice",
                "outputs": [
                    {"name": "price", "type": "uint256"},
                    {"name": "timestamp", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]
            
            self.price_reader = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.PRICE_READER_ADDRESS),
                abi=price_reader_abi
            )
            
            logger.info(f"[FTSO] ✅ PriceReader initialized at {self.PRICE_READER_ADDRESS}")
    
    async def _get_ftso_price(self, symbol: str):
        """Get price from PriceReader for a given symbol"""
        try:
            # Get asset ID
            symbol_clean = symbol.upper().replace("/USD", "").replace("USD", "").strip()
            asset_id = self.ASSET_IDS.get(symbol_clean)
            
            if asset_id is None:
                raise ValueError(f"No asset ID for {symbol_clean}")
            
            logger.info(f"[FTSO] Querying PriceReader for {symbol_clean} (Asset ID: {asset_id})")
            
            # Call getCurrentPrice - returns (price, timestamp)
            price_value, timestamp = self.price_reader.functions.getCurrentPrice(asset_id).call()
            
            # FTSO uses 5 decimals
            real_price = float(price_value) / 100000
            
            logger.info(f"[FTSO] ✅ REAL price from Flare validators: {symbol_clean} = ${real_price:,.2f} (ts: {timestamp})")
            
            return FTSOPrice(
                symbol=symbol,
                price=real_price,
                timestamp=timestamp,
                decimals=5,  # FTSO standard
                provider="FTSO_PRICEREADER_COSTON2",
                confidence=0.99
            )
            
        except Exception as e:
            logger.error(f"[FTSO] Error getting price for {symbol}: {e}")
            raise
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def get_price(self, symbol: str) -> FTSOPrice:
        """
        Get REAL price from FTSO via FtsoRegistry (Phase 5 - FIXED)
        
        Args:
            symbol: Trading pair base (e.g., "BTC", "ETH")
            
        Returns:
            FTSOPrice with actual validator price
        """
        logger.info(f"[FTSO] Requesting REAL price for {symbol}")
        
        try:
            # Initialize Web3 and FtsoRegistry if needed
            await self._init_web3()
            
            # Get price from FtsoRegistry
            return await self._get_ftso_price(symbol)
            
        except Exception as e:
            logger.error(f"[FTSO] Error fetching REAL price: {e}")
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
