#!/usr/bin/env python3
"""
Tesla Fleet API OAuth Setup Script

This script completes the OAuth 2.0 flow for Tesla Fleet API.
Run this once to obtain access and refresh tokens.

Usage:
    python scripts/setup_tesla_fleet.py
"""

import sys
import secrets
import hashlib
import base64
import json
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
import httpx


# Tesla Fleet API endpoints
AUTH_URL = "https://auth.tesla.com/oauth2/v3"
API_URL = "https://fleet-api.prd.na.vn.cloud.tesla.com"
REDIRECT_URI = "http://localhost:8000/callback"


def generate_pkce_challenge():
    """Generate PKCE code verifier and challenge"""
    # Generate code verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    # Generate code challenge (SHA256 hash of verifier)
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


def get_authorization_url(client_id: str, code_challenge: str, state: str) -> str:
    """Generate authorization URL"""
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid offline_access vehicle_device_data vehicle_cmds vehicle_charging_cmds',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'prompt': 'login'  # Force login to show consent screen
    }

    return f"{AUTH_URL}/authorize?{urlencode(params)}"


def exchange_code_for_token(
    client_id: str,
    client_secret: str,
    code: str,
    code_verifier: str
) -> dict:
    """Exchange authorization code for access token"""
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }

    response = httpx.post(
        f"{AUTH_URL}/token",
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if response.status_code != 200:
        raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")

    return response.json()


def save_tokens(token_data: dict, cache_file: Path):
    """Save tokens to cache file"""
    # Calculate expiration time
    from datetime import datetime, timedelta
    expires_in = token_data.get('expires_in', 3600)
    expires_at = datetime.now() + timedelta(seconds=expires_in)

    cache_data = {
        'access_token': token_data['access_token'],
        'refresh_token': token_data.get('refresh_token'),
        'expires_at': expires_at.isoformat(),
        'vehicle_id': None  # Will be populated on first API call
    }

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)

    print(f"✓ Tokens saved to: {cache_file}")


def main():
    print("=" * 60)
    print("Tesla Fleet API OAuth Setup")
    print("=" * 60)
    print()

    # Check configuration
    if not config.tesla_client_id or config.tesla_client_id == "din_client_id_her":
        print("ERROR: TESLA_CLIENT_ID not configured in .env")
        print("\nPlease edit .env and add your Tesla Developer credentials:")
        print("  TESLA_CLIENT_ID=your_client_id")
        print("  TESLA_CLIENT_SECRET=your_client_secret")
        sys.exit(1)

    if not config.tesla_client_secret or config.tesla_client_secret == "din_client_secret_her":
        print("ERROR: TESLA_CLIENT_SECRET not configured in .env")
        print("\nPlease edit .env and add your Tesla Developer credentials:")
        print("  TESLA_CLIENT_ID=your_client_id")
        print("  TESLA_CLIENT_SECRET=your_client_secret")
        sys.exit(1)

    print("Configuration:")
    print(f"  Client ID: {config.tesla_client_id[:20]}...")
    print(f"  Redirect URI: {REDIRECT_URI}")
    print()

    # Generate PKCE parameters
    code_verifier, code_challenge = generate_pkce_challenge()
    state = secrets.token_urlsafe(32)

    # Generate authorization URL
    auth_url = get_authorization_url(config.tesla_client_id, code_challenge, state)

    print("Opening Tesla login in your browser...")
    print()
    print("After logging in and authorizing:")
    print("1. You will be redirected to localhost (may show 'Page Not Found')")
    print("2. Copy the ENTIRE URL from the browser address bar")
    print("3. Paste it below")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for user to paste callback URL
    print("Waiting for authorization...")
    callback_url = input("\nPaste the callback URL here: ").strip()

    if not callback_url:
        print("ERROR: No URL provided")
        sys.exit(1)

    # Parse callback URL
    try:
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)

        # Verify state
        returned_state = params.get('state', [None])[0]
        if returned_state != state:
            print("ERROR: State mismatch - possible security issue")
            sys.exit(1)

        # Get authorization code
        auth_code = params.get('code', [None])[0]
        if not auth_code:
            error = params.get('error', ['unknown'])[0]
            error_desc = params.get('error_description', [''])[0]
            print(f"ERROR: Authorization failed: {error}")
            if error_desc:
                print(f"  {error_desc}")
            sys.exit(1)

        print("\n✓ Authorization code received")

    except Exception as e:
        print(f"ERROR: Failed to parse callback URL: {e}")
        sys.exit(1)

    # Exchange code for token
    print("Exchanging code for access token...")
    try:
        token_data = exchange_code_for_token(
            config.tesla_client_id,
            config.tesla_client_secret,
            auth_code,
            code_verifier
        )

        print("✓ Access token received")

    except Exception as e:
        print(f"\n✗ Token exchange failed: {e}")
        sys.exit(1)

    # Save tokens
    cache_file = Path(config.tesla_cache_file)
    save_tokens(token_data, cache_file)

    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Set MOCK_MODE=false in .env to use real Tesla data")
    print("2. Run: python main.py")
    print("3. Open http://localhost:8000")
    print()
    print("Your tokens are saved and will be automatically refreshed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
