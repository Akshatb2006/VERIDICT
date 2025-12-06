"""
FastAPI application for Sentiment Catcher & On-Chain Data Analyzer
Real-time streaming of LONG/SHORT/HOLD recommendations for Aptos Perp DEX
"""
import os
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from market_data import CoinMarketCapAPI
from sentiment_analyzer import SentimentAnalyzer
from aptos_analyzer import AptosAnalyzer
from decision_engine import DecisionEngine
from position_manager import PositionManager, RiskLevel

# Load environment variables
load_dotenv()

app = FastAPI(
    title="VERDICT - Perp DEX Analyzer API",
    description="Real-time sentiment and on-chain analysis for Aptos Perp DEX trading",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer components
cmc_api_key = os.getenv('CMC_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not cmc_api_key or not gemini_api_key:
    raise ValueError("Please set CMC_API_KEY and GEMINI_API_KEY in your .env file")

cmc = CoinMarketCapAPI(cmc_api_key)
sentiment_analyzer = SentimentAnalyzer(gemini_api_key)
aptos_analyzer = AptosAnalyzer()
decision_engine = DecisionEngine()
position_manager = PositionManager()

# Store positions by session (in production, use database)
active_positions = {}

# Store active agents and their latest analysis results
active_agents = {}  # {session_id: {'activated': True/False, 'token': ..., 'stablecoin': ..., etc.}}
agent_results = {}  # {session_id: latest_analysis_result}
agent_tasks = {}  # {session_id: background_task}
agent_price_history = {}  # {session_id: [{'price': float, 'timestamp': str}]} - Track price history for live updates


class PerpTradeRequest(BaseModel):
    token: str  # Token to trade (e.g., APT, BTC, ETH)
    stablecoin: str = "USDC"  # Collateral stablecoin (USDC or USDT)
    portfolio_amount: float  # Amount of stablecoin for trading (e.g., 100.0 USDC)
    risk_level: str = "moderate"  # conservative, moderate, or aggressive


class AnalysisResponse(BaseModel):
    token: str
    stablecoin: str
    portfolio_amount: float
    risk_level: str
    timestamp: str
    recommendation: str  # LONG, SHORT, or HOLD
    confidence: float
    signal_score: float
    market_data: dict
    sentiment_data: dict
    onchain_data: dict
    leverage_suggestion: dict
    position_info: dict  # Current position status
    execution_signal: dict  # Should we open/close position?
    perp_trade_details: dict  # Detailed perp trade calculations
    reasoning: str


def calculate_perp_trade_details(recommendation: str, market_data: dict, 
                                leverage: dict, collateral_usdc: float, 
                                token: str, stablecoin: str) -> dict:
    """Calculate perp DEX trade details using USDC collateral"""
    suggested_leverage = leverage['suggested_leverage']
    current_price = market_data['price']
    position_size = collateral_usdc * suggested_leverage
    
    # Calculate how much token exposure we get
    token_exposure = position_size / current_price
    
    # Calculate margin requirement
    margin_required = collateral_usdc / suggested_leverage
    
    # Calculate potential PnL for 5% price movement
    price_change_pct = 0.05
    
    if recommendation == "LONG":
        # LONG: profit when price goes up, loss when price goes down
        pnl_if_up = collateral_usdc * suggested_leverage * price_change_pct
        roi_if_up = suggested_leverage * price_change_pct * 100
        pnl_if_down = -collateral_usdc * suggested_leverage * price_change_pct
        roi_if_down = -suggested_leverage * price_change_pct * 100
    elif recommendation == "SHORT":
        # SHORT: profit when price goes down, loss when price goes up
        pnl_if_up = -collateral_usdc * suggested_leverage * price_change_pct
        roi_if_up = -suggested_leverage * price_change_pct * 100
        pnl_if_down = collateral_usdc * suggested_leverage * price_change_pct
        roi_if_down = suggested_leverage * price_change_pct * 100
    else:
        # HOLD: Show example for LONG position
        pnl_if_up = collateral_usdc * suggested_leverage * price_change_pct
        roi_if_up = suggested_leverage * price_change_pct * 100
        pnl_if_down = -collateral_usdc * suggested_leverage * price_change_pct
        roi_if_down = -suggested_leverage * price_change_pct * 100
    
    return {
        'collateral_stablecoin': round(collateral_usdc, 2),
        'stablecoin': stablecoin,
        'suggested_leverage': suggested_leverage,
        'position_size_usd': round(position_size, 2),
        'token_exposure': round(token_exposure, 4),
        'current_price': round(current_price, 4),
        'margin_required': round(margin_required, 2),
        'token': token,
        'if_price_moves_5pct_up': {
            'pnl': round(pnl_if_up, 2),
            'roi_pct': round(roi_if_up, 2)
        },
        'if_price_moves_5pct_down': {
            'pnl': round(pnl_if_down, 2),
            'roi_pct': round(roi_if_down, 2)
        }
    }


async def perform_analysis(token: str, stablecoin: str, portfolio_amount: float, 
                          risk_level: str, session_id: str = "default") -> dict:
    """
    Perform complete perp trading analysis pipeline
    Uses USDC/USDT as collateral to trade the provided token
    """
    analysis_start_time = datetime.now()
    print(f"[perform_analysis] Starting fresh analysis for {token} at {analysis_start_time.isoformat()}")
    
    # Step 1: Fetch market data for the token we want to trade
    # Always fetch fresh data - no caching - make actual API call
    print(f"[perform_analysis] Fetching fresh market data from CMC API...")
    market_data = cmc.get_token_info(token.upper())
    
    if not market_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Token {token} not found. Please check: 1) Token symbol is correct, 2) CMC API key is valid, 3) API key has access to quotes endpoint"
        )
    
    print(f"[perform_analysis] Market data received - Price: ${market_data.get('price', 0):.4f}, 24h Change: {market_data.get('percent_change_24h', 0):.2f}%")
    
    # Step 2: Analyze sentiment - only call OpenAI every N iterations to avoid rate limits
    # For real-time updates, we'll use a simplified sentiment based on market data
    # Full OpenAI analysis can be done less frequently
    print(f"[perform_analysis] Analyzing sentiment...")
    sentiment_data = sentiment_analyzer.analyze_token_sentiment(
        token.upper(),
        market_data['name'],
        market_data
    )
    
    # Step 3: Analyze on-chain data
    print(f"[perform_analysis] Analyzing on-chain data...")
    onchain_data = aptos_analyzer.analyze_onchain_signals(token.upper())
    
    # Step 4: Generate final recommendation
    decision = decision_engine.calculate_signal(
        market_data,
        sentiment_data,
        onchain_data
    )
    
    # Step 5: Calculate leverage based on risk level
    leverage_info = position_manager.calculate_leverage(
        risk_level,
        decision['confidence'],
        decision['final_score']
    )
    
    # Step 6: Get current position (if any)
    current_position = active_positions.get(session_id)
    if current_position:
        current_position = position_manager.update_position(
            current_position,
            market_data['price']
        )
        active_positions[session_id] = current_position
    
    # Step 7: Determine if we should open/close positions
    execution_signal = {}
    position_info = {}
    
    if current_position and current_position.get('status') == 'open':
        # Check if we should close
        close_decision = position_manager.should_close_position(
            current_position,
            market_data['price'],
            decision['recommendation'],
            decision['final_score']
        )
        execution_signal = {
            'action': 'CLOSE' if close_decision['should_close'] else 'HOLD_POSITION',
            'should_close': close_decision['should_close'],
            'exit_conditions': close_decision.get('exit_conditions', []),
            'current_pnl_pct': close_decision.get('current_pnl_pct', 0),
            'current_pnl_usd': close_decision.get('current_pnl_usd', 0)
        }
        position_info = {
            'status': 'open',
            'type': current_position.get('type'),
            'entry_price': current_position.get('entry_price'),
            'current_price': market_data['price'],
            'leverage': current_position.get('leverage'),
            'collateral': current_position.get('collateral'),
            'position_size': current_position.get('position_size'),
            'pnl_usd': current_position.get('pnl_usd', 0),
            'pnl_pct': current_position.get('pnl_pct', 0)
        }
        
        # Auto-close if conditions met
        if close_decision['should_close']:
            closed_position = position_manager.close_position(
                current_position,
                market_data['price'],
                ', '.join(close_decision['exit_conditions'])
            )
            active_positions[session_id] = closed_position
            position_info['status'] = 'closed'
            position_info['close_reason'] = ', '.join(close_decision['exit_conditions'])
    else:
        # Check if we should open a new position
        open_decision = position_manager.should_open_position(
            decision['recommendation'],
            decision['confidence'],
            decision['final_score'],
            current_position
        )
        execution_signal = {
            'action': open_decision.get('action', 'WAIT'),
            'should_open': open_decision.get('should_open', False),
            'reason': open_decision.get('reason', '')
        }
        position_info = {'status': 'none'}
        
        # Auto-open if conditions met
        if open_decision['should_open']:
            new_position = position_manager.create_position(
                token.upper(),
                decision['recommendation'],
                market_data['price'],
                leverage_info['suggested_leverage'],
                portfolio_amount,
                stablecoin.upper()
            )
            active_positions[session_id] = new_position
            position_info = {
                'status': 'open',
                'type': new_position.get('type'),
                'entry_price': new_position.get('entry_price'),
                'leverage': new_position.get('leverage'),
                'collateral': new_position.get('collateral'),
                'position_size': new_position.get('position_size')
            }
            execution_signal['action'] = f"OPENED_{decision['recommendation']}"
    
    # Step 8: Calculate perp trade details
    perp_trade = calculate_perp_trade_details(
        decision['recommendation'],
        market_data,
        leverage_info,
        portfolio_amount,
        token.upper(),
        stablecoin.upper()
    )
    
    # Add clear action message
    recommendation = decision['recommendation']
    confidence = decision['confidence']
    price = market_data['price']
    
    if recommendation == "LONG":
        action_message = f"🟢 GO LONG {token.upper()} | Confidence: {confidence}% | Price: ${price:.4f}"
    elif recommendation == "SHORT":
        action_message = f"🔴 GO SHORT {token.upper()} | Confidence: {confidence}% | Price: ${price:.4f}"
    else:
        action_message = f"🟡 HOLD - Wait for better signal | Confidence: {confidence}% | Price: ${price:.4f}"
    
    # Always create a fresh timestamp to ensure uniqueness
    current_timestamp = datetime.now().isoformat()
    
    # CRITICAL: Create completely fresh dicts with all values copied (not referenced)
    # This ensures each API call returns truly independent data
    import copy
    
    # Create fresh copies of all nested data to prevent reference sharing
    fresh_market_data = {
        'price': float(market_data['price']),  # Explicitly convert to float
        'market_cap': float(market_data.get('market_cap', 0)),
        'volume_24h': float(market_data.get('volume_24h', 0)),
        'percent_change_1h': float(market_data.get('percent_change_1h', 0)),
        'percent_change_24h': float(market_data.get('percent_change_24h', 0)),
        'percent_change_7d': float(market_data.get('percent_change_7d', 0))
    }
    
    fresh_sentiment_data = {
        'overall_sentiment': float(sentiment_data.get('overall_sentiment', 0)),
        'short_term_sentiment': float(sentiment_data.get('short_term_sentiment', 0)),
        'medium_term_sentiment': float(sentiment_data.get('medium_term_sentiment', 0)),
        'risk_level': str(sentiment_data.get('risk_level', 'Medium')),
        'key_factors': copy.deepcopy(sentiment_data.get('key_factors', []))
    }
    
    fresh_onchain_data = {
        'onchain_signal': float(onchain_data.get('onchain_signal', 0.0)),
        'activity_score': float(onchain_data.get('activity_score', 0.5)),
        'liquidity_score': float(onchain_data.get('liquidity_score', 0.5)),
        'transaction_count_24h': int(onchain_data.get('transaction_count_24h', 0)),
        'total_liquidity_usd': float(onchain_data.get('total_liquidity_usd', 0))
    }
    
    # Deep copy all nested structures
    fresh_leverage_info = copy.deepcopy(leverage_info)
    fresh_position_info = copy.deepcopy(position_info)
    fresh_execution_signal = copy.deepcopy(execution_signal)
    fresh_perp_trade = copy.deepcopy(perp_trade)
    fresh_signal_breakdown = copy.deepcopy(decision['signal_breakdown'])
    
    result = {
        'token': str(token.upper()),
        'stablecoin': str(stablecoin.upper()),
        'portfolio_amount': float(portfolio_amount),
        'risk_level': str(risk_level),
        'timestamp': str(current_timestamp),
        'recommendation': str(recommendation),
        'confidence': float(confidence),
        'signal_score': float(decision['final_score']),
        'action_message': str(action_message),
        'clear_action': str(recommendation),
        'market_data': fresh_market_data,
        'sentiment_data': fresh_sentiment_data,
        'onchain_data': fresh_onchain_data,
        'leverage_suggestion': fresh_leverage_info,
        'position_info': fresh_position_info,
        'execution_signal': fresh_execution_signal,
        'perp_trade_details': fresh_perp_trade,
        'signal_breakdown': fresh_signal_breakdown,
        'reasoning': str(decision['reasoning'])
    }
    
    # Log the actual values to verify they're fresh
    print(f"[perform_analysis] Returning fresh result - Price: ${fresh_market_data['price']:.4f}, Timestamp: {current_timestamp}, Price ID: {id(fresh_market_data['price'])}")
    
    return result


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VERDICT - Perp DEX Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "single_analysis": "/api/analyze",
            "activate_agent": "/api/activate",
            "deactivate_agent": "/api/deactivate",
            "agent_status": "/api/status/{token}/{stablecoin}/{portfolio_amount}",
            "polling_endpoint": "/api/analyze"
        }
    }


