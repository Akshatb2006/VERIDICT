"""
Smart Contract interaction module for Flare VerifierContract
"""

from web3 import Web3
from eth_account import Account
import json
import os
from typing import Optional, Dict, Tuple
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Contract ABI (simplified - will be generated after compilation)
VERIFIER_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "string", "name": "signal", "type": "string"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "fdcProof", "type": "bytes32"}
        ],
        "name": "verifyDecision",
        "outputs": [
            {"internalType": "bytes32", "name": "decisionId", "type": "bytes32"},
            {"internalType": "bool", "name": "isValid", "type": "bool"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "decisionId", "type": "bytes32"}],
        "name": "isDecisionValid",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getStatistics",
        "outputs": [
            {"internalType": "uint256", "name": "total", "type": "uint256"},
            {"internalType": "uint256", "name": "valid", "type": "uint256"},
            {"internalType": "uint256", "name": "invalid", "type": "uint256"},
            {"internalType": "uint256", "name": "successRate", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


class FlareVerifier:
    """Interact with VerifierContract on Flare Network"""
    
    def __init__(self):
        self.rpc_url = os.getenv("FLARE_RPC_URL", "https://coston2-api.flare.network/ext/C/rpc")
        self.contract_address = os.getenv("VERIFIER_CONTRACT_ADDRESS")
        self.private_key = os.getenv("DEPLOYER_PRIVATE_KEY")
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            logger.error("[Flare Verifier] Failed to connect to Flare RPC")
            return
        
        logger.info(f"[Flare Verifier] Connected to {self.rpc_url}")
        
        # Initialize account
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            logger.info(f"[Flare Verifier] Account: {self.account.address}")
        else:
            self.account = None
            logger.warning("[Flare Verifier] No private key - read-only mode")
        
        # Initialize contract
        if self.contract_address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=VERIFIER_ABI
            )
            logger.info(f"[Flare Verifier] Contract loaded: {self.contract_address}")
        else:
            self.contract = None
            logger.warning("[Flare Verifier] No contract address configured")
    
    def _string_to_bytes32(self, text: str) -> bytes:
        """Convert string to bytes32"""
        return Web3.keccak(text=text)
    
    async def verify_decision_on_chain(
        self,
        symbol: str,
        signal: str,
        data_hash: str,
        fdc_proof: str
    ) -> Tuple[Optional[str], bool]:
        """
        Verify AI decision on Flare blockchain
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            signal: Trading signal (LONG/SHORT/HOLD)
            data_hash: Hash of input data
            fdc_proof: FDC attestation proof
            
        Returns:
            Tuple of (decision_id, is_valid)
        """
        if not self.contract or not self.account:
            logger.error("[Flare Verifier] Contract or account not initialized")
            return (None, False)
        
        try:
            logger.info(f"[Flare Verifier] Verifying {symbol} {signal} on-chain...")
            
            # Convert hashes to bytes32
            data_hash_bytes = self._string_to_bytes32(data_hash)
            fdc_proof_bytes = self._string_to_bytes32(fdc_proof)
            
            # Build transaction
            tx = self.contract.functions.verifyDecision(
                symbol,
                signal,
                data_hash_bytes,
                fdc_proof_bytes
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 250000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': int(os.getenv("FLARE_CHAIN_ID", "114"))
            })
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"[Flare Verifier] Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            
            # Parse logs to get decision ID and validity
            # This is simplified - in production, properly decode logs
            success = receipt['status'] == 1
            
            decision_id = tx_hash.hex() if success else None
            
            logger.info(f"[Flare Verifier] Verification complete - Valid: {success}")
            
            return (decision_id, success)
            
        except Exception as e:
            logger.error(f"[Flare Verifier] Error verifying on-chain: {e}")
            return (None, False)
    
    async def check_decision_status(self, decision_id: str) -> bool:
        """
        Check if a decision is valid
        
        Args:
            decision_id: Decision ID from verification
            
        Returns:
            True if valid, False otherwise
        """
        if not self.contract:
            return False
        
        try:
            decision_id_bytes = bytes.fromhex(decision_id.replace('0x', ''))
            is_valid = self.contract.functions.isDecisionValid(decision_id_bytes).call()
            return is_valid
        except Exception as e:
            logger.error(f"[Flare Verifier] Error checking status: {e}")
            return False
    
    async def get_statistics(self) -> Dict:
        """
        Get verification statistics from contract
        
        Returns:
            Dictionary with total, valid, invalid, and success rate
        """
        if not self.contract:
            return {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "success_rate": 0
            }
        
        try:
            stats = self.contract.functions.getStatistics().call()
            return {
                "total": stats[0],
                "valid": stats[1],
                "invalid": stats[2],
                "success_rate": stats[3] / 100  # Convert from basis points to percentage
            }
        except Exception as e:
            logger.error(f"[Flare Verifier] Error getting statistics: {e}")
            return {"total": 0, "valid": 0, "invalid": 0, "success_rate": 0}
