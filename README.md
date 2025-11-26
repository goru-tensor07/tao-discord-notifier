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

