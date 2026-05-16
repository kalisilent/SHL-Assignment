# Render Deployment Guide

This guide walks you through deploying the SHL Assessment Recommender Agent to Render.

## Prerequisites

- Render account (free tier available): https://render.com
- GitHub account with this repo
- Google Gemini API key (free tier: https://ai.google.dev)

## Step 1: Prepare Environment Variables

You'll need these environment variables set in Render:

```
GEMINI_API_KEY=<your-gemini-api-key>
FORCE_RETRIEVER_ONLY=0
```

Get your Gemini API key:
1. Go to https://ai.google.dev
2. Click "Get API Key"
3. Create or select a project
4. Copy your API key

## Step 2: Deploy to Render (Web Service)

### Option A: Using Render Web Dashboard (Easiest)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **"Web Service"**
3. **Connect GitHub**:
   - Click "Connect account" → authorize GitHub
   - Select your repository: `kalisilent/SHL-Assignment`
   - Branch: `main`
4. **Configure**:
   - **Name**: `shl-assessment-agent` (or your choice)
   - **Environment**: `Docker`
   - **Region**: Leave default (or nearest to you)
   - **Branch**: `main`
   - **Build Command**: (leave empty - uses Dockerfile)
   - **Start Command**: (leave empty - uses Dockerfile)
5. **Environment Variables** (click "Add from file" or add manually):
   ```
   GEMINI_API_KEY = <your-api-key>
   FORCE_RETRIEVER_ONLY = 0
   ```
6. **Click "Create Web Service"**
7. **Wait** (first deploy takes 5-10 minutes)

### Option B: Using Render CLI

```bash
# Install Render CLI (if needed)
npm install -g @render-oss/cli

# Or via Homebrew
brew install render

# Login
render login

# Deploy
render deploy --repo https://github.com/kalisilent/SHL-Assignment \
  --branch main \
  --name shl-assessment-agent \
  --env GEMINI_API_KEY=<your-api-key>
```

## Step 3: Monitor Deployment

In Render dashboard:
- **Logs**: Watch for startup messages and errors
- **Expected logs**:
  ```
  Starting up: Loading FAISS index and initializing Agent...
  System Ready!
  Uvicorn running on 0.0.0.0:8000
  ```
- **Cold start**: First request takes ~30-60s (FAISS loading). Subsequent requests are fast.

## Step 4: Test Your Deployment

Once the deployment shows "Live" (green dot), test it:

```bash
# Get your service URL from Render dashboard
# It looks like: https://shl-assessment-agent-xxxx.onrender.com

# Test health endpoint
curl https://shl-assessment-agent-xxxx.onrender.com/health

# Expected response:
# {"status":"ok"}

# Test chat endpoint
curl -X POST https://shl-assessment-agent-xxxx.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I need to hire a Java developer"}
    ]
  }'
```

## Step 5: Update Submission

Once your URL is live:

1. **Update** `SUBMISSION_PACKAGE_URL.md`:
   ```markdown
   - **Public API**: https://shl-assessment-agent-xxxx.onrender.com
   - **Health check**: https://shl-assessment-agent-xxxx.onrender.com/health
   - **Chat endpoint**: https://shl-assessment-agent-xxxx.onrender.com/chat
   ```

2. **Commit and push**:
   ```bash
   git add SUBMISSION_PACKAGE_URL.md
   git commit -m "Update with deployed Render URL"
   git push origin main
   ```

## Troubleshooting

### Service won't start

**Error**: `ModuleNotFoundError` or dependency issues
- **Fix**: Ensure all dependencies are in `requirements.txt`
- Check Dockerfile runs successfully

### Timeout (30s limit for /chat calls)

**Error**: Requests taking >30 seconds
- **Why**: FAISS indexing on cold start takes time
- **Fix**: The lifespan function loads FAISS once at startup, not per-request. Should be OK.
- **Verify**: Check app/main.py lines 10-17 ensure lifespan loads everything once.

### Out of memory

**Error**: Service crashes after a few requests
- **Why**: FAISS + transformers are memory-intensive
- **Fix**: Render free tier has 1GB. If needed, upgrade to Starter ($7/mo, 2GB RAM).

### API key not recognized

**Error**: "API key invalid" from Gemini
- **Fix**: Double-check the API key in Render environment variables
- Ensure it's in quotes if it contains special chars: `GEMINI_API_KEY = "sk-..."`

## Next Steps After Deployment

1. **Verify health** (cold start may take ~2 min):
   ```bash
   curl https://your-url/health
   ```

2. **Run evaluation** against your endpoint:
   ```bash
   python3 scripts/run_agent_eval.py https://your-url/chat
   ```

3. **Submit**:
   - URL: `https://your-url`
   - PDF: `Approach_Document.pdf`
   - External zip link: [set in SUBMISSION_PACKAGE_URL.md]

---

**Questions?** Check:
- Render docs: https://render.com/docs
- FastAPI docs: https://fastapi.tiangolo.com
- Gemini API: https://ai.google.dev/docs
