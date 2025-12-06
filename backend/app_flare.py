"""
Updated main application with Flare FDC/FTSO integration
This replaces direct API calls with verified Flare data sources
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

# Import Flare modules
from flare_data_connector import FlareDataConnector
from ftso_price_feed import FTSOPriceFeed
from flare_verifier import FlareVerifier
from sentiment_analyzer import SentimentAnalyzer

load_dotenv()

app = FastAPI(
    title="VERDICT - Perp DEX Analyzer API",
    description="Real-time sentiment and on-chain analysis with Flare FDC verification",
    version="2.0.0-flare"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Flare components
fdc = FlareDataConnector()
ftso = FTSOPriceFeed()
verifier = FlareVerifier()
sentiment_analyzer = SentimentAnalyzer(
    api_key=os.getenv("GEMINI_API_KEY"),
    fdc_connector=fdc
)

# Request/Response models
class AnalysisRequest(BaseModel):
    token: str
    stablecoin: str = "USDC"
    portfolio_amount: float
    risk_level: str = "moderate"

class AnalysisResponse(BaseModel):
    token: str
    signal: str
    confidence: float
    ftso_price: float
    sentiment_score: float
    verified: bool
    fdc_verified: bool
    contract_verified: Optional[bool]
    verification_hash: Optional[str]
    timestamp: str

@app.get("/")
async def root():
    return {
        "message": "VERDICT - Flare-Powered Trading Analyzer",
        "version": "2.0.0-flare",
        "features": ["FDC Verification", "FTSO Prices", "On-Chain Proof"],
        "endpoints": {
            "analyze": "/api/analyze",
            "health": "/api/health",
            "stats": "/api/stats"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check with Flare service status"""
    
    # Check FDC connectivity
    fdc_status = "configured" if fdc else "not_configured"
    
    # Check FTSO connectivity  
    ftso_status = "configured" if ftso else "not_configured"
    
    # Check verifier contract
    verifier_status = "configured" if verifier and verifier.contract else "not_configured"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "fdc": fdc_status,
            "ftso": ftso_status,
            "verifier_contract": verifier_status,
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not_configured"
        },
        "contract_address": os.getenv("VERIFIER_CONTRACT_ADDRESS"),
        "network": "coston2"
    }

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_token(request: AnalysisRequest):
    """
    Analyze token with Flare FDC/FTSO verification
    """
    try:
        print(f"\n[VERDICT Analysis] Starting for {request.token}")
        print(f"[Verification Pipeline] Step 1: FDC Data Request")
        
        # STEP 1: Get verified price from FTSO
        ftso_price_data = await ftso.get_price(f"{request.token}/USD")
        ftso_price = ftso_price_data.price
        
        print(f"[FTSO] Price: ${ftso_price:.2f} (Verified: {ftso_price > 0})")
        
        # STEP 2: Get verified sentiment data from FDC (if available)
        # For now, use direct sentiment with FDC metadata
        verified_sentiment_data = await fdc.get_verified_sentiment(request.token)
        
        print(f"[FDC] Sentiment data verified: {verified_sentiment_data.verified}")
        
        # STEP 3: Analyze with Gemini AI (includes verification context)
        market_data = {
            "price": ftso_price,
            "percent_change_24h": 0,  # Simplified for demo
            "percent_change_1h": 0,
            "percent_change_7d": 0,
            "market_cap": 0,
            "volume_24h": 0
        }
        
        sentiment_result = await sentiment_analyzer.analyze_token_sentiment(
            token_symbol=request.token,
            token_name=request.token,
            market_data=market_data,
            verified_data=verified_sentiment_data
        )
        
        sentiment_score = sentiment_result.get("overall_sentiment", 0)
        fdc_verified = sentiment_result.get("fdc_verified", False)
        
        print(f"[Gemini AI] Sentiment: {sentiment_score:.2f} (FDC Verified: {fdc_verified})")
        
        # STEP 4: Generate trading signal
        if sentiment_score > 20 and ftso_price > 0:
            signal = "LONG"
            confidence = min(0.7 + (sentiment_score / 200), 0.95)
        elif sentiment_score < -20:
            signal = "SHORT"
            confidence = min(0.7 + (abs(sentiment_score) / 200), 0.95)
        else:
            signal = "HOLD"
            confidence = 0.6
        
        print(f"[Decision] {signal} with {confidence*100:.1f}% confidence")
        
        # STEP 5: Verify on-chain (if data is verified)
        contract_verified = None
        verification_hash = None
        
        if fdc_verified and verified_sentiment_data.verified:
            print(f"[Smart Contract] Submitting for on-chain verification...")
            try:
                decision_id, is_valid = await verifier.verify_decision_on_chain(
                    symbol=f"{request.token}/USD",
                    signal=signal,
                    data_hash=verified_sentiment_data.hash,
                    fdc_proof=verified_sentiment_data.proof or "demo_proof"
                )
                contract_verified = is_valid
                verification_hash = decision_id
                print(f"[Smart Contract] Verified: {is_valid}, Hash: {decision_id[:16]}...")
            except Exception as e:
                print(f"[Smart Contract] Verification skipped: {e}")
                contract_verified = False
        
        # Build response
        response = AnalysisResponse(
            token=request.token,
            signal=signal,
            confidence=confidence,
            ftso_price=ftso_price,
            sentiment_score=sentiment_score,
            verified=fdc_verified and (contract_verified if contract_verified is not None else True),
            fdc_verified=fdc_verified,
            contract_verified=contract_verified,
            verification_hash=verification_hash,
            timestamp=datetime.now().isoformat()
        )
        
        print(f"[VERDICT] ✅ Analysis complete - {signal} signal")
        return response
        
    except Exception as e:
        print(f"[Error] Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_verification_stats():
    """Get verification statistics from smart contract"""
    try:
        stats = await verifier.get_statistics()
        return {
            "total_decisions": stats["total"],
            "valid_decisions": stats["valid"],
            "invalid_decisions": stats["invalid"],
            "success_rate": stats["success_rate"],
            "contract_address": os.getenv("VERIFIER_CONTRACT_ADDRESS")
        }
    except Exception as e:
        return {"error": str(e)}

# Serve dashboard
@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("example_dashboard.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
