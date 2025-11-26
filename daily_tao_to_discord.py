"""Post daily TAO earnings to a Discord webhook.

This script:
- Fetches TAO income for one or more coldkeys from the Taostats accounting API
- Fetches alpha staked balances with subnet information
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
from typing import List, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

import requests

# --- Environment configuration ---

if load_dotenv is not None:
    load_dotenv()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TAOSTATS_API_KEY = os.environ.get("TAOSTATS_API_KEY")
TAOSTATS_BASE_URL = os.environ.get("TAOSTATS_BASE_URL", "https://api.taostats.io/api")
MINER_ADDRESSES = os.environ.get("MINER_ADDRESSES")
LOOKBACK_DAYS = int(os.environ.get("TAO_LOOKBACK_DAYS", "10"))
TAO_NETWORK = os.environ.get("TAO_NETWORK", "finney")
DEBUG_MODE = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

# Constants
RAO_TO_TAO = 10**9  # 1 TAO = 1e9 RAO
API_TIMEOUT = 30

# Alpha token symbol mapping by netuid
# Each subnet has its own alpha token symbol
ALPHA_TOKEN_SYMBOLS: dict[int, str] = {
    41: "נ",  # Subnet 41
    64: "ش",  # Subnet 64
    # Add more subnet symbols as needed
}


@dataclass(frozen=True)
class MinerEarning:
    """Represents TAO earnings for a coldkey."""
    coldkey: str
    amount_tao: float


@dataclass(frozen=True)
class AlphaStakeBalance:
    """Represents alpha staked balance for a subnet."""
    netuid: int
    balance_rao: str
    balance_as_tao: str
    hotkey_name: Optional[str] = None


class DailyTaoReporter:
    """Main reporter class for fetching and posting TAO earnings to Discord."""

    def __init__(self) -> None:
        """Initialize reporter and validate required environment variables."""
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate all required configuration."""
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

    def _get_headers(self) -> dict[str, str]:
        """Get API request headers."""
        return {
            "accept": "application/json",
            "authorization": TAOSTATS_API_KEY,
        }

    def _get_accounting_endpoint(self) -> str:
        """Get the accounting API endpoint URL."""
        return f"{TAOSTATS_BASE_URL.rstrip('/')}/accounting/v1"

    def _get_date_range(self) -> tuple[Optional[str], Optional[str], Optional[date], date]:
        """Calculate date range for earnings query.
        
        Returns:
            Tuple of (date_start_str, date_end_str, start_date, end_date).
            If LOOKBACK_DAYS <= 0, returns (None, None, None, None) for all-time query.
        """
        if LOOKBACK_DAYS <= 0:
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

    def _make_api_request(self, url: str) -> dict:
        """Make an API request and return parsed JSON response.
        
        Args:
            url: Full API URL to request
            
        Returns:
            Parsed JSON response as dictionary
            
        Raises:
            RuntimeError: If API request fails or returns invalid JSON
        """
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"API request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON response from API: {exc}") from exc

    def fetch_earnings(self) -> List[MinerEarning]:
        """Fetch TAO earnings for configured coldkeys.
        
        Returns:
            List of MinerEarning objects containing coldkey and earnings amount
        """
        url = (
            f"https://api.taostats.io/api/account/latest/v1"
            f"?address={MINER_ADDRESSES}&network={TAO_NETWORK}&page=1&limit=50"
        )
        
        try:
            res_json = self._make_api_request(url)
            data = res_json.get("data", [])
            
            if not data:
                if DEBUG_MODE:
                    print(f"⚠️  No earnings data found for {MINER_ADDRESSES[:20]}...", file=sys.stderr)
                return [MinerEarning(coldkey=MINER_ADDRESSES, amount_tao=0.0)]
            
            # Extract balance_staked from first record
            first_record = data[0]
            balance_staked = first_record.get("balance_staked", "0")
            balance_tao = float(balance_staked) / RAO_TO_TAO if balance_staked else 0.0
            
            return [MinerEarning(coldkey=MINER_ADDRESSES, amount_tao=balance_tao)]
            
        except Exception as exc:
            if DEBUG_MODE:
                print(f"🔍 Debug: Error fetching earnings: {exc}", file=sys.stderr)
            raise

    def fetch_alpha_rewards(self) -> List[AlphaStakeBalance]:
        """Fetch alpha staked balances with subnet information.
        
        Returns:
            List of AlphaStakeBalance objects containing netuid and balance information
        """
        url = f"https://api.taostats.io/api/dtao/stake_balance/latest/v1?coldkey={MINER_ADDRESSES}"
        
        try:
            res_json = self._make_api_request(url)
            data = res_json.get("data", [])
            if not data:
                if DEBUG_MODE:
                    print(f"⚠️  No alpha stake data found for {MINER_ADDRESSES[:20]}...", file=sys.stderr)
                return []
            
            alpha_balances = []
            for item in data:
                netuid = item.get("netuid")
                balance = item.get("balance", "0")
                balance_as_tao = item.get("balance_as_tao", "0")
                hotkey_name = item.get("hotkey_name")
                
                if netuid is not None:
                    alpha_balances.append(
                        AlphaStakeBalance(
                            netuid=netuid,
                            balance_rao=balance,
                            balance_as_tao=balance_as_tao,
                            hotkey_name=hotkey_name,
                        )
                    )
            
            if DEBUG_MODE:
                print(f"🔍 Debug: Found {len(alpha_balances)} alpha stake records", file=sys.stderr)
            
            return alpha_balances
            
        except Exception as exc:
            if DEBUG_MODE:
                print(f"🔍 Debug: Error fetching alpha rewards: {exc}", file=sys.stderr)
            return []

    def build_message(
        self, 
        earnings: List[MinerEarning], 
        alpha_balances: Optional[List[AlphaStakeBalance]] = None
    ) -> str:
        """Build formatted Discord message from earnings and alpha balances.
        
        Args:
            earnings: List of TAO earnings
            alpha_balances: Optional list of alpha staked balances
            
        Returns:
            Formatted message string for Discord
        """
        date_start_str, date_end_str, start_date, end_date = self._get_date_range()

        # Build header based on time range
        if LOOKBACK_DAYS <= 0:
            header = "📊 Total TAO Earnings (All Time)"
        elif LOOKBACK_DAYS == 1:
            header = f"📊 Daily TAO Earnings — {end_date.isoformat() if end_date else 'N/A'}"
        else:
            header = f"📊 TAO Earnings — {date_start_str} → {date_end_str}"

        lines = [header, f"Network: **{TAO_NETWORK}**", ""]

        # Add earnings section
        if earnings:
            lines.append("**💰 TAO Earnings:**")
            total_earnings = 0.0
            for entry in earnings:
                total_earnings += entry.amount_tao
                lines.append(f"• `{entry.coldkey[:20]}...`: **{entry.amount_tao:.6f} TAO**")
            
            lines.append(f"**Total Earnings:** {total_earnings:.6f} TAO across {len(earnings)} coldkey(s)")
            lines.append("")
        else:
            lines.append("**💰 TAO Earnings:** No earnings data available.")
            lines.append("")

        # Add alpha staked balances section
        if alpha_balances:
            lines.append("**🔷 Alpha Staked Balances:**")
            total_alpha_tao = 0.0
            
            for balance in alpha_balances:
                balance_tao = float(balance.balance_rao) / RAO_TO_TAO
                total_alpha_tao += balance_tao
                
                # Get alpha token symbol for this subnet, default to "α" if not found
                token_symbol = ALPHA_TOKEN_SYMBOLS.get(balance.netuid, "α")
                hotkey_info = f" ({balance.hotkey_name})" if balance.hotkey_name else ""
                lines.append(
                    f"• Subnet **{balance.netuid}**{hotkey_info}: "
                    f"**{balance_tao:.4f} {token_symbol}**"
                )
            
            
        else:
            lines.append("**🔷 Alpha Staked Balances:** No alpha stake data available.")

        return "\n".join(lines)

    def post_to_discord(self, content: str) -> None:
        """Post message to Discord webhook.
        
        Args:
            content: Message content to post
            
        Raises:
            RuntimeError: If webhook URL is invalid or request fails
        """
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
            with urllib.request.urlopen(request, timeout=API_TIMEOUT) as response:
                status = response.getcode()
                response_body = response.read().decode("utf-8")
                if status not in (200, 204):
                    raise RuntimeError(
                        f"Discord returned status {status}: {response_body}"
                    )
        except urllib.error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                pass

            error_msg = f"HTTP {exc.code}: {exc.reason}"
            if error_body:
                error_msg += f" - {error_body}"

            if exc.code == 403:
                error_msg += (
                    "\nPossible causes:"
                    "\n  - Webhook URL is invalid or expired"
                    "\n  - Webhook was deleted from Discord server"
                    "\n  - Check your .env file has the correct DISCORD_WEBHOOK_URL"
                    "\n  - Create a new webhook in Discord: Server Settings → Integrations → Webhooks"
                )
            elif exc.code == 404:
                error_msg += "\nWebhook not found. The webhook may have been deleted."

            raise RuntimeError(f"Failed to send Discord message: {error_msg}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Network error connecting to Discord: {exc.reason}"
            ) from exc

        print(f"✅ Message sent to Discord (status {status})")

    def run(self) -> int:
        """Main execution method.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            earnings = self.fetch_earnings()
            alpha_balances = self.fetch_alpha_rewards()
            message = self.build_message(earnings, alpha_balances)
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
    """Entry point for the script."""
    sys.exit(DailyTaoReporter().run())


if __name__ == "__main__":
    main()