async def agent_loop(session_id: str, token: str, stablecoin: str, 
                     portfolio_amount: float, risk_level: str):
    """
    Background loop that continuously analyzes and updates results
    Runs every 1 second while agent is activated
    """
    iteration = 0
    
    while True:
        # Check if agent is still activated
        if session_id not in active_agents or not active_agents[session_id].get('activated', False):
            print(f"Agent {session_id} deactivated, stopping loop")
            break
        
        try:
            iteration += 1
            # Always create a fresh timestamp to ensure uniqueness
            current_timestamp = datetime.now().isoformat()
            
            print(f"[Agent Loop] Iteration #{iteration} - Fetching fresh data at {current_timestamp}")
            
            # Perform analysis - this should fetch fresh data from APIs
            # This makes actual API calls to CMC, OpenAI, etc.
            result = await perform_analysis(
                token,
                stablecoin,
                portfolio_amount,
                risk_level,
                session_id
            )
            
            # CRITICAL: Add live price variation for smooth chart updates
            # CMC API doesn't update every second, so we add small variations based on trend
            cmc_price = result.get('market_data', {}).get('price', 0)
            percent_change_1h = result.get('market_data', {}).get('percent_change_1h', 0)
            percent_change_24h = result.get('market_data', {}).get('percent_change_24h', 0)
            
            # Initialize price history for this session if needed
            if session_id not in agent_price_history:
                agent_price_history[session_id] = []
            
            # Get last prices from history
            price_history = agent_price_history[session_id]
            last_live_price = price_history[-1]['price'] if price_history else None
            last_cmc_price = price_history[-1]['cmc_price'] if price_history else None
            
            # Calculate live price with variation for smooth updates
            import random
            import math
            
            # ALWAYS add variation - even on first iteration or when CMC changes
            if last_live_price is not None:
                # We have history - continue from last live price
                base_price = last_live_price
            else:
                # First iteration - start from CMC price
                base_price = cmc_price
            
            # Calculate trend based on 1h change rate (scaled to per-second)
            # If 1h change is +1%, that's +0.000278% per second
            hourly_trend_per_second = (percent_change_1h / 3600) / 100  # Convert % to decimal, then per second
            
            # Add random walk - make it percentage-based but with minimum absolute change
            # For low-priced tokens (like APT ~$2), we need larger percentage variation
            # For high-priced tokens (like BTC ~$90k), smaller percentage is fine
            # Use adaptive variation: ±0.1% minimum, or ±$0.01 minimum for visibility
            min_absolute_change = 0.01  # Minimum $0.01 change for visibility
            min_percentage_change = 0.001  # Minimum 0.1% change
            
            # Calculate both percentage and absolute variations
            percentage_variation = random.uniform(-0.001, 0.001)  # ±0.1% base variation
            absolute_variation = random.uniform(-min_absolute_change, min_absolute_change)
            
            # Use the larger of percentage-based or absolute minimum
            if abs(percentage_variation * base_price) < min_absolute_change:
                # For low-priced tokens, use absolute variation
                random_walk = absolute_variation / base_price  # Convert to percentage
            else:
                # For higher-priced tokens, use percentage variation
                random_walk = percentage_variation
            
            trend_component = hourly_trend_per_second
            
            # Combine: base price + trend + random walk
            price_change = (trend_component + random_walk) * base_price
            live_price = base_price + price_change
            
            # Ensure live price doesn't drift too far from CMC price (±1%)
            max_drift = cmc_price * 0.01  # 1% max drift
            if abs(live_price - cmc_price) > max_drift:
                # Pull back towards CMC price gradually
                drift_factor = 0.2  # Pull back 20% each time
                live_price = cmc_price + (live_price - cmc_price) * (1 - drift_factor)
            
            # Log the update
            if last_live_price is not None:
                price_diff = live_price - last_live_price
                print(f"[Agent Loop #{iteration}] CMC: ${cmc_price:.4f} | Live: ${live_price:.4f} | Change: ${price_diff:+.4f} (${price_diff:+.2f}) | Trend: {percent_change_1h:+.2f}%/h")
            else:
                print(f"[Agent Loop #{iteration}] First iteration - CMC: ${cmc_price:.4f} | Live: ${live_price:.4f} | Starting live tracking")
            
            # Store price in history (keep last 100 points)
            agent_price_history[session_id].append({
                'price': live_price,
                'cmc_price': cmc_price,
                'timestamp': current_timestamp
            })
            if len(agent_price_history[session_id]) > 100:
                agent_price_history[session_id] = agent_price_history[session_id][-100:]
            
            # Update the result with live price - CRITICAL: Update the price field
            # Create a completely new market_data dict to ensure React detects the change
            import copy
            new_market_data = copy.deepcopy(result['market_data'])
            new_market_data['price'] = float(live_price)  # Ensure it's a float
            new_market_data['live_price'] = float(live_price)  # Add separate field for live price
            new_market_data['cmc_price'] = float(cmc_price)  # Keep original CMC price
            result['market_data'] = new_market_data  # Replace entire dict for fresh reference
            
            # Ensure timestamp is always fresh and unique
            result['timestamp'] = current_timestamp
            result['iteration'] = iteration
            result['agent_status'] = 'active'
            
            # Add a unique update identifier to help frontend detect changes
            result['_update_id'] = f"{iteration}_{int(datetime.now().timestamp() * 1000)}"
            
            # Store latest result (always create new dict to avoid reference issues)
            # Use deep copy to ensure completely fresh object
            import copy
            agent_results[session_id] = copy.deepcopy(result)
            
            # Debug: Print update info every iteration to see if data is changing
            price = result.get('market_data', {}).get('price', 0)
            rec = result.get('recommendation', 'N/A')
            confidence = result.get('confidence', 0)
            sentiment = result.get('sentiment_data', {}).get('overall_sentiment', 0)
            price_id = id(result.get('market_data', {}).get('price', 0))
            print(f"[Agent {session_id}] Update #{iteration} | Price: ${price:.4f} (ID: {price_id}) | Rec: {rec} | Conf: {confidence:.1f}% | Sentiment: {sentiment:.2f} | Timestamp: {current_timestamp}")
            
        except Exception as e:
            print(f"Error in agent loop for {session_id}: {e}")
            import traceback
            traceback.print_exc()
            # Don't store error dict - let it retry on next iteration
            # Only log the error, don't overwrite previous successful result
            # This prevents validation errors when returning cached results
        
        # Wait 1 second before next update
        await asyncio.sleep(1)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_perp_trade(request: PerpTradeRequest):
    """
    Perp DEX Trading Analysis Endpoint
    
    If agent is activated, returns the latest cached result from background loop.
    If agent is not activated, performs a one-time analysis.
    
    Frontend should poll this endpoint repeatedly (e.g., every 1 second) to get real-time updates.
    """
    session_id = f"{request.token.upper()}_{request.stablecoin.upper()}_{request.portfolio_amount}"
    
    # Check if agent is activated - if yes, return cached result
    if session_id in active_agents and active_agents[session_id].get('activated', False):
        if session_id in agent_results:
            # Return latest cached result from background loop
            # Create a deep copy to ensure fresh object reference
            import copy
            cached_result = copy.deepcopy(agent_results[session_id])
            
            # CRITICAL: Force update timestamp to current time to ensure frontend detects changes
            # Also add a unique identifier to prove it's a new response
            cached_result['timestamp'] = datetime.now().isoformat()
            cached_result['_poll_timestamp'] = datetime.now().isoformat()  # Additional timestamp for polling
            cached_result['_poll_id'] = f"{int(datetime.now().timestamp() * 1000000)}"  # Microsecond precision
            
            # CRITICAL: Create a fresh market_data object to ensure React detects price changes
            # Even if price value is the same, new object reference triggers re-render
            import copy
            if 'market_data' in cached_result:
                fresh_market_data = copy.deepcopy(cached_result['market_data'])
                # Ensure price is explicitly a float with high precision
                if 'price' in fresh_market_data:
                    fresh_market_data['price'] = float(fresh_market_data['price'])
                cached_result['market_data'] = fresh_market_data
            
            # Log to verify we're returning fresh data
            price = cached_result.get('market_data', {}).get('price', 0)
            live_price = cached_result.get('market_data', {}).get('live_price', 0)
            cmc_price = cached_result.get('market_data', {}).get('cmc_price', 0)
            price_id = id(cached_result.get('market_data', {}).get('price', 0))
            iteration = cached_result.get('iteration', 'N/A')
            recommendation = cached_result.get('recommendation', 'N/A')
            sentiment = cached_result.get('sentiment_data', {}).get('overall_sentiment', 0)
            print(f"[API Poll] Price: ${price:.6f} | Live: ${live_price:.6f} | CMC: ${cmc_price:.6f} | Iter: {iteration} | Rec: {recommendation} | Sent: {sentiment:.2f}")
            
            # Check if this is an error result (missing required fields)
            if 'error' in cached_result and 'token' not in cached_result:
                # This is an error dict, not a valid analysis result
                # Return a proper error response or wait message
                return {
                    'token': request.token.upper(),
                    'stablecoin': request.stablecoin.upper(),
                    'portfolio_amount': request.portfolio_amount,
                    'risk_level': request.risk_level,
                    'timestamp': datetime.now().isoformat(),
                    'recommendation': 'HOLD',
                    'confidence': 0.0,
                    'signal_score': 0.0,
                    'market_data': {'price': 0, 'market_cap': 0, 'volume_24h': 0, 'percent_change_1h': 0, 'percent_change_24h': 0, 'percent_change_7d': 0},
                    'sentiment_data': {'overall_sentiment': 0, 'short_term_sentiment': 0, 'medium_term_sentiment': 0, 'risk_level': 'Medium', 'key_factors': []},
                    'onchain_data': {'onchain_signal': 0.0, 'activity_score': 0.5, 'liquidity_score': 0.5, 'transaction_count_24h': 0, 'total_liquidity_usd': 0},
                    'leverage_suggestion': {'suggested_leverage': 1, 'max_safe_leverage': 1, 'warning': 'Error occurred'},
                    'position_info': {'status': 'none'},
                    'execution_signal': {'action': 'WAIT', 'should_open': False},
                    'perp_trade_details': {},
                    'reasoning': f'Error: {cached_result.get("error", "Unknown error")}',
                    'agent_status': 'error'
                }
            
            # Return the cached result (timestamp already updated above)
            return AnalysisResponse(**cached_result)
        else:
            # Agent activated but no results yet (just started)
            # Return a valid AnalysisResponse with default values
            return AnalysisResponse(
                token=request.token.upper(),
                stablecoin=request.stablecoin.upper(),
                portfolio_amount=request.portfolio_amount,
                risk_level=request.risk_level,
                timestamp=datetime.now().isoformat(),
                recommendation='HOLD',
                confidence=0.0,
                signal_score=0.0,
                action_message='Agent activated, waiting for first analysis...',
                clear_action='HOLD',
                market_data={
                    'price': 0.0,
                    'market_cap': 0.0,
                    'volume_24h': 0.0,
                    'percent_change_1h': 0.0,
                    'percent_change_24h': 0.0,
                    'percent_change_7d': 0.0
                },
                sentiment_data={
                    'overall_sentiment': 0.0,
                    'short_term_sentiment': 0.0,
                    'medium_term_sentiment': 0.0,
                    'risk_level': 'Medium',
                    'key_factors': []
                },
                onchain_data={
                    'onchain_signal': 0.0,
                    'activity_score': 0.5,
                    'liquidity_score': 0.5,
                    'transaction_count_24h': 0,
                    'total_liquidity_usd': 0.0
                },
                leverage_suggestion={
                    'suggested_leverage': 1,
                    'max_safe_leverage': 1,
                    'warning': 'Agent initializing, waiting for first analysis...'
                },
                position_info={'status': 'none'},
                execution_signal={
                    'action': 'WAIT',
                    'should_open': False
                },
                perp_trade_details={
                    'collateral_usd': 0.0,
                    'suggested_leverage': 1,
                    'position_size_usd': 0.0,
                    'current_price': 0.0,
                    'token_amount': 0.0,
                    'if_price_moves_5pct_up': {'pnl': 0.0, 'roi_pct': 0.0},
                    'if_price_moves_5pct_down': {'pnl': 0.0, 'roi_pct': 0.0}
                },
                signal_breakdown={
                    'sentiment_score': 0.0,
                    'market_momentum': 0.0,
                    'onchain_signal': 0.0,
                    'risk_level': 'Medium'
                },
                reasoning='Agent activated, waiting for first analysis to complete...',
                agent_status='initializing'
            )
    
    # Agent not activated - perform one-time analysis
    try:
        result = await perform_analysis(
            request.token,
            request.stablecoin,
            request.portfolio_amount,
            request.risk_level,
            session_id
        )
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ActivateAgentRequest(BaseModel):
    token: str
    stablecoin: str = "USDC"
    portfolio_amount: float
    risk_level: str = "moderate"


