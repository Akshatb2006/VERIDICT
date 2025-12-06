# Smart Contract Deployment Guide

## Prerequisites

1. **Get Coston2 Testnet Tokens**
   - Visit Flare Faucet: https://faucet.flare.network/
   - Connect your MetaMask wallet
   - Request C2FLR tokens for Coston2 testnet

2. **Install Dependencies**
   ```bash
   npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
   ```

3. **Configure Hardhat**
   Create `hardhat.config.js`:
   ```javascript
   require("@nomicfoundation/hardhat-toolbox");
   require("dotenv").config();
   
   module.exports = {
     solidity: "0.8.20",
     networks: {
       coston2: {
         url: "https://coston2-api.flare.network/ext/C/rpc",
         chainId: 114,
         accounts: [process.env.DEPLOYER_PRIVATE_KEY]
       }
     },
     etherscan: {
       apiKey: {
         coston2: "flare" // Dummy API key for Flare explorer
       },
       customChains: [
         {
           network: "coston2",
           chainId: 114,
           urls: {
             apiURL: "https://coston2-explorer.flare.network/api",
             browserURL: "https://coston2-explorer.flare.network"
           }
         }
       ]
     }
   };
   ```

## Deployment Steps

### 1. Create Deployment Script

Create `contracts/scripts/deploy.js`:

```javascript
const hre = require("hardhat");

async function main() {
  console.log("Deploying VerifierContract to Coston2...");
  
  const VerifierContract = await hre.ethers.getContractFactory("VerifierContract");
  const verifier = await VerifierContract.deploy();
  
  await verifier.waitForDeployment();
  
  const address = await verifier.getAddress();
  console.log("VerifierContract deployed to:", address);
  
  // Save address to .env
  console.log("\nAdd this to your .env file:");
  console.log(`VERIFIER_CONTRACT_ADDRESS=${address}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

### 2. Deploy Contract

```bash
npx hardhat run contracts/scripts/deploy.js --network coston2
```

Expected output:
```
Deploying VerifierContract to Coston2...
VerifierContract deployed to: 0x1234567890abcdef...

Add this to your .env file:
VERIFIER_CONTRACT_ADDRESS=0x1234567890abcdef...
```

### 3. Verify Contract (Optional)

```bash
npx hardhat verify --network coston2 YOUR_CONTRACT_ADDRESS
```

##4. Test Deployment

Create `contracts/test/test_verifier.js`:

```javascript
const { expect } = require("chai");

describe("VerifierContract", function () {
  let verifier;
  let owner;
  
  beforeEach(async function () {
    [owner] = await ethers.getSigners();
    const VerifierContract = await ethers.getContractFactory("VerifierContract");
    verifier = await VerifierContract.deploy();
    await verifier.waitForDeployment();
  });
  
  it("Should verify a decision", async function () {
    const symbol = "BTC/USD";
    const signal = "LONG";
    const dataHash = ethers.id("test_data");
    const fdcProof = ethers.id("test_proof");
    
    const tx = await verifier.verifyDecision(symbol, signal, dataHash, fdcProof);
    const receipt = await tx.wait();
    
    // Check event emission
    const event = receipt.logs.find(log => log.fragment.name === "DecisionVerified");
    expect(event).to.not.be.undefined;
  });
  
  it("Should track statistics", async function () {
    const symbol = "BTC/USD";
    const signal = "LONG";
    const dataHash = ethers.id("test_data");
    const fdcProof = ethers.id("test_proof");
    
    await verifier.verifyDecision(symbol, signal, dataHash, fdcProof);
    
    const stats = await verifier.getStatistics();
    expect(stats.total).to.equal(1);
    expect(stats.valid).to.equal(1);
  });
});
```

Run tests:
```bash
npx hardhat test
```

## Using the Contract from Python

Create `flare_verifier.py`:

```python
from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv()

class FlareVerifier:
    def __init__(self):
        self.rpc_url = os.getenv("FLARE_RPC_URL")
        self.contract_address = os.getenv("VERIFIER_CONTRACT_ADDRESS")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Load contract ABI
        with open("contracts/VerifierContract.sol.abi", "r") as f:
            self.contract_abi = json.load(f)
        
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
    
    async def verify_decision(self, symbol, signal, data_hash, fdc_proof):
        """Verify AI decision on-chain"""
        
        # Build transaction
       tx = self.contract.functions.verifyDecision(
            symbol,
            signal,
            data_hash,
            fdc_proof
        ).build_transaction({
            'from': os.getenv("WALLET_ADDRESS"),
            'nonce': self.w3.eth.get_transaction_count(os.getenv("WALLET_ADDRESS")),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send
        signed = self.w3.eth.account.sign_transaction(tx, os.getenv("DEPLOYER_PRIVATE_KEY"))
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return receipt
```

## Troubleshooting

**Issue: "insufficient funds"**
- Get more C2FLR from faucet: https://faucet.flare.network/

**Issue: "nonce too low"**
- Reset MetaMask account in Settings → Advanced → Reset Account

**Issue: "contract not verified"**
- Manual verification at: https://coston2-explorer.flare.network/

## Next Steps

1. ✅ Deploy contract
2. ✅ Save address to `.env`
3. 📝 Update backend to call contract
4. 🎨 Show verification status in UI
