#!/usr/bin/env python3
"""
Tesla Fleet API Account Registration

This script registers your application with Tesla Fleet API in your region.
This is a one-time setup step required before you can access vehicle data.

Usage:
    python scripts/register_tesla_account.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
import httpx


API_URL = "https://fleet-api.prd.eu.vn.cloud.tesla.com"  # EU region


def get_partner_token(client_id: str, client_secret: str) -> str:
    """Get partner authentication token using client credentials"""
    print("Getting partner authentication token...")

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'openid vehicle_device_data vehicle_cmds vehicle_charging_cmds vehicle_location',
        'audience': API_URL
    }

    response = httpx.post(
        "https://auth.tesla.com/oauth2/v3/token",
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30.0
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get partner token: {response.status_code} - {response.text}")

    token_data = response.json()
    print("✓ Partner token obtained")
    return token_data['access_token']


def register_account(access_token: str):
    """Register partner account in the region"""
    print("Registering application with Tesla Fleet API...")
    print()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # POST to partner_accounts endpoint
    # Using GitHub Pages URL
    response = httpx.post(
        f"{API_URL}/api/1/partner_accounts",
        headers=headers,
        json={
            'domain': 'iggisigg.github.io'
        },
        timeout=30.0
    )

    if response.status_code == 200 or response.status_code == 201:
        print("✓ Application registered successfully!")
        print()
        data = response.json()
        print("Registration details:")
        print(f"  Domain: {data.get('domain', 'N/A')}")
        print(f"  Public Key: {data.get('public_key', 'N/A')[:50]}...")
        return True

    elif response.status_code == 409:
        print("✓ Application already registered")
        print()
        return True

    else:
        print(f"✗ Registration failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def main():
    print("=" * 60)
    print("Tesla Fleet API - Account Registration")
    print("=" * 60)
    print()

    # Check if we have credentials
    if not config.tesla_client_id or config.tesla_client_id == "din_client_id_her":
        print("ERROR: TESLA_CLIENT_ID not configured in .env")
        sys.exit(1)

    if not config.tesla_client_secret or config.tesla_client_secret == "din_client_secret_her":
        print("ERROR: TESLA_CLIENT_SECRET not configured in .env")
        sys.exit(1)

    try:
        # Get partner authentication token using client credentials
        partner_token = get_partner_token(config.tesla_client_id, config.tesla_client_secret)

        # Register account using partner token
        success = register_account(partner_token)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        success = False

    if success:
        print()
        print("=" * 60)
        print("✓ Setup complete!")
        print("=" * 60)
        print()
        print("You can now use the Tesla Fleet API:")
        print("  python main.py")
        print()
        print("The dashboard will show real Tesla data at:")
        print("  http://localhost:8000")
    else:
        print()
        print("Registration failed. Please check:")
        print("1. Your OAuth tokens are valid (try running setup again)")
        print("2. Your Tesla Developer app has correct scopes")
        print("3. You're using the correct region endpoint")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
