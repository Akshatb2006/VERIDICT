# 🚀 SentenexAI Quick Deployment Guide

## Prerequisites
- [x] GitHub account
- [x] CoinMarketCap API key
- [x] Google Gemini API key
- [ ] Flare Network wallet (optional, for smart contract)

---

## Step 1: Deploy Backend to Render (15 minutes)

### 1A. Push to GitHub
```bash
cd /path/to/Sentenex-main
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 1B. Deploy on Render
1. Go to **[render.com](https://render.com)** → Sign up with GitHub
2. Click **"New +"** → **"Web Service"**
3. Select your repository
4. Configure:
   - **Name**: `sentenexai-backend`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add **Environment Variables**:
   ```
   CMC_API_KEY=paste_your_key_here
   GEMINI_API_KEY=paste_your_key_here
   PYTHON_VERSION=3.11.0
   ```
6. Click **"Create Web Service"**
7. Wait 5-10 minutes for deployment
8. **Save your backend URL**: `https://sentenexai-backend.onrender.com` ✍️

---

## Step 2: Update Frontend Configuration (2 minutes)

### 2A. Edit Dashboard
Open `frontend/dashboard.html` and find line ~1035:

```javascript
// Change this line:
return 'https://your-backend-app.onrender.com/api';

// To your actual Render URL:
return 'https://sentenexai-backend.onrender.com/api';  // ← Your URL here
```

### 2B. Commit Changes
```bash
git add frontend/dashboard.html
git commit -m "Update API URL for production"
git push origin main
```

---

## Step 3: Deploy Frontend to Netlify (10 minutes)

### 3A. Deploy on Netlify
1. Go to **[netlify.com](https://app.netlify.com)** → Sign up with GitHub
2. Click **"Add new site"** → **"Import an existing project"**
3. Select GitHub → Choose your repository  
4. Configure:
   - **Base directory**: `frontend`
   - **Build command**: (leave empty)
   - **Publish directory**: `.`
5. Click **"Deploy site"**
6. Wait 2-3 minutes
7. **Save your frontend URL**: `https://your-app.netlify.app` ✍️

### 3B. (Optional) Custom Domain
- Netlify Dashboard → **Domain settings** → **Add custom domain**

---

## Step 4: Configure CORS (5 minutes)

### 4A. Update Render Environment
1. Go to Render Dashboard → Select your backend service
2. Click **"Environment"** tab
3. Add new environment variable:
   ```
   ALLOWED_ORIGINS=https://your-app.netlify.app
   ```
4. Click **"Save Changes"**
5. Render will automatically redeploy

---

## Step 5: Test Your Deployment! 🎉

### 5A. Test Backend
```bash
curl https://sentenexai-backend.onrender.com/health
```
Should return: `{"status":"healthy",...}`

### 5B. Test Frontend
1. Open `https://your-app.netlify.app` in browser
2. Open Console (F12) and check for: `🌐 API URL: https://...`
3. Enter token (e.g., **BTC**) and amount (e.g., **1000**)
4. Click **"Activate Agent"**
5. You should see recommendations updating in real-time! ✅

---

## Optional: Deploy Smart Contract (30 minutes)

If you want blockchain verification:

```bash
# Install Hardhat
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox

# Get testnet tokens
# Visit: https://faucet.flare.network/

# Deploy to Coston2
npx hardhat run contracts/scripts/deploy.js --network coston2

# Add contract address to Render env vars
VERIFIER_CONTRACT_ADDRESS=0x...
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed smart contract instructions.

---

## Troubleshooting

### Backend Won't Start
- Check Render logs for errors
- Verify API keys are set correctly
- Ensure build command completed

### Frontend Can't Connect
- Check browser console for errors
- Verify API URL in dashboard.html matches your Render URL
- Check CORS settings on Render

### CORS Errors
- Add your Netlify URL to Render's `ALLOWED_ORIGINS`
- Make sure URLs match exactly (no trailing slashes)
- Redeploy Render service after adding env var

---

## Quick Reference

📚 **Full Documentation**:
- [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md) - Detailed deployment guide
- [walkthrough.md](walkthrough.md) - Complete changes made
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Smart contract deployment

🔧 **Helper Tools**:
- `./check-deployment.sh` - Check if you're ready to deploy

🌐 **Your URLs** (save these):
- Backend: `https://__________________.onrender.com`
- Frontend: `https://__________________.netlify.app`
- Contract: `https://coston2-explorer.flare.network/address/0x__________________`

---

## Need Help?

- **Render Issues**: https://render.com/docs
- **Netlify Issues**: https://docs.netlify.com
- **API Keys**: Check [CMC](https://coinmarketcap.com/api/) and [Gemini](https://ai.google.dev/) dashboards

---

**Estimated Total Time**: ~30 minutes (without smart contract), ~60 minutes (with smart contract)

🎯 **You're all set! Happy trading with VERDICT!** 🚀
