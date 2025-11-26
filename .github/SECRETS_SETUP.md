# GitHub Secrets Setup Guide

**⚠️ IMPORTANT:** GitHub Actions uses **Secrets**, not `.env` files. You must add secrets in GitHub's web interface.

## Quick Setup (3 Steps):

### Step 1: Go to Secrets Page
1. Open your GitHub repository
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret** button

### Step 2: Add Required Secrets

Add these **3 required secrets** (one at a time):

#### 1. `DISCORD_WEBHOOK_URL`
- **Name:** `DISCORD_WEBHOOK_URL`
- **Value:** Your Discord webhook URL
- **Example:** `https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz`
- **How to get:**
  - Discord Server → Server Settings → Integrations → Webhooks
  - Click "New Webhook" or copy existing webhook URL
  - Copy the full URL

#### 2. `TAOSTATS_API_KEY`
- **Name:** `TAOSTATS_API_KEY`
- **Value:** Your Taostats API key
- **Example:** `your-api-key-here`
- **How to get:** From Taostats API documentation or dashboard

#### 3. `MINER_ADDRESSES`
- **Name:** `MINER_ADDRESSES`
- **Value:** Your coldkey address(es)
- **Example (single):** `5G3xHmDRz9yWDS9tnznWTVnyhCvLZiLUUbqFbRNEreGSCYgD`
- **Example (multiple):** `5ABC...,5DEF...,5GHI...` (comma-separated)

### Step 3: Add Optional Secrets (if needed)

These have defaults, but you can customize:

#### `TAO_LOOKBACK_DAYS`
- **Name:** `TAO_LOOKBACK_DAYS`
- **Value:** `10` (or any number, `0` for all-time)
- **Default:** `10` if not set

#### `TAO_NETWORK`
- **Name:** `TAO_NETWORK`
- **Value:** `finney`, `nakamoto`, or `kusanagi`
- **Default:** `finney` if not set

#### `DEBUG`
- **Name:** `DEBUG`
- **Value:** `true` or `false`
- **Default:** `false` if not set

## Visual Guide:

```
Repository → Settings → Secrets and variables → Actions
    ↓
New repository secret
    ↓
Name: DISCORD_WEBHOOK_URL
Secret: https://discord.com/api/webhooks/...
    ↓
Add secret
    ↓
Repeat for TAOSTATS_API_KEY and MINER_ADDRESSES
```

## Verification:

After adding all secrets:

1. Go to **Actions** tab
2. Click **TAO Earnings Discord Reporter** workflow
3. Click **Run workflow** → **Run workflow** (to test)
4. Check the run logs - should see "✅ All required secrets are configured"

## Troubleshooting:

### Error: "DISCORD_WEBHOOK_URL environment variable is required"
- **Solution:** Make sure you added the secret with the exact name `DISCORD_WEBHOOK_URL`
- Check: Settings → Secrets and variables → Actions → You should see all 3 required secrets listed

### Error: "ModuleNotFoundError: No module named 'requests'"
- **Solution:** Already fixed in `requirements.txt` - make sure you've pushed the latest code

### Workflow not running automatically
- **Solution:** Scheduled workflows only run on the default branch (usually `main`)
- Make sure your workflow file is in `.github/workflows/` directory
- Push to `main` branch to activate the schedule

## Security Notes:

- ✅ Secrets are encrypted and only visible to repository admins
- ✅ Secrets are never exposed in logs (GitHub automatically masks them)
- ✅ Never commit `.env` files or API keys to the repository
- ✅ Use GitHub Secrets for all sensitive data