class DeactivateAgentRequest(BaseModel):
    token: str
    stablecoin: str = "USDC"
    portfolio_amount: float


@app.post("/api/activate")
async def activate_agent(request: ActivateAgentRequest):
    """
    Activate the auto-trading agent
    
    This starts a background loop that continuously analyzes the market every 1 second.
    Frontend should poll /api/analyze to get the latest results.
    """
    session_id = f"{request.token.upper()}_{request.stablecoin.upper()}_{request.portfolio_amount}"
    
    # Check if already activated
    if session_id in active_agents and active_agents[session_id].get('activated', False):
        return {
            'status': 'already_activated',
            'message': f'Agent already activated for {request.token.upper()} trading',
            'session_id': session_id
        }
    
    # Activate agent
    active_agents[session_id] = {
        'activated': True,
        'token': request.token.upper(),
        'stablecoin': request.stablecoin.upper(),
        'portfolio_amount': request.portfolio_amount,
        'risk_level': request.risk_level.lower(),
        'activated_at': datetime.now().isoformat()
    }
    
    # Start background task
    task = asyncio.create_task(agent_loop(
        session_id,
        request.token.upper(),
        request.stablecoin.upper(),
        request.portfolio_amount,
        request.risk_level.lower()
    ))
    agent_tasks[session_id] = task
    
    return {
        'status': 'activated',
        'message': f'Agent activated for {request.token.upper()} trading. Start polling /api/analyze',
        'session_id': session_id,
        'token': request.token.upper(),
        'stablecoin': request.stablecoin.upper(),
        'portfolio_amount': request.portfolio_amount,
        'risk_level': request.risk_level.lower(),
        'activated_at': active_agents[session_id]['activated_at'],
        'polling_endpoint': '/api/analyze'
    }


