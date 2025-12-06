"""
Position Manager for Perp DEX Trading
Tracks open positions, calculates PnL, and manages entry/exit
"""
from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PositionType(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class PositionManager:
    def __init__(self):
        self.positions = {}  # Track positions by user_id or session_id
    
    def calculate_leverage(self, risk_level: str, confidence: float, signal_strength: float) -> Dict:
        """
        Calculate leverage based on risk level, confidence, and signal strength
        """
        # Base leverage by risk level
        base_leverage = {
            RiskLevel.CONSERVATIVE: 3,
            RiskLevel.MODERATE: 5,
            RiskLevel.AGGRESSIVE: 10
        }.get(risk_level.lower(), RiskLevel.MODERATE)
        
        # Adjust based on confidence and signal strength
        confidence_multiplier = min(confidence / 100, 1.0)
        signal_multiplier = min(abs(signal_strength) / 50, 1.0)
        
        # Combined multiplier
        multiplier = (confidence_multiplier * 0.6) + (signal_multiplier * 0.4)
        
        # Calculate final leverage
        if risk_level.lower() == RiskLevel.AGGRESSIVE:
            suggested_leverage = int(base_leverage * (0.7 + multiplier * 0.6))  # 7x to 13x
            max_leverage = 15
        elif risk_level.lower() == RiskLevel.MODERATE:
            suggested_leverage = int(base_leverage * (0.6 + multiplier * 0.8))  # 3x to 9x
            max_leverage = 10
        else:  # Conservative
            suggested_leverage = int(base_leverage * (0.5 + multiplier * 1.0))  # 1.5x to 6x
            max_leverage = 5
        
        return {
            'suggested_leverage': min(suggested_leverage, max_leverage),
            'max_leverage': max_leverage,
            'base_leverage': base_leverage,
            'risk_level': risk_level
        }
    
    def calculate_margin_requirement(self, position_size: float, leverage: int) -> Dict:
        """
        Calculate margin requirement for a position
        Margin = Position Size / Leverage
        """
        margin_required = position_size / leverage
        available_for_trading = position_size - margin_required
        
        return {
            'margin_required': margin_required,
            'position_size': position_size,
            'leverage': leverage,
            'available_for_trading': available_for_trading
        }
    
    def should_open_position(self, recommendation: str, confidence: float, 
                           signal_score: float, current_position: Optional[Dict]) -> Dict:
        """
        Determine if we should open a new position
        """
        # Don't open if we already have a position
        if current_position and current_position.get('status') == 'open':
            return {
                'should_open': False,
                'reason': 'Position already open',
                'action': 'monitor'
            }
        
        # Only open if signal is strong enough (lowered for more opportunities)
        min_confidence = 60.0  # Lowered from 70.0
        min_signal = 15.0  # Lowered from 25.0
        
        if recommendation in ["LONG", "SHORT"]:
            if confidence >= min_confidence and abs(signal_score) >= min_signal:
                return {
                    'should_open': True,
                    'reason': f'Strong {recommendation} signal',
                    'action': f'OPEN_{recommendation}',
                    'confidence': confidence,
                    'signal_score': signal_score
                }
            else:
                return {
                    'should_open': False,
                    'reason': f'Signal not strong enough (Confidence: {confidence}%, Signal: {signal_score:.2f})',
                    'action': 'wait'
                }
        
        return {
            'should_open': False,
            'reason': 'HOLD signal - no position',
            'action': 'wait'
        }
    
    def should_close_position(self, current_position: Dict, current_price: float,
                            recommendation: str, signal_score: float) -> Dict:
        """
        Determine if we should close the current position
        """
        if not current_position or current_position.get('status') != 'open':
            return {
                'should_close': False,
                'reason': 'No open position'
            }
        
        entry_price = current_position.get('entry_price', 0)
        position_type = current_position.get('type')
        leverage = current_position.get('leverage', 1)
        collateral = current_position.get('collateral', 0)
        
        # Calculate current PnL
        if position_type == "LONG":
            price_change_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            price_change_pct = ((entry_price - current_price) / entry_price) * 100
        
        pnl_pct = price_change_pct * leverage
        pnl_usd = collateral * (pnl_pct / 100)
        
        # Exit conditions
        exit_conditions = []
        
        # 1. Take profit: +50% ROI
        if pnl_pct >= 50:
            exit_conditions.append('take_profit_50pct')
        
        # 2. Stop loss: -30% ROI
        if pnl_pct <= -30:
            exit_conditions.append('stop_loss_30pct')
        
        # 3. Signal reversal: Recommendation changed
        if position_type == "LONG" and recommendation == "SHORT":
            exit_conditions.append('signal_reversal_to_short')
        elif position_type == "SHORT" and recommendation == "LONG":
            exit_conditions.append('signal_reversal_to_long')
        
        # 4. Signal weakened: Score moved to HOLD zone
        if recommendation == "HOLD" and abs(signal_score) < 15:
            exit_conditions.append('signal_weakened')
        
        should_close = len(exit_conditions) > 0
        
        return {
            'should_close': should_close,
            'exit_conditions': exit_conditions,
            'current_pnl_pct': pnl_pct,
            'current_pnl_usd': pnl_usd,
            'entry_price': entry_price,
            'current_price': current_price,
            'price_change_pct': price_change_pct
        }
    
    def create_position(self, token: str, position_type: str, entry_price: float,
                       leverage: int, collateral: float, stablecoin: str) -> Dict:
        """
        Create a new position record
        """
        position_size = collateral * leverage
        
        position = {
            'token': token,
            'type': position_type,
            'status': 'open',
            'entry_price': entry_price,
            'current_price': entry_price,
            'leverage': leverage,
            'collateral': collateral,
            'position_size': position_size,
            'stablecoin': stablecoin,
            'opened_at': datetime.now().isoformat(),
            'pnl_usd': 0.0,
            'pnl_pct': 0.0
        }
        
        return position
    
    def update_position(self, position: Dict, current_price: float) -> Dict:
        """
        Update position with current price and calculate PnL
        """
        entry_price = position.get('entry_price', 0)
        position_type = position.get('type')
        leverage = position.get('leverage', 1)
        collateral = position.get('collateral', 0)
        
        if position_type == "LONG":
            price_change_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            price_change_pct = ((entry_price - current_price) / entry_price) * 100
        
        pnl_pct = price_change_pct * leverage
        pnl_usd = collateral * (pnl_pct / 100)
        
        position['current_price'] = current_price
        position['pnl_usd'] = round(pnl_usd, 2)
        position['pnl_pct'] = round(pnl_pct, 2)
        position['updated_at'] = datetime.now().isoformat()
        
        return position
    
    def close_position(self, position: Dict, exit_price: float, reason: str) -> Dict:
        """
        Close a position and calculate final PnL
        """
        position = self.update_position(position, exit_price)
        
        position['status'] = 'closed'
        position['exit_price'] = exit_price
        position['closed_at'] = datetime.now().isoformat()
        position['close_reason'] = reason
        
        return position

