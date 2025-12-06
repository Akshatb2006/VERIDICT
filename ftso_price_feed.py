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
    
    # Flare Contract Registry on Coston2 (THE authoritative registry)
    FLARE_CONTRACT_REGISTRY = "0x1000000000000000000000000000000000000002"
    
    # Feed names (not IDs - we'll hash them)
    FEED_NAMES = {
        "BTC": "BTC/USD",
        "ETH": "ETH/USD",
        "FLR": "FLR/USD",
        "XRP": "XRP/USD",
        "DOGE": "DOGE/USD",
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
        self.registry_contract = None
        self.ftso_cache = {}  # Cache resolved FTSO contracts
    
    async def _init_web3(self):
        """Initialize Web3 connection to Coston2"""
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
            
            logger.info(f"[FTSO] Connected to Flare Coston2 (Chain ID: {chain_id})")
            
            # Initialize Flare Contract Registry
            # Minimal ABI - just what we need
            registry_abi = [{
                "inputs": [{"name": "_name", "type": "string"}],
                "name": "getContractAddressByName",
                "outputs": [{"type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }]
            
            self.registry_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.FLARE_CONTRACT_REGISTRY),
                abi=registry_abi
            )
            
            logger.info(f"[FTSO] Flare Contract Registry initialized at {self.FLARE_CONTRACT_REGISTRY}")
    
    async def _get_ftso_contract(self, feed_name: str):
        """Dynamically resolve FTSO contract for a given feed"""
        if feed_name in self.ftso_cache:
            return self.ftso_cache[feed_name]
        
        # Hash the feed name (e.g., "BTC/USD") to get feed ID
        from web3 import Web3
        feed_id = Web3.keccak(text=feed_name)
        
        # Query registry for FTSO contract address
        try:
            ftso_address = self.registry_contract.functions.getContractAddressByName(
                feed_name
            ).call()
            
            if ftso_address == "0x0000000000000000000000000000000000000000":
                raise ValueError(f"Feed '{feed_name}' not found in registry")
            
            # FTSOv2 ABI - getCurrentPrice and getCurrentPriceWithDecimals
            ftso_abi = [
                {
                    "inputs": [],
                    "name": "getCurrentPrice",
                    "outputs": [{"type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "getCurrentPriceWithDecimals",
                    "outputs": [
                        {"name": "price", "type": "uint256"},
                        {"name": "timestamp", "type": "uint256"},
                        {"name": "decimals", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            ftso_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(ftso_address),
                abi=ftso_abi
            )
            
            self.ftso_cache[feed_name] = ftso_contract
            logger.info(f"[FTSO] Resolved {feed_name} → {ftso_address}")
            
            return ftso_contract
            
        except Exception as e:
            logger.error(f"[FTSO] Failed to resolve {feed_name}: {e}")
            raise
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def get_price(self, symbol: str) -> FTSOPrice:
        """
        Get REAL price from FTSO v2 contract (Phase 5 - FIXED)
        
        Args:
            symbol: Trading pair base (e.g., "BTC", "ETH")
            
        Returns:
            FTSOPrice with actual validator price
        """
        logger.info(f"[FTSO] Requesting REAL price for {symbol}")
        
        try:
            # Initialize Web3 if needed
            await self._init_web3()
            
            # Get feed name
            symbol_clean = symbol.upper().replace("/USD", "").replace("USD", "").strip()
            feed_name = self.FEED_NAMES.get(symbol_clean)
            
            if not feed_name:
                logger.warning(f"[FTSO] No feed for {symbol_clean}, using fallback")
                return self._create_fallback_price(symbol)
            
            # Dynamically resolve FTSO contract for this feed
            ftso_contract = await self._get_ftso_contract(feed_name)
            
            # Call getCurrentPriceWithDecimals() - returns (price, timestamp, decimals)
            price_data = ftso_contract.functions.getCurrentPriceWithDecimals().call()
            price_value = price_data[0]
            timestamp = price_data[1]
            decimals = price_data[2]
            
            # Calculate actual price
            real_price = float(price_value) / (10 ** decimals)
            
            ftso_price = FTSOPrice(
                symbol=symbol,
                price=real_price,
                timestamp=timestamp,
                decimals=decimals,
                provider="FTSO_V2_REAL",
                confidence=0.99
            )
            
            logger.info(f"[FTSO] ✅ REAL price from Flare validators: ${ftso_price.price:,.2f}")
            
            return ftso_price
            
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
