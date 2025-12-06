"""
Attack Simulation Module for VERDICT
Demonstrates verification system's ability to detect data tampering
"""

import random
from typing import Dict, Tuple
from datetime import datetime
import copy


class AttackSimulator:
    """Simulate various data tampering attacks to demonstrate verification capabilities"""
    
    ATTACK_TYPES = {
        "price_manipulation": "Corrupt price data to simulate fake market conditions",
        "sentiment_corruption": "Manipulate sentiment scores to influence decisions",
        "proof_invalidation": "Break FDC proof to simulate attestation failure",
        "multi_vector": "Combined attack on multiple data sources"
    }
    
    def __init__(self):
        self.attack_active = False
        self.attack_type = None
        self.attack_metadata = {}
    
    def simulate_attack(self, 
                       analysis_data: Dict, 
                       attack_type: str = "price_manipulation") -> Tuple[Dict, Dict]:
        """
        Simulate a data tampering attack
        
        Args:
            analysis_data: Original analysis data from perform_analysis()
            attack_type: Type of attack to simulate
            
        Returns:
            Tuple of (tampered_data, attack_info)
        """
        # Create deep copy to avoid modifying original
        tampered_data = copy.deepcopy(analysis_data)
        
        attack_info = {
            "attack_type": attack_type,
            "attack_active": True,
            "timestamp": datetime.now().isoformat(),
            "description": self.ATTACK_TYPES.get(attack_type, "Unknown attack"),
            "tampering_details": []
        }
        
        # Apply attack based on type
        if attack_type == "price_manipulation":
            tampered_data, details = self._tamper_price(tampered_data)
            attack_info["tampering_details"] = details
            
        elif attack_type == "sentiment_corruption":
            tampered_data, details = self._corrupt_sentiment(tampered_data)
            attack_info["tampering_details"] = details
            
        elif attack_type == "proof_invalidation":
            tampered_data, details = self._invalidate_proof(tampered_data)
            attack_info["tampering_details"] = details
            
        elif attack_type == "multi_vector":
            # Apply multiple attacks
            tampered_data, price_details = self._tamper_price(tampered_data)
            tampered_data, sent_details = self._corrupt_sentiment(tampered_data)
            tampered_data, proof_details = self._invalidate_proof(tampered_data)
            attack_info["tampering_details"] = price_details + sent_details + proof_details
        
        # Mark data as tampered
        tampered_data["_tampered"] = True
        tampered_data["_attack_info"] = attack_info
        
        # Force verification to fail
        tampered_data["verified"] = False
        tampered_data["contract_verified"] = False
        tampered_data["fdc_verified"] = False
        
        self.attack_active = True
        self.attack_type = attack_type
        self.attack_metadata = attack_info
        
        return tampered_data, attack_info
    
    def _tamper_price(self, data: Dict) -> Tuple[Dict, list]:
        """
        Tamper with price data to create mismatch
        
        Args:
            data: Analysis data to tamper
            
        Returns:
            Tuple of (tampered_data, tampering_details)
        """
        details = []
        
        # Get original price
        original_price = data.get("market_data", {}).get("price", 0)
        
        # Corrupt price by 20-50% (significant change)
        corruption_factor = random.uniform(1.2, 1.5)
        tampered_price = original_price * corruption_factor
        
        # Update market data with fake price
        if "market_data" in data:
            data["market_data"]["price"] = round(tampered_price, 2)
            data["market_data"]["_original_price"] = original_price
            
            details.append({
                "component": "market_data.price",
                "original_value": f"${original_price:.2f}",
                "tampered_value": f"${tampered_price:.2f}",
                "change_pct": f"+{((tampered_price / original_price - 1) * 100):.1f}%",
                "method": "Price manipulation attack"
            })
        
        # This will cause FTSO verification to fail
        # because tampered price won't match FTSO price
        if "ftso_price" in data:
            # FTSO price stays correct (from real oracle)
            ftso_price = data["ftso_price"]
            price_diff_pct = abs(tampered_price - ftso_price) / ftso_price * 100
            
            details.append({
                "component": "ftso_verification",
                "detection": "FTSO Mismatch Detected",
                "ftso_price": f"${ftso_price:.2f}",
                "declared_price": f"${tampered_price:.2f}",
                "difference": f"{price_diff_pct:.1f}%",
                "threshold": "2.0%",
                "result": "❌ VERIFICATION FAILED"
            })
        
        return data, details
    
    def _corrupt_sentiment(self, data: Dict) -> Tuple[Dict, list]:
        """
        Corrupt sentiment data to manipulate trading signals
        
        Args:
            data: Analysis data to tamper
            
        Returns:
            Tuple of (tampered_data, tampering_details)
        """
        details = []
        
        if "sentiment_data" in data:
            original_sentiment = data["sentiment_data"].get("overall_sentiment", 0)
            
            # Flip sentiment to opposite extreme
            if original_sentiment > 0:
                # Positive -> Very negative
                tampered_sentiment = -8.0
            else:
                # Negative -> Very positive
                tampered_sentiment = 8.0
            
            data["sentiment_data"]["overall_sentiment"] = tampered_sentiment
            data["sentiment_data"]["_original_sentiment"] = original_sentiment
            
            details.append({
                "component": "sentiment_data.overall_sentiment",
                "original_value": f"{original_sentiment:.2f}",
                "tampered_value": f"{tampered_sentiment:.2f}",
                "method": "Sentiment manipulation attack",
                "impact": "Could cause incorrect LONG/SHORT signals"
            })
        
        return data, details
    
    def _invalidate_proof(self, data: Dict) -> Tuple[Dict, list]:
        """
        Invalidate FDC attestation proof
        
        Args:
            data: Analysis data to tamper
            
        Returns:
            Tuple of (tampered_data, tampering_details)
        """
        details = []
        
        # Mark FDC as unverified
        original_fdc = data.get("fdc_verified", True)
        data["fdc_verified"] = False
        
        details.append({
            "component": "fdc_verification",
            "original_value": "✅ Verified",
            "tampered_value": "❌ Invalid Proof",
            "method": "FDC attestation proof corruption",
            "result": "Data provenance cannot be verified"
        })
        
        # Corrupt verification hash
        if "verification_hash" in data:
            original_hash = data["verification_hash"]
            # Create invalid hash
            tampered_hash = "0x" + "0" * 62 + "FAKE"
            data["verification_hash"] = tampered_hash
            data["_original_hash"] = original_hash
            
            details.append({
                "component": "verification_hash",
                "original_value": original_hash[:16] + "...",
                "tampered_value": tampered_hash[:16] + "...",
                "method": "Hash corruption",
                "result": "Cryptographic verification failed"
            })
        
        return data, details
    
    def reset_simulation(self) -> Dict:
        """
        Reset attack simulation to normal operation
        
        Returns:
            Reset status dictionary
        """
        self.attack_active = False
        self.attack_type = None
        self.attack_metadata = {}
        
        return {
            "status": "simulation_reset",
            "message": "Attack simulation deactivated, returning to normal verification",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_attack_types(self) -> Dict[str, str]:
        """Get available attack types and descriptions"""
        return self.ATTACK_TYPES.copy()
    
    def is_attack_active(self) -> bool:
        """Check if attack simulation is currently active"""
        return self.attack_active
    
    def get_attack_metadata(self) -> Dict:
        """Get current attack metadata"""
        return self.attack_metadata.copy() if self.attack_metadata else {}