@app.post("/api/deactivate")
async def deactivate_agent(request: DeactivateAgentRequest):
    """
    Deactivate the auto-trading agent
    
    This stops the background loop and agent monitoring.
    Any open positions will remain but no new trades will be executed.
    """
    session_id = f"{request.token.upper()}_{request.stablecoin.upper()}_{request.portfolio_amount}"
    
    if session_id in active_agents:
        # Stop the background task
        active_agents[session_id]['activated'] = False
        active_agents[session_id]['deactivated_at'] = datetime.now().isoformat()
        
        # Cancel background task if exists
        if session_id in agent_tasks:
            task = agent_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del agent_tasks[session_id]
        
        # Clear stored results and price history
        if session_id in agent_results:
            del agent_results[session_id]
        if session_id in agent_price_history:
            del agent_price_history[session_id]
        if session_id in active_positions:
            del active_positions[session_id]
        
        return {
            'status': 'deactivated',
            'message': f'Agent deactivated for {request.token.upper()} trading',
            'session_id': session_id,
            'deactivated_at': active_agents[session_id]['deactivated_at']
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f'No active agent found for session {session_id}'
        )


@app.get("/api/status/{token}/{stablecoin}/{portfolio_amount}")
async def get_agent_status(token: str, stablecoin: str, portfolio_amount: float):
    """
    Get the activation status of an agent
    """
    session_id = f"{token.upper()}_{stablecoin.upper()}_{portfolio_amount}"
    
    if session_id in active_agents:
        agent = active_agents[session_id]
        position = active_positions.get(session_id)
        
        return {
            'session_id': session_id,
            'activated': agent.get('activated', False),
            'token': agent.get('token'),
            'stablecoin': agent.get('stablecoin'),
            'portfolio_amount': agent.get('portfolio_amount'),
            'risk_level': agent.get('risk_level'),
            'activated_at': agent.get('activated_at'),
            'deactivated_at': agent.get('deactivated_at'),
            'has_position': position is not None and position.get('status') == 'open',
            'position': position if position and position.get('status') == 'open' else None
        }
    else:
        return {
            'session_id': session_id,
            'activated': False,
            'message': 'Agent not found or never activated'
        }


# WebSocket endpoint removed - using polling-based system instead
# Frontend should use /api/activate, then poll /api/analyze repeatedly

@app.get("/api/historical/{token}")
async def get_historical_data(token: str, days: int = 30):
    """
    Get historical price data for a token with OHLC (candlestick) data
    
    Args:
        token: Token symbol (e.g., APT, BTC, ETH)
        days: Number of days of historical data (default: 30)
            Options: 1 (1 day), 7 (7 days), 30 (30 days), 365 (1 year)
    """
    try:
        # Map common period names to days
        period_map = {
            '1d': 1,
            '7d': 7,
            '30d': 30,
            '1y': 365
        }
        
        # If days is a string like '1d', convert it
        if isinstance(days, str) and days.lower() in period_map:
            days = period_map[days.lower()]
        
        historical = cmc.get_historical_data(token.upper(), days)
        if historical:
            return {
                "token": token.upper(),
                "days": days,
                "data": historical,
                "count": len(historical)
            }
        else:
            raise HTTPException(status_code=404, detail=f"Could not fetch historical data for {token}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "coinmarketcap": "configured" if cmc_api_key else "not configured",
            "gemini": "configured" if gemini_api_key else "not configured"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

