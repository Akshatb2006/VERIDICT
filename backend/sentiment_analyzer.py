"""
Google Gemini-powered sentiment analysis for tokens with Flare FDC verification
"""
import os
import google.generativeai as genai
from typing import Dict, Optional
import json
from datetime import datetime


class SentimentAnalyzer:
    def __init__(self, api_key: str, fdc_connector=None):
        # Configure Gemini with API key
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash for speed and real-time trading analysis
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Flare Data Connector for verification
        self.fdc = fdc_connector
    
    async def analyze_token_sentiment(self, token_symbol: str, token_name: str, 
                                market_data: Dict, verified_data=None) -> Dict:
        """
        Analyze sentiment for a token based on verified market data
        
        Args:
            token_symbol: Token symbol (e.g., "BTC")
            token_name: Full token name
            market_data: Market data dictionary
            verified_data: Optional VerifiedData from FDC
            
        Returns:
            Sentiment analysis with verification metadata
        """
        try:
            import time
            request_start = time.time()
            print(f"[Gemini API] Making sentiment analysis call for {token_symbol} at {datetime.now().isoformat()}")
            print(f"[Gemini API] Market data - Price: ${market_data.get('price', 0):.4f}, 24h: {market_data.get('percent_change_24h', 0):.2f}%")
            
            # If FDC verification available, include it in analysis
            verification_context = ""
            if verified_data and verified_data.verified:
                verification_context = f"""
                NOTE: This data has been cryptographically verified by Flare Data Connector (FDC).
                Verification Hash: {verified_data.hash[:16]}...
                Data is attestation-backed and tamper-proof.
                """
            
            # Create a comprehensive prompt for sentiment analysis
            prompt = f"""
            Analyze the sentiment for {token_name} ({token_symbol}) based on the following market data:
            
            Current Price: ${market_data.get('price', 0):,.2f}
            1h Change: {market_data.get('percent_change_1h', 0):.2f}%
            24h Change: {market_data.get('percent_change_24h', 0):.2f}%
            7d Change: {market_data.get('percent_change_7d', 0):.2f}%
            Market Cap: ${market_data.get('market_cap', 0):,.0f}
            24h Volume: ${market_data.get('volume_24h', 0):,.0f}
            
            {verification_context}
            
            Based on this data, provide:
            1. Overall sentiment score (-100 to +100, where -100 is very bearish, +100 is very bullish)
            2. Short-term sentiment (next 1-4 hours)
            3. Medium-term sentiment (next 24 hours)
            4. Key factors influencing the sentiment
            5. Risk assessment (Low/Medium/High)
            
            Respond ONLY with a valid JSON object (no markdown, no extra text) in this exact format:
            {{
                "overall_sentiment": <number>,
                "short_term_sentiment": <number>,
                "medium_term_sentiment": <number>,
                "key_factors": ["factor1", "factor2"],
                "risk_level": "Low|Medium|High",
                "reasoning": "brief explanation"
            }}
            """
            
            # Generate content with Gemini
            response = self.model.generate_content(prompt)
            
            request_time = time.time() - request_start
            print(f"[Gemini API] Response received in {request_time:.2f}s", end="")
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            try:
                sentiment_data = json.loads(response_text)
                print(f" - Sentiment: {sentiment_data.get('overall_sentiment', 0):.2f}, Risk: {sentiment_data.get('risk_level', 'Unknown')}")
                
                # Add verification metadata
                if verified_data:
                    sentiment_data["fdc_verified"] = verified_data.verified
                    sentiment_data["fdc_hash"] = verified_data.hash
                    sentiment_data["fdc_timestamp"] = verified_data.timestamp
                else:
                    sentiment_data["fdc_verified"] = False
                    sentiment_data["fdc_hash"] = None
                    sentiment_data["fdc_timestamp"] = None
                
                return sentiment_data
                
            except json.JSONDecodeError:
                # Fallback parsing
                print(f" - Failed to parse JSON, using fallback")
                sentiment_score = self._extract_sentiment_from_text(response_text)
                
                return {
                    "overall_sentiment": sentiment_score,
                    "short_term_sentiment": sentiment_score,
                    "medium_term_sentiment": sentiment_score,
                    "key_factors": ["Price momentum", "Market conditions"],
                    "risk_level": "Medium",
                    "reasoning": "Automated analysis based on market data",
                    "fdc_verified": verified_data.verified if verified_data else False,
                    "fdc_hash": verified_data.hash if verified_data else None,
                    "fdc_timestamp": verified_data.timestamp if verified_data else None
                }
                
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {
                "overall_sentiment": 0.0,
                "short_term_sentiment": 0.0,
                "medium_term_sentiment": 0.0,
                "key_factors": [],
                "risk_level": "Unknown",
                "reasoning": f"Error: {str(e)}",
                "fdc_verified": False,
                "fdc_hash": None,
                "fdc_timestamp": None
            }
    
    def _extract_sentiment_from_text(self, text: str) -> float:
        """Extract sentiment score from text response (fallback)"""
        # Simple keyword-based sentiment extraction
        positive_keywords = ['bullish', 'positive', 'strong', 'growth', 'upward']
        negative_keywords = ['bearish', 'negative', 'weak', 'decline', 'downward']
        
        text_lower = text.lower()
        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        if pos_count > neg_count:
            return 50.0
        elif neg_count > pos_count:
            return -50.0
        else:
            return 0.0
    
    def get_trading_recommendation(self, sentiment_data: Dict, 
                                   market_data: Dict) -> str:
        """
        Generate trading recommendation based on sentiment and market data
        """
        overall_sentiment = sentiment_data.get('overall_sentiment', 0)
        short_term = sentiment_data.get('short_term_sentiment', 0)
        risk_level = sentiment_data.get('risk_level', 'Medium')
        
        # Combine sentiment scores with market momentum
        price_change_24h = market_data.get('percent_change_24h', 0)
        price_change_1h = market_data.get('percent_change_1h', 0)
        
        # Use overall sentiment directly (it's already on -100 to +100 scale)
        # Apply a simple threshold for extremely dynamic signals
        score = overall_sentiment
        
        # Generate recommendation (sentiment-based with low thresholds)
        if score > 5:
            return "LONG"
        elif score < -5:
            return "SHORT"
        else:
            return "HOLD"
