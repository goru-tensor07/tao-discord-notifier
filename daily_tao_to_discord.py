"""Post daily TAO earnings to a Discord webhook.

This script:
- Fetches TAO income for one or more coldkeys from the Taostats accounting API
- Aggregates earnings over a lookback window (in days)
- Posts a summary message to a Discord webhook

It is designed to run from GitHub Actions on a schedule.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import List
import requests
try:
    from dotenv import load_dotenv
except ImportError:
    # dotenv is optional - script will work with environment variables only
    load_dotenv = None

# --- Environment configuration ---

# Load .env file if python-dotenv is available
if load_dotenv is not None:
    load_dotenv()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TAOSTATS_API_KEY = os.environ.get("TAOSTATS_API_KEY")

# Default to the same base used in the Taostats notebook examples
TAOSTATS_BASE_URL = os.environ.get("TAOSTATS_BASE_URL", "https://api.taostats.io/api")

# Comma-separated list of coldkeys
MINER_ADDRESSES = os.environ.get("MINER_ADDRESSES")
print(MINER_ADDRESSES)
# Number of days to look back (e.g., 1 = "yesterday to today")
# Set to 0 or negative to query all available data (total/cumulative earnings)
# Set to a large number (e.g., 365) to get last year's data
LOOKBACK_DAYS = int(os.environ.get("TAO_LOOKBACK_DAYS", "10"))

# Network name used in the accounting API (finney / nakamoto / kusanagi)
TAO_NETWORK = os.environ.get("TAO_NETWORK", "finney")

# Debug mode - set to "1" or "true" to print API responses
DEBUG_MODE = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


@dataclass
class MinerEarning:
    coldkey: str
    amount_tao: float


class DailyTaoReporter:
    def __init__(self) -> None:
        if not DISCORD_WEBHOOK_URL:
            raise RuntimeError("DISCORD_WEBHOOK_URL environment variable is required")
        if not DISCORD_WEBHOOK_URL.startswith("https://discord.com/api/webhooks/"):
            raise RuntimeError(
                f"Invalid Discord webhook URL format. "
                f"Expected: https://discord.com/api/webhooks/... "
                f"Got: {DISCORD_WEBHOOK_URL[:60]}..."
            )
        if not TAOSTATS_API_KEY:
            raise RuntimeError("TAOSTATS_API_KEY environment variable is required")
        if not MINER_ADDRESSES:
            raise RuntimeError("MINER_ADDRESSES environment variable is required")

    # -------- Taostats API helpers --------

    def _headers(self) -> dict[str, str]:
        # Match the Taostats API style from extrinsics example:
        # headers = {"accept": "application/json", "Authorization": api_key}
        return {
            "accept": "application/json",
            "Authorization": TAOSTATS_API_KEY,
        }

    def _endpoint(self) -> str:
        # Accounting endpoint from the notebook:
        # https://api.taostats.io/api/accounting/v1
        return f"{TAOSTATS_BASE_URL.rstrip('/')}/accounting/v1"

    def _date_range(self) -> tuple[str | None, str | None, date | None, date]:
        """Return (date_start_str, date_end_str, start_date, end_date).
        
        If LOOKBACK_DAYS <= 0, returns (None, None, None, None) to query all data.
        """
        if LOOKBACK_DAYS <= 0:
            # Query all available data (no date restrictions)
            return (None, None, None, None)
        
        today_utc = datetime.now(timezone.utc).date()
        end_date = today_utc
        start_date = today_utc - timedelta(days=LOOKBACK_DAYS)

        return (
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            start_date,
            end_date,
        )

    def fetch_earnings(self) -> List[MinerEarning]:
        network = TAO_NETWORK
        page =1
        limit = 50
        #get current block
        url = f"https://api.taostats.io/api/account/latest/v1?address={MINER_ADDRESSES}&network={network}&page={page}&limit={limit}"
        headers = {"accept": "application/json", "authorization":TAOSTATS_API_KEY}
        response = requests.get(url, headers=headers)
        resJson = json.loads(response.text)
        data = resJson['data']
        address = data[0]
        balance_staked = address.get('balance_staked')
        earnings = [MinerEarning(coldkey=MINER_ADDRESSES, amount_tao=balance_staked)]
        print(earnings)
        return earnings

    # -------- Discord helpers --------

    def build_message(self, earnings: List[MinerEarning]) -> str:
        date_start_str, date_end_str, start_date, end_date = self._date_range()

        if LOOKBACK_DAYS <= 0:
            header = "📊 Total TAO Earnings (All Time)"
        elif LOOKBACK_DAYS == 1:
            header = f"📊 Daily TAO Earnings — {end_date.isoformat() if end_date else 'N/A'}"
        else:
            header = f"📊 TAO Earnings — {date_start_str} → {date_end_str}"

        if not earnings:
            return (
                f"{header}\n"
                f"Network: **{TAO_NETWORK}**\n"
                "No earnings data available for the configured coldkeys in this period."
            )

        lines = [
            header,
            f"Network: **{TAO_NETWORK}**",
            "",
        ]

        total = 0.0
        for entry in earnings:
            total += float(entry.amount_tao)
            lines.append(f"• `{entry.coldkey}`: **{(int(entry.amount_tao)/(10**9)):.2f} TAO**")

        lines.append("")
        lines.append(f"**Total:** {total/(10**9):.6f} TAO across {len(earnings)} coldkey(s)")

        return "\n".join(lines)

    def post_to_discord(self, content: str) -> None:
        # Validate webhook URL format
        if not DISCORD_WEBHOOK_URL or not DISCORD_WEBHOOK_URL.startswith("https://discord.com/api/webhooks/"):
            raise RuntimeError(
                f"Invalid Discord webhook URL format. "
                f"Expected: https://discord.com/api/webhooks/... "
                f"Got: {DISCORD_WEBHOOK_URL[:50] if DISCORD_WEBHOOK_URL else 'None'}..."
            )

        payload = json.dumps({"content": content}).encode("utf-8")
        request = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "DailyTaoReporter/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.getcode()
                # Read response body for debugging
                response_body = response.read().decode("utf-8")
                if status not in (200, 204):
                    raise RuntimeError(
                        f"Discord returned status {status}: {response_body}"
                    )
        except urllib.error.HTTPError as exc:
            # Try to read error response body for better diagnostics
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                pass

            error_msg = f"HTTP {exc.code}: {exc.reason}"
            if error_body:
                error_msg += f" - {error_body}"

            # Provide helpful suggestions based on error code
            if exc.code == 403:
                error_msg += (
                    "\nPossible causes:"
                    "\n  - Webhook URL is invalid or expired"
                    "\n  - Webhook was deleted from Discord server"
                    "\n  - Check your .env file has the correct DISCORD_WEBHOOK_URL"
                    "\n  - Create a new webhook in Discord: Server Settings → Integrations → Webhooks"
                )
            elif exc.code == 404:
                error_msg += (
                    "\nWebhook not found. The webhook may have been deleted."
                )

            raise RuntimeError(f"Failed to send Discord message: {error_msg}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Network error connecting to Discord: {exc.reason}"
            ) from exc

        print(f"✅ Message sent to Discord (status {status})")

    # -------- Main run --------

    def run(self) -> int:
        try:
            earnings = self.fetch_earnings()
            message = self.build_message(earnings)
        except Exception as exc:  # noqa: BLE001
            message = (
                "⚠️ Daily TAO Earnings — data unavailable\n"
                f"Reason: {exc}"
            )

        try:
            self.post_to_discord(message)
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to send Discord message: {exc}", file=sys.stderr)
            return 1

        return 0


def main() -> None:
    sys.exit(DailyTaoReporter().run())


if __name__ == "__main__":
    main()
