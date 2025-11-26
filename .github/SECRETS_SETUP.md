# GitHub Secrets Setup Guide

To use this GitHub Actions workflow, you need to configure the following secrets in your repository:

## Steps to Add Secrets:

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each of the following:

## Required Secrets:

### `DISCORD_WEBHOOK_URL`
- **Description**: Your Discord webhook URL
- **Format**: `https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz`
- **How to get**: 
  - Go to your Discord server
  - Server Settings → Integrations → Webhooks → New Webhook
  - Copy the webhook URL

### `TAOSTATS_API_KEY`
- **Description**: Your Taostats API key
- **Format**: Your API key string
- **How to get**: Get from Taostats API documentation or dashboard

### `MINER_ADDRESSES`
- **Description**: Comma-separated list of coldkey addresses
- **Format**: `5ABC...,5DEF...,5GHI...`
- **Example**: `5G3xHmDRz9yWDS9tnznWTVnyhCvLZiLUUbqFbRNEreGSCYgD`

## Optional Secrets:

### `TAO_LOOKBACK_DAYS`
- **Description**: Number of days to look back (default: 10)
- **Format**: Integer (e.g., `10`, `30`, `0` for all-time)

### `TAO_NETWORK`
- **Description**: Bittensor network name (default: finney)
- **Format**: `finney`, `nakamoto`, or `kusanagi`

### `DEBUG`
- **Description**: Enable debug mode (default: false)
- **Format**: `true` or `false`

## Verification:

After adding secrets, the workflow will:
- Run every 2 minutes automatically
- Use your configured secrets
- Post earnings reports to your Discord channel

## Testing:

You can manually trigger the workflow:
1. Go to **Actions** tab
2. Select **TAO Earnings Discord Reporter**
3. Click **Run workflow** → **Run workflow**

