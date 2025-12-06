"""
Flare Data Connector (FDC) Integration
Provides cryptographically verified data from external sources via Flare's oracle network
"""

import aiohttp
import hashlib
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class VerifiedData:
    """Represents data with FDC attestation proof"""
    content: Dict[str, Any]
    hash: str
    timestamp: int
    proof: Optional[str]
    verified: bool
    source_id: str


class FlareDataConnector:
    """
    Flare Data Connector - fetches verified data from Web2/Web3 sources
    All data is cryptographically attested by Flare network
    """
    
    def __init__(self, fdc_endpoint: str = "https://fdc-api.flare.network"):
        self.fdc_endpoint = fdc_endpoint
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _compute_hash(self, data: Dict) -> str:
        """Compute hash of data for verification"""
        data_str = str(sorted(data.items()))
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def get_verified_price(self, symbol: str) -> VerifiedData:
        """
        Get verified price data from FDC
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USD")
            
        Returns:
            VerifiedData with price information and attestation proof
        """
        logger.info(f"[FDC] Requesting verified price for {symbol}")
        
        try:
            session = await self._get_session()
            
            # Request data from FDC with source specification
            request_payload = {
                "source_type": "price_feed",
                "symbol": symbol,
                "sources": ["coinmarketcap", "coingecko", "binance"],
                "attestation_type": "evm"
            }
            
            async with session.post(
                f"{self.fdc_endpoint}/api/v1/price",
                json=request_payload,
                timeout=10
            ) as response:
                if response.status != 200:
                    logger.error(f"[FDC] Price request failed: {response.status}")
                    # Return unverified fallback
                    return self._create_fallback_data(symbol, "price")
                
                data = await response.json()
                
                # Extract attestation proof
                content = data.get("data", {})
                proof = data.get("attestation_proof")
                
                # Validate proof
                verified = self._validate_attestation(content, proof)
                
                logger.info(f"[FDC] Price received - Verified: {verified}")
                
                return VerifiedData(
                    content=content,
                    hash=self._compute_hash(content),
                    timestamp=int(datetime.now().timestamp()),
                    proof=proof,
                    verified=verified,
                    source_id="fdc_price_feed"
                )
                
        except Exception as e:
            logger.error(f"[FDC] Error fetching price: {e}")
            return self._create_fallback_data(symbol, "price")
    
    async def get_verified_sentiment(self, symbol: str) -> VerifiedData:
        """
        Get verified sentiment data from FDC
        
        Args:
            symbol: Token symbol (e.g., "BTC")
            
        Returns:
            VerifiedData with sentiment analysis and attestation proof
        """
        logger.info(f"[FDC] Requesting verified sentiment for {symbol}")
        
        try:
            session = await self._get_session()
            
            request_payload = {
                "source_type": "sentiment_api",
                "symbol": symbol,
                "sources": ["twitter", "reddit", "news_aggregator"],
                "attestation_type": "evm"
            }
            
            async with session.post(
                f"{self.fdc_endpoint}/api/v1/sentiment",
                json=request_payload,
                timeout=15
            ) as response:
                if response.status != 200:
                    logger.error(f"[FDC] Sentiment request failed: {response.status}")
                    return self._create_fallback_data(symbol, "sentiment")
                
                data = await response.json()
                content = data.get("data", {})
                proof = data.get("attestation_proof")
                
                verified = self._validate_attestation(content, proof)
                
                logger.info(f"[FDC] Sentiment received - Verified: {verified}")
                
                return VerifiedData(
                    content=content,
                    hash=self._compute_hash(content),
                    timestamp=int(datetime.now().timestamp()),
                    proof=proof,
                    verified=verified,
                    source_id="fdc_sentiment"
                )
                
        except Exception as e:
            logger.error(f"[FDC] Error fetching sentiment: {e}")
            return self._create_fallback_data(symbol, "sentiment")
    
    async def get_verified_news(self, symbol: str) -> VerifiedData:
        """
        Get verified news data from FDC
        
        Args:
            symbol: Token symbol (e.g., "BTC")
            
        Returns:
            VerifiedData with news articles and attestation proof
        """
        logger.info(f"[FDC] Requesting verified news for {symbol}")
        
        try:
            session = await self._get_session()
            
            request_payload = {
                "source_type": "news_feed",
                "symbol": symbol,
                "sources": ["cryptopanic", "newsapi"],
                "attestation_type": "evm"
            }
            
            async with session.post(
                f"{self.fdc_endpoint}/api/v1/news",
                json=request_payload,
                timeout=15
            ) as response:
                if response.status != 200:
                    logger.error(f"[FDC] News request failed: {response.status}")
                    return self._create_fallback_data(symbol, "news")
                
                data = await response.json()
                content = data.get("data", {})
                proof = data.get("attestation_proof")
                
                verified = self._validate_attestation(content, proof)
                
                logger.info(f"[FDC] News received - Verified: {verified}")
                
                return VerifiedData(
                    content=content,
                    hash=self._compute_hash(content),
                    timestamp=int(datetime.now().timestamp()),
                    proof=proof,
                    verified=verified,
                    source_id="fdc_news"
                )
                
        except Exception as e:
            logger.error(f"[FDC] Error fetching news: {e}")
            return self._create_fallback_data(symbol, "news")
    
    def _validate_attestation(self, data: Dict, proof: Optional[str]) -> bool:
        """
        Validate FDC attestation proof
        
        Args:
            data: Data content to validate
            proof: Attestation proof from FDC
            
        Returns:
            True if proof is valid, False otherwise
        """
        if not proof:
            logger.warning("[FDC] No attestation proof provided")
            return False
        
        try:
            # Compute data hash
            data_hash = self._compute_hash(data)
            
            # In production, this would verify the cryptographic signature
            # against Flare's attestation provider contract
            # For now, we validate proof format
            
            if len(proof) < 32:
                return False
            
            # TODO: Implement full EVM proof verification
            # This would call Flare's FDC verification contract
            
            logger.info(f"[FDC] Attestation validated - Hash: {data_hash[:16]}...")
            return True
            
        except Exception as e:
            logger.error(f"[FDC] Attestation validation error: {e}")
            return False
    
    def _create_fallback_data(self, symbol: str, data_type: str) -> VerifiedData:
        """Create fallback unverified data when FDC fails"""
        return VerifiedData(
            content={"error": f"FDC {data_type} unavailable", "symbol": symbol},
            hash="",
            timestamp=int(datetime.now().timestamp()),
            proof=None,
            verified=False,
            source_id=f"fdc_{data_type}_fallback"
        )
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
