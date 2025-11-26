# Bittensor TAO Earnings Discord Reporter

Automated daily TAO earnings reporter for Bittensor miners. Fetches earnings data from the Taostats API and posts summaries to Discord via webhook.

## Features

- 📊 Fetches TAO earnings for multiple coldkeys from Taostats accounting API
- 📅 Configurable lookback period (daily, weekly, or all-time)
- 🔄 Supports multiple Bittensor networks (Finney, Nakamoto, Kusanagi)
- 📱 Posts formatted earnings reports to Discord webhook
- ⚙️ Designed for automated execution via GitHub Actions or cron

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bittensor-tao-earnings-reporter.git
cd bittensor-tao-earnings-reporter
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Configuration

Create a `.env` file in the project root:

```env
# Required
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
TAOSTATS_API_KEY=your-taostats-api-key
MINER_ADDRESSES=5ABC...,5DEF...,5GHI...

# Optional
TAO_LOOKBACK_DAYS=10          # Days to look back (0 = all time)
TAO_NETWORK=finney            # Network: finney, nakamoto, or kusanagi
TAOSTATS_BASE_URL=https://api.taostats.io/api
DEBUG=false                   # Enable debug mode
```

## Usage

### Run locally:
```bash
python daily_tao_to_discord.py
```

### Run with GitHub Actions (Automated):

The repository includes a GitHub Actions workflow that runs automatically.

#### Option 1: GitHub Actions (5-minute minimum)

**Limitation:** GitHub Actions has a **5-minute minimum** for scheduled workflows.

**Setup:**

1. **Add GitHub Secrets:**
   - Go to your repository → **Settings** → **Secrets and variables** → **Actions**
   - Add the following secrets:
     - `DISCORD_WEBHOOK_URL` - Your Discord webhook URL
     - `TAOSTATS_API_KEY` - Your Taostats API key
     - `MINER_ADDRESSES` - Comma-separated coldkey addresses
     - `TAO_LOOKBACK_DAYS` (optional) - Default: 10
     - `TAO_NETWORK` (optional) - Default: finney
     - `DEBUG` (optional) - Default: false

2. **Workflow will automatically:**
   - Run every 5 minutes (GitHub minimum)
   - Fetch earnings data
   - Post to Discord webhook

3. **Manual trigger:**
   - Go to **Actions** tab → **TAO Earnings Discord Reporter** → **Run workflow**

#### Option 2: Server Cron Job (True 2-minute intervals)

For true 2-minute intervals, use a cron job on your server:

1. **Set up environment variables** in your `.env` file (see Configuration section)

2. **Add to crontab:**
   ```bash
   crontab -e
   # Add this line:
   */2 * * * * /path/to/daily-tao-script/cron-2min.sh
   ```

3. **Or use the provided script:**
   ```bash
   chmod +x cron-2min.sh
   # Then add to crontab:
   */2 * * * * /full/path/to/cron-2min.sh >> /var/log/tao-reporter.log 2>&1
   ```

**Note:** See `.github/SECRETS_SETUP.md` for detailed GitHub Secrets setup instructions.


## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | Yes | - | Discord webhook URL |
| `TAOSTATS_API_KEY` | Yes | - | Taostats API key |
| `MINER_ADDRESSES` | Yes | - | Comma-separated list of coldkey addresses |
| `TAO_LOOKBACK_DAYS` | No | `10` | Number of days to look back (0 = all time) |
| `TAO_NETWORK` | No | `finney` | Bittensor network name |
| `TAOSTATS_BASE_URL` | No | `https://api.taostats.io/api` | Taostats API base URL |
| `DEBUG` | No | `false` | Enable debug logging |



## Requirements

- Python 3.9+
- `python-dotenv` (optional, for `.env` file support)

