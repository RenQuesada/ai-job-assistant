#!/usr/bin/env python3

"""
# Check OpenRouter API key info (OPENROUTER_API_KEY env var)
./check_credits.py

# Use specific API key by passing as an arg
./check_credits.py --key sk-or-v1-...

# Show raw JSON response
./check_credits.py --json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

USAGE = """
Usage: check_credits [options]

Options:
  -k, --key <api-key>       OpenRouter API key
  -j, --json                Output raw JSON response
  -h, --help                Show this help message

API Key Priority:
  1. --key command line argument
  2. OPENROUTER_API_KEY environment variable

Examples:
  check_credits
  check_credits --key sk-or-v1-...
  check_credits --json
"""

# https://openrouter.ai/docs/api/reference/limits
OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/key"


def get_api_key(cli_key):
    """Gets API key from various sources in priority order."""
    return (
        cli_key
        or os.environ.get("OPENROUTER_API_KEY")
        or None
    )


def fetch_key_info(api_key):
    """Fetches key information from OpenRouter API."""
    try:
        req = urllib.request.Request(
            OPENROUTER_KEY_URL,
            method="GET",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        if e.code == 401:
            msg = "Unauthorized - Invalid API key or authentication required"
        elif e.code == 403:
            msg = "Forbidden - Access denied"
        elif e.code == 500:
            msg = "Internal Server Error - Please try again"
        else:
            msg = f"Failed to fetch key info: {e.code} {e.reason}"
        print(f"Error fetching key info: {msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching key info: {e}", file=sys.stderr)
        sys.exit(1)


def format_currency(amount):
    """
    Formats currency amount (OpenRouter credits are always USD).
    """
    # Use up to 6 decimal places, minimum 2
    if amount == int(amount):
        formatted = f"${amount:,.2f}"
    else:
        # Format with up to 6 decimal places,
        # stripping trailing zeros but keeping min 2
        formatted = f"${amount:,.6f}"
        # Strip trailing zeros but keep at least 2
        # decimal places
        integer_part, decimal_part = formatted.split(".")
        decimal_part = decimal_part.rstrip("0")
        if len(decimal_part) < 2:
            decimal_part = decimal_part.ljust(2, "0")
        formatted = f"{integer_part}.{decimal_part}"
    return f"{formatted} (USD)"


def format_key_display(response):
    """Formats the key data for human-readable output."""
    lines = []

    lines.append("OpenRouter API Key Information\n")
    lines.append("=" * 60)

    data = response.get("data")

    if not data:
        lines.append("No key data available")
        lines.append("=" * 60)
        return "\n".join(lines)

    # Key label
    if data.get("label"):
        lines.append(f"Key Label:         {data['label']}")
        lines.append("")

    # Credit limit information
    lines.append("CREDIT LIMITS")
    lines.append("-" * 60)

    if data.get("limit") is None:
        lines.append("Credit Limit:      Unlimited")
    else:
        lines.append(
            f"Credit Limit:      "
            f"{format_currency(data['limit'])}"
        )

    if data.get("limit_remaining") is None:
        lines.append("Remaining:         Unlimited")
    else:
        lines.append(
            f"Remaining:         "
            f"{format_currency(data['limit_remaining'])}"
        )

        # Calculate percentage used
        if (
            data.get("limit") is not None
            and data["limit"] > 0
        ):
            percent_used = (
                (data["limit"] - data["limit_remaining"])
                / data["limit"]
                * 100
            )
            lines.append(
                f"Used:              "
                f"{percent_used:.2f}%"
            )

    lines.append("")

    # Usage information
    lines.append("USAGE (OPENROUTER MODELS)")
    lines.append("-" * 60)
    lines.append(
        f"All Time:          "
        f"{format_currency(data['usage'])}"
    )
    lines.append(
        f"Today (UTC):       "
        f"{format_currency(data['usage_daily'])}"
    )
    lines.append(
        f"This Week (UTC):   "
        f"{format_currency(data['usage_weekly'])}"
    )
    lines.append(
        f"This Month (UTC):  "
        f"{format_currency(data['usage_monthly'])}"
    )

    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check OpenRouter API key credits",
        add_help=True,
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        default=None,
        help="OpenRouter API key",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON response",
    )

    args = parser.parse_args()

    api_key = get_api_key(args.key)

    if not api_key:
        print("Error: No API key provided\n", file=sys.stderr)
        print("Please provide an API key using one of these methods:", file=sys.stderr)
        print("  1. --key command line argument", file=sys.stderr)
        print("  2. OPENROUTER_API_KEY environment variable", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  check_credits --key sk-or-v1-...", file=sys.stderr)
        print("  OPENROUTER_API_KEY=sk-or-v1-... check_credits", file=sys.stderr)
        sys.exit(1)

    # Mask the API key in output (e.g., "sk-or-v1-...98c6")
    if len(api_key) > 14:
        masked_key = f"{api_key[:9]}...{api_key[-4:]}"
    else:
        masked_key = "***"

    if not args.json:
        print(f"Using API key: {masked_key}\n", file=sys.stderr)

    response = fetch_key_info(api_key)

    if args.json:
        print(json.dumps(response, indent=2))
    else:
        print(format_key_display(response))


if __name__ == "__main__":
    main()