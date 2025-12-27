#!/usr/bin/env python3
"""
Tesla OAuth Setup Script

Run this script once to complete OAuth authentication with Tesla.
It will open a browser window for you to login to your Tesla account.
The authentication token will be cached for future use.

Usage:
    python scripts/setup_tesla.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config


def setup_tesla_auth():
    """Setup Tesla authentication via OAuth flow"""

    try:
        import teslapy
    except ImportError:
        print("ERROR: teslapy library not installed")
        print("Please run: pip install teslapy")
        sys.exit(1)

    print("=" * 60)
    print("Tesla OAuth Setup")
    print("=" * 60)
    print()

    # Get email from config
    email = config.tesla_email
    if not email or email == "din_email@example.com":
        email = input("Enter your Tesla account email: ").strip()
        if not email:
            print("ERROR: Email is required")
            sys.exit(1)

    # Ensure cache directory exists
    cache_file = Path(config.tesla_cache_file)
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nEmail: {email}")
    print(f"Cache file: {cache_file}")
    print()

    try:
        # Initialize Tesla API
        tesla = teslapy.Tesla(email, cache_file=str(cache_file))

        # Check if already authorized
        if tesla.authorized:
            print("✓ Already authenticated!")
            print("\nFetching vehicle list...")

            vehicles = tesla.vehicle_list()
            print(f"\nFound {len(vehicles)} vehicle(s):")
            for i, vehicle in enumerate(vehicles, 1):
                print(f"  {i}. {vehicle['display_name']} ({vehicle['vin']})")

            print("\n✓ Setup complete! You can now run the main application.")
            return

        # Start OAuth flow
        print("Starting OAuth flow...")
        print("\nA browser window will open shortly.")
        print("Please login to your Tesla account and authorize the application.")
        print("\nWaiting for authorization...")

        # This will open a browser window
        tesla.fetch_token()

        print("\n✓ Authentication successful!")
        print(f"Token saved to: {cache_file}")

        # Verify by fetching vehicles
        print("\nVerifying connection...")
        vehicles = tesla.vehicle_list()
        print(f"\nFound {len(vehicles)} vehicle(s):")
        for i, vehicle in enumerate(vehicles, 1):
            print(f"  {i}. {vehicle['display_name']} ({vehicle['vin']})")

        print("\n✓ Setup complete!")
        print("\nYou can now run the main application with:")
        print("  python main.py")
        print("\nNote: Set MOCK_MODE=false in .env to use real Tesla data")

    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you have an active internet connection")
        print("  2. Check that your Tesla account credentials are correct")
        print("  3. Try running the script again")
        sys.exit(1)


if __name__ == "__main__":
    setup_tesla_auth()
