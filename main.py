#!/usr/bin/env python3
"""
Ladeprioriteringssystem - Main Entry Point

Automatisk ladeprioriteringssystem for Tesla Model Y (MVP)
Kan senere utvides til å inkludere Hyundai Ioniq 5

Usage:
    python main.py

Configuration:
    Se .env.example for konfigurasjonsmuligheter
    Kopier .env.example til .env og tilpass verdiene

Første gangs oppsett (ekte Tesla data):
    1. Sett TESLA_EMAIL i .env
    2. Kjør: python scripts/setup_tesla.py
    3. Sett MOCK_MODE=false i .env
    4. Kjør: python main.py

Testing med mock data:
    1. La MOCK_MODE=true i .env (default)
    2. Kjør: python main.py
"""

import sys
import asyncio
from pathlib import Path

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).parent))


def check_python_version():
    """Ensure Python version is 3.9 or higher"""
    if sys.version_info < (3, 9):
        print("ERROR: Python 3.9 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []

    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")

    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")

    try:
        import pydantic
    except ImportError:
        missing.append("pydantic")

    try:
        import sqlalchemy
    except ImportError:
        missing.append("sqlalchemy")

    if missing:
        print("ERROR: Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


def create_env_if_needed():
    """Create .env file from .env.example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        print("✓ .env file created")
        print("\nPlease review .env and update settings as needed.")
        print("For Tesla integration, run: python scripts/setup_tesla.py\n")


def main():
    """Main entry point"""

    print("=" * 60)
    print("Ladeprioriteringssystem")
    print("Tesla Model Y MVP")
    print("=" * 60)
    print()

    # Check requirements
    check_python_version()
    check_dependencies()
    create_env_if_needed()

    # Import here after dependency check
    import uvicorn
    from config import config

    # Display configuration
    print("Configuration:")
    print(f"  Tesla Mock Mode: {config.tesla_mock_mode}")
    print(f"  Ioniq Mock Mode: {config.ioniq_mock_mode}")
    print(f"  Host: {config.host}")
    print(f"  Port: {config.port}")
    print(f"  Update Interval: {config.update_interval_minutes} min")
    print(f"  Charge Threshold: {config.charge_threshold_percent}%")
    print(f"  Database: {config.database_path}")
    print(f"  Log Level: {config.log_level}")
    print()

    if config.tesla_mock_mode:
        print("⚠️  Tesla running in MOCK MODE - using simulated data")
        print("   To use real Tesla API:")
        print("   1. Run: python scripts/setup_tesla.py")
        print("   2. Set TESLA_MOCK_MODE=false in .env")
    if config.ioniq_mock_mode:
        print("⚠️  Ioniq running in MOCK MODE - using simulated data")
        print("   To use real OBD-II data:")
        print("   1. Connect OBD-II adapter")
        print("   2. Set IONIQ_MOCK_MODE=false in .env")
        print()

    print("Starting server...")
    print("=" * 60)
    print()

    try:
        # Start FastAPI server
        uvicorn.run(
            "api.app:app",
            host=config.host,
            port=config.port,
            log_level=config.log_level.lower(),
            access_log=False  # We have our own logging
        )

    except KeyboardInterrupt:
        print("\n\nShutdown requested by user (Ctrl+C)")
        print("Goodbye!")

    except Exception as e:
        print(f"\n✗ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
