# SentenexAI Deployment Instructions

This guide provides step-by-step instructions for deploying the SentenexAI/VERDICT application using Render (backend) and Netlify (frontend).

## Table of Contents
1. [Backend Deployment (Render)](#backend-deployment-render)
2. [Frontend Deployment (Netlify)](#frontend-deployment-netlify)
3. [Smart Contract Deployment (Flare Network)](#smart-contract-deployment)
4. [Final Configuration](#final-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Backend Deployment (Render)

### Step 1: Prepare Your Repository

1. Ensure all files are committed to Git:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. Your repository should include:
   - `render.yaml` (already created)
   - `backend/requirements.txt`
   - `backend/app.py` with updated CORS settings
   - `backend/.env.example` (for reference)

### Step 2: Create Render Account

1. Go to [https://render.com](https://render.com)
2. Sign up using your GitHub account
3. Authorize Render to access your repositories

### Step 3: Deploy Backend to Render

1. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

2. **Configure Service:**
   - **Name**: `sentenexai-backend` (or your preferred name)
   - **Region**: Choose closest to your users (e.g., Oregon, Frankfurt)
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty
   - **Runtime**: Python 3
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables:**
   Click "Advanced" → "Add Environment Variable" and add:
   
   ```
   CMC_API_KEY=your_coinmarketcap_api_key_here
   GEMINI_API_KEY=your_google_gemini_api_key_here
   PYTHON_VERSION=3.11.0
   PORT=10000
   ```
   
   Optional (for smart contract features):
   ```
   FLARE_RPC_URL=https://coston2-api.flare.network/ext/C/rpc
   FLARE_NETWORK=coston2
   FLARE_CHAIN_ID=114
   FDC_ENDPOINT=https://fdc-api.flare.network
   FDC_ENABLED=true
   FTSO_ENABLED=true
   VERIFIER_CONTRACT_ADDRESS=0x... (add after contract deployment)
   DEPLOYER_PRIVATE_KEY=your_wallet_private_key (if using contract)
   WALLET_ADDRESS=your_wallet_address (if using contract)
   ```

4. **Deploy:**
   - Click "Create Web Service"
   - Wait 5-10 minutes for the initial deployment
   - Once complete, you'll get a URL like: `https://sentenexai-backend.onrender.com`

5. **Verify Backend:**
   - Visit `https://your-backend-url.onrender.com`
   - You should see: `{"message": "VERDICT - Perp DEX Analyzer API", ...}`
   - Visit `https://your-backend-url.onrender.com/health`
   - Should return: `{"status": "healthy", ...}`

---

## Frontend Deployment (Netlify)

### Step 1: Update Frontend Configuration

1. **Update API URL in `frontend/dashboard.html`:**
   
   Find line ~1026 and update the production URL:
   ```javascript
   function getApiUrl() {
       if (window.location.hostname.includes('netlify.app') || 
           window.location.hostname.includes('your-custom-domain.com')) {
           // Replace with your actual Render backend URL
           return 'https://sentenexai-backend.onrender.com/api';  // ← Update this!
       }
       return 'http://localhost:8000/api';
   }
   ```

2. **Update verification.html** (if using):
   - Make the same API URL changes in `frontend/verification.html`

3. **Commit changes:**
   ```bash
   git add frontend/
   git commit -m "Update frontend API URLs for production"
   git push origin main
   ```

### Step 2: Deploy to Netlify

#### Option A: Netlify CLI (Recommended)

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify:**
   ```bash
   netlify login
   ```

3. **Deploy:**
   ```bash
   # Navigate to project root
   cd /path/to/Sentenex-main
   
   # Initialize and deploy
   netlify deploy --dir=frontend --prod
   ```

4. **Follow prompts:**
   - Create new site or link existing
   - Choose a site name
   - Confirm deployment

#### Option B: Netlify Web UI

1. **Login to Netlify:**
   - Go to [https://app.netlify.com](https://app.netlify.com)
   - Sign up/login with GitHub

2. **Deploy:**
   - Click "Add new site" → "Import an existing project"
   - Choose GitHub and select your repository
   - Configure build settings:
     - **Base directory**: `frontend`
     - **Build command**: (leave empty for static site)
     - **Publish directory**: `.` or `frontend`
   - Click "Deploy site"

3. **Get URL:**
   - After deployment, you'll get a URL like: `https://your-app-name.netlify.app`
   - You can customize this in Site settings → Domain management

### Step 3: Configure CORS on Backend

Update Render environment variables:

1. Go to your Render dashboard
2. Select your backend service
3. Go to "Environment" tab
4. Add new environment variable:
   ```
   ALLOWED_ORIGINS=https://your-app-name.netlify.app,https://custom-domain.com
   ```
5. Click "Save Changes"
6. Render will automatically redeploy

---

## Smart Contract Deployment

> **Note:** This step is optional and only needed if you want blockchain verification features.

### Prerequisites

1. **Install Hardhat dependencies:**
   ```bash
   cd /path/to/Sentenex-main
   npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
   ```

2. **Get testnet tokens:**
   - Visit [https://faucet.flare.network/](https://faucet.flare.network/)
   - Connect MetaMask to Coston2 testnet
   - Request C2FLR tokens

### Deployment Steps

1. **Check deployment script exists:**
   ```bash
   ls contracts/scripts/deploy.js
   ```

2. **Add private key to environment:**
   ```bash
   # Create .env in project root if it doesn't exist
   echo "DEPLOYER_PRIVATE_KEY=your_private_key_here" >> .env
   ```

3. **Deploy contract:**
   ```bash
   npx hardhat run contracts/scripts/deploy.js --network coston2
   ```

4. **Save contract address:**
   - Copy the deployed contract address from output
   - Add to Render environment variables:
     ```
     VERIFIER_CONTRACT_ADDRESS=0x...
     ```

5. **Verify contract (optional):**
   ```bash
   npx hardhat verify --network coston2 YOUR_CONTRACT_ADDRESS
   ```

---

## Final Configuration

### Update Backend Environment (Render)

Ensure all environment variables are set:
- ✅ `CMC_API_KEY`
- ✅ `GEMINI_API_KEY`
- ✅ `ALLOWED_ORIGINS` (with your Netlify URL)
- ✅ `VERIFIER_CONTRACT_ADDRESS` (if using smart contract)

### Update Frontend URLs

1. Update `frontend/dashboard.html` line ~1026 with your actual Render URL
2. Update `netlify.toml` if you have custom redirects needed
3. Commit and push:
   ```bash
   git add .
   git commit -m "Final production configuration"
   git push origin main
   ```

4. Redeploy Netlify (it should auto-deploy from Git)

---

## Verification

### Backend Health Check
```bash
# Test health endpoint
curl https://your-backend-url.onrender.com/health

# Should return:
# {"status":"healthy","service":"VERDICT API",...}
```

### Frontend Connectivity
1. Open `https://your-app-name.netlify.app`
2. Open browser console (F12)
3. Check for API URL log: `🌐 API URL: https://your-backend-url.onrender.com/api`
4. Enter token symbol (e.g., BTC) and portfolio amount
5. Click "Activate Agent"
6. Verify recommendations appear

### API Test
```bash
curl -X POST https://your-backend-url.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "token": "BTC",
    "stablecoin": "USDC",
    "portfolio_amount": 1000,
    "risk_level": "moderate"
  }'
```

---

## Troubleshooting

### Backend Issues

**Problem: "Application failed to respond"**
- Check Render logs: Dashboard → Logs tab
- Verify all environment variables are set
- Check that build command completed successfully

**Problem: "Module not found"**
- Ensure `requirements.txt` includes all dependencies
- Redeploy to trigger fresh build

**Problem: API returning 500 errors**
- Check Render logs for error details
- Verify `CMC_API_KEY` and `GEMINI_API_KEY` are valid
- Test locally first: `cd backend && uvicorn app:app --reload`

### Frontend Issues

**Problem: CORS errors**
- Verify `ALLOWED_ORIGINS` on Render includes your Netlify URL
- Check browser console for exact error
- Make sure Netlify URL matches exactly (with/without trailing slash)

**Problem: "Failed to fetch"**
- Check API URL in `dashboard.html` is correct
- Verify backend is running (visit health endpoint)
- Check browser Network tab for failed requests

**Problem: Dashboard not updating**
- Open browser console for JavaScript errors
- Verify WebSocket connection if using real-time features
- Clear browser cache and hard reload (Ctrl+Shift+R)

### Smart Contract Issues

**Problem: "insufficient funds"**
- Get more C2FLR from [faucet](https://faucet.flare.network/)
- Check wallet balance on Coston2

**Problem: "nonce too low"**
- Reset MetaMask: Settings → Advanced → Reset Account

---

## URLs Reference

After deployment, save these URLs:

- **Frontend (Netlify)**: `https://your-app-name.netlify.app`
- **Backend (Render)**: `https://sentenexai-backend.onrender.com`
- **API Docs**: `https://sentenexai-backend.onrender.com/docs`
- **Health Check**: `https://sentenexai-backend.onrender.com/health`
- **Smart Contract (if deployed)**: `https://coston2-explorer.flare.network/address/0x...`

---

## Next Steps

1. **Custom Domain (Optional)**:
   - Netlify: Settings → Domain management → Add custom domain
   - Render: Settings → Custom domain

2. **Monitoring**:
   - Set up Render alerts for service health
   - Monitor API usage on CoinMarketCap dashboard
   - Check Gemini API quota

3. **Scaling**:
   - Upgrade Render plan if needed for more resources
   - Add caching layer for frequently accessed data
   - Consider CDN for static assets

4. **Security**:
   - Never commit `.env` files to Git
   - Rotate API keys regularly
   - Use Render's secret management for sensitive data
   - Enable HTTPS everywhere (automatic on Render & Netlify)

---

## Support

- **Render Docs**: [https://render.com/docs](https://render.com/docs)
- **Netlify Docs**: [https://docs.netlify.com](https://docs.netlify.com)
- **Flare Docs**: [https://docs.flare.network](https://docs.flare.network)
