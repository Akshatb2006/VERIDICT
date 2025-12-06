"""
Decision engine that combines market data, sentiment, and on-chain signals
to generate trading recommendations for perpetual DEX
"""
from typing import Dict, Tuple
import json


class DecisionEngine:
    def __init__(self):
        # Weight configuration for different signals
        self.weights = {
            'sentiment': 0.35,      # AI sentiment analysis
            'market_momentum': 0.30, # Price movements and volume
            'onchain': 0.20,        # On-chain activity
            'risk': 0.15            # Risk assessment
        }
    
    def calculate_signal(self, market_data: Dict, sentiment_data: Dict, 
                        onchain_data: Dict) -> Dict:
        """
        Calculate final trading signal by combining all inputs
        """
        # Extract key metrics
        sentiment_score = sentiment_data.get('overall_sentiment', 0)
        short_term_sentiment = sentiment_data.get('short_term_sentiment', 0)
        risk_level = sentiment_data.get('risk_level', 'Medium')
        
        # Market momentum calculation (more sensitive)
        price_change_24h = market_data.get('percent_change_24h', 0)
        price_change_1h = market_data.get('percent_change_1h', 0)
        volume_24h = market_data.get('volume_24h', 0)
        
        # Normalize volume (assuming typical volume range)
        volume_score = min(volume_24h / 10000000, 1.0) * 100  # Scale to 0-100
        
        # Market momentum score (amplified for better signals)
        # Multiply by 1.5 to make price movements more impactful
        market_momentum = ((price_change_24h * 0.6) + (price_change_1h * 0.4)) * 1.5
        
        # On-chain signal
        onchain_signal = onchain_data.get('onchain_signal', 0)
        
        # Risk adjustment
        risk_multiplier = {
            'Low': 1.2,
            'Medium': 1.0,
            'High': 0.7
        }.get(risk_level, 1.0)
        
        # Calculate weighted final score
        sentiment_component = (sentiment_score * 0.6 + short_term_sentiment * 0.4) * self.weights['sentiment']
        momentum_component = market_momentum * self.weights['market_momentum']
        onchain_component = onchain_signal * self.weights['onchain']
        
        # Combine all signals
        final_score = (sentiment_component + momentum_component + onchain_component) * risk_multiplier
        
        # Determine recommendation (extremely sensitive - almost always shows signal)
        # LONG: score > 0.5 (reduced from 3 to account for weighted calculation)
        # SHORT: score < -0.5 (reduced from -3 to account for weighted calculation)
        if final_score > 0.5:
            recommendation = "LONG"
            confidence = min(abs(final_score) / 10, 1.0)  # Adjusted for new threshold
        elif final_score < -0.5:
            recommendation = "SHORT"
            confidence = min(abs(final_score) / 10, 1.0)  # Adjusted for new threshold
        else:
            recommendation = "HOLD"
            confidence = 1.0 - (abs(final_score) / 0.5)  # Adjusted for new threshold
        
        # Calculate position sizing suggestion (for perp DEX)
        leverage_suggestion = self._suggest_leverage(confidence, risk_level)
        
        return {
            'recommendation': recommendation,
            'confidence': round(confidence * 100, 2),
            'final_score': round(final_score, 2),
            'signal_breakdown': {
                'sentiment_score': round(sentiment_score, 2),
                'market_momentum': round(market_momentum, 2),
                'onchain_signal': round(onchain_signal, 2),
                'risk_level': risk_level
            },
            'leverage_suggestion': leverage_suggestion,
            'reasoning': self._generate_reasoning(recommendation, final_score, 
                                                 sentiment_data, market_data, onchain_data)
        }
    
    def _suggest_leverage(self, confidence: float, risk_level: str) -> Dict:
        """
        Suggest appropriate leverage based on confidence and risk
        For perp DEX, leverage typically ranges from 1x to 100x+
        """
        base_leverage = {
            'Low': 10,
            'Medium': 5,
            'High': 2
        }.get(risk_level, 5)
        
        # Adjust based on confidence
        if confidence > 0.8:
            suggested_leverage = min(base_leverage * 2, 20)
        elif confidence > 0.6:
            suggested_leverage = base_leverage
        else:
            suggested_leverage = max(base_leverage // 2, 1)
        
        return {
            'suggested_leverage': suggested_leverage,
            'max_safe_leverage': base_leverage * 2,
            'warning': 'High leverage increases risk. Only use what you can afford to lose.'
        }
    
    def _generate_reasoning(self, recommendation: str, score: float,
                           sentiment_data: Dict, market_data: Dict, 
                           onchain_data: Dict) -> str:
        """Generate human-readable reasoning for the recommendation"""
        factors = sentiment_data.get('key_factors', [])
        price_change = market_data.get('percent_change_24h', 0)
        
        reasoning_parts = [
            f"Overall signal score: {score:.2f}",
            f"24h price change: {price_change:.2f}%",
        ]
        
        if factors:
            reasoning_parts.append(f"Key factors: {', '.join(factors[:3])}")
        
        risk = sentiment_data.get('risk_level', 'Medium')
        reasoning_parts.append(f"Risk level: {risk}")
        
        return " | ".join(reasoning_parts)

