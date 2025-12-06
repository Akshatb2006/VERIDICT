// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VerifierContract
 * @notice Verifies AI trading decisions against Flare Data Connector (FDC) attestations
 * @dev This contract validates that AI decisions are based on verified, tamper-proof data
 */
contract VerifierContract {
    
    // Structs
    struct VerifiedDecision {
        string symbol;           // Trading pair (e.g., "BTC/USD")
        string signal;          // LONG, SHORT, or HOLD
        bytes32 dataHash;       // Hash of input data used by AI
        bytes32 fdcProof;       // FDC attestation proof
        uint256 timestamp;      // Decision timestamp
        bool valid;             // Verification result
        address user;           // Who made the decision
    }
    
    // State variables
    mapping(bytes32 => VerifiedDecision) public decisions;
    mapping(address => uint256) public userDecisionCount;
    
    uint256 public totalDecisions;
    uint256 public validDecisions;
    uint256 public invalidDecisions;
    
    // Events
    event DecisionVerified(
        bytes32 indexed decisionId,
        address indexed user,
        string symbol,
        string signal,
        bool valid,
        uint256 timestamp
    );
    
    event VerificationFailed(
        bytes32 indexed decisionId,
        address indexed user,
        string reason,
        uint256 timestamp
    );
    
    /**
     * @notice Verify an AI trading decision
     * @param symbol Trading pair symbol
     * @param signal Trading signal (LONG/SHORT/HOLD)
     * @param dataHash Hash of the data used to make the decision
     * @param fdcProof FDC attestation proof for the data
     * @return decisionId Unique ID for this verification
     * @return isValid Whether the verification passed
     */
    function verifyDecision(
        string memory symbol,
        string memory signal,
        bytes32 dataHash,
        bytes32 fdcProof
    ) public returns (bytes32 decisionId, bool isValid) {
        
        // Generate unique decision ID
        decisionId = keccak256(abi.encodePacked(
            msg.sender,
            symbol,
            signal,
            dataHash,
            block.timestamp
        ));
        
        // Validate FDC proof
        isValid = _validateFDCProof(dataHash, fdcProof);
        
        // Store decision
        decisions[decisionId] = VerifiedDecision({
            symbol: symbol,
            signal: signal,
            dataHash: dataHash,
            fdcProof: fdcProof,
            timestamp: block.timestamp,
            valid: isValid,
            user: msg.sender
        });
        
        // Update counters
        totalDecisions++;
        userDecisionCount[msg.sender]++;
        
        if (isValid) {
            validDecisions++;
        } else {
            invalidDecisions++;
        }
        
        // Emit event
        emit DecisionVerified(
            decisionId,
            msg.sender,
            symbol,
            signal,
            isValid,
            block.timestamp
        );
        
        return (decisionId, isValid);
    }
    
    /**
     * @notice Batch verify multiple decisions
     * @param symbols Array of trading symbols
     * @param signals Array of trading signals
     * @param dataHashes Array of data hashes
     * @param fdcProofs Array of FDC proofs
     * @return decisionIds Array of decision IDs
     * @return validResults Array of validation results
     */
    function batchVerifyDecisions(
        string[] memory symbols,
        string[] memory signals,
        bytes32[] memory dataHashes,
        bytes32[] memory fdcProofs
    ) external returns (bytes32[] memory decisionIds, bool[] memory validResults) {
        
        require(
            symbols.length == signals.length &&
            signals.length == dataHashes.length &&
            dataHashes.length == fdcProofs.length,
            "Array lengths mismatch"
        );
        
        uint256 length = symbols.length;
        decisionIds = new bytes32[](length);
        validResults = new bool[](length);
        
        for (uint256 i = 0; i < length; i++) {
            (decisionIds[i], validResults[i]) = verifyDecision(
                symbols[i],
                signals[i],
                dataHashes[i],
                fdcProofs[i]
            );
        }
        
        return (decisionIds, validResults);
    }
    
    /**
     * @notice Get decision details
     * @param decisionId Unique decision ID
     * @return decision VerifiedDecision struct
     */
    function getDecision(bytes32 decisionId) 
        external 
        view 
        returns (VerifiedDecision memory decision) 
    {
        return decisions[decisionId];
    }
    
    /**
     * @notice Check if a decision is valid
     * @param decisionId Decision ID to check
     * @return True if decision exists and is valid
     */
    function isDecisionValid(bytes32 decisionId) external view returns (bool) {
        return decisions[decisionId].valid;
    }
    
    /**
     * @notice Get statistics
     * @return total Total decisions
     * @return valid Valid decisions
     * @return invalid Invalid decisions
     * @return successRate Success rate (basis points, e.g., 9500 = 95%)
     */
    function getStatistics() 
        external 
        view 
        returns (
            uint256 total,
            uint256 valid,
            uint256 invalid,
            uint256 successRate
        ) 
    {
        total = totalDecisions;
        valid = validDecisions;
        invalid = invalidDecisions;
        
        if (total > 0) {
            successRate = (valid * 10000) / total;
        } else {
            successRate = 0;
        }
        
        return (total, valid, invalid, successRate);
    }
    
    /**
     * @notice Validate FDC attestation proof
     * @param dataHash Hash of the data
     * @param fdcProof FDC attestation proof
     * @return True if proof is valid
     */
    function _validateFDCProof(
        bytes32 dataHash,
        bytes32 fdcProof
    ) internal pure returns (bool) {
        
        // Basic validation
        if (dataHash == bytes32(0) || fdcProof == bytes32(0)) {
            return false;
        }
        
        // In production, this would:
        // 1. Call FDC verification contract
        // 2. Verify cryptographic signature
        // 3. Check attestation provider validity
        // 4. Validate timestamp freshness
        
        // For demo/testing, we accept non-zero proofs
        // TODO: Implement full FDC verification
        
        return true;
    }
    
    /**
     * @notice Emergency pause function (for testing only)
     * @dev In production, implement proper access control
     */
    function emergencyStop() external {
        // TODO: Add access control (only owner)
        // For now, anyone can call (testnet only)
        totalDecisions = 0;
        validDecisions = 0;
        invalidDecisions = 0;
    }
}
