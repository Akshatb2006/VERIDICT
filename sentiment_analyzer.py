"""
Google Gemini-powered sentiment analysis for tokens
"""
import os
import google.generativeai as genai
from typing import Dict, Optional
import json
from datetime import datetime


class SentimentAnalyzer:
    def __init__(self, api_key: str):
        # Configure Gemini with API key
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash for speed and real-time trading analysis
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_token_sentiment(self, token_symbol: str, token_name: str, 
                                market_data: Dict) -> Dict:
        """
        Analyze sentiment for a token based on market data and generate insights
        """
        try:
            import time
            request_start = time.time()
            print(f"[Gemini API] Making sentiment analysis call for {token_symbol} at {datetime.now().isoformat()}")
            print(f"[Gemini API] Market data - Price: ${market_data.get('price', 0):.4f}, 24h: {market_data.get('percent_change_24h', 0):.2f}%")
            
            # Create a comprehensive prompt for sentiment analysis
            prompt = f"""
            Analyze the sentiment for {token_name} ({token_symbol}) based on the following market data:
            
            Current Price: ${market_data.get('price', 0):,.2f}
            1h Change: {market_data.get('percent_change_1h', 0):.2f}%
            24h Change: {market_data.get('percent_change_24h', 0):.2f}%
            7d Change: {market_data.get('percent_change_7d', 0):.2f}%
            Market Cap: ${market_data.get('market_cap', 0):,.0f}
            24h Volume: ${market_data.get('volume_24h', 0):,.0f}
            
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
            
            # Extract and parse JSON from response
            content = response.text.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]   # Remove ```
            if content.endswith("```"):
                content = content[:-3]   # Remove closing ```
            content = content.strip()
            
            # Parse JSON
            result = json.loads(content)
            
            request_time = time.time() - request_start
            print(f"[Gemini API] Response received in {request_time:.2f}s - Sentiment: {result.get('overall_sentiment', 0):.2f}, Risk: {result.get('risk_level', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            # Return neutral sentiment on error
            return {
                "overall_sentiment": 0,
                "short_term_sentiment": 0,
                "medium_term_sentiment": 0,
                "key_factors": ["Data unavailable"],
                "risk_level": "Medium",
                "reasoning": f"Error occurred: {str(e)}"
            }
    
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
        
        # Weighted scoring
        score = (overall_sentiment * 0.4) + (short_term * 0.3) + (price_change_24h * 0.2) + (price_change_1h * 0.1)
        
        # Risk adjustment
        if risk_level == "High":
            score *= 0.7  # Reduce confidence for high risk
        elif risk_level == "Low":
            score *= 1.1  # Slightly increase confidence for low risk
        
        # Generate recommendation
        if score > 30:
            return "LONG"
        elif score < -30:
            return "SHORT"
        else:
            return "HOLD"
