#!/usr/bin/env python3
"""
Generate EC keys for Tesla Fleet API partner registration

This script generates:
- Private key (keep secret, never share)
- Public key (upload to your website)

The keys use secp256r1 curve as required by Tesla.
"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path


def generate_keys():
    """Generate EC key pair for Tesla Fleet API"""
    print("=" * 60)
    print("Tesla Fleet API - Key Generation")
    print("=" * 60)
    print()

    # Generate private key using secp256r1 curve (required by Tesla)
    print("Generating EC key pair (secp256r1 curve)...")
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Generate public key from private key
    public_key = private_key.public_key()

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Create keys directory
    keys_dir = Path("data/keys")
    keys_dir.mkdir(parents=True, exist_ok=True)

    # Save private key (KEEP SECRET!)
    private_key_file = keys_dir / "private_key.pem"
    with open(private_key_file, 'wb') as f:
        f.write(private_pem)
    print(f"✓ Private key saved to: {private_key_file}")
    print("  ⚠️  KEEP THIS FILE SECRET - Never share or commit to git!")

    # Save public key (this will be uploaded to your website)
    public_key_file = keys_dir / "com.tesla.3p.public-key.pem"
    with open(public_key_file, 'wb') as f:
        f.write(public_pem)
    print(f"✓ Public key saved to: {public_key_file}")
    print("  📤 Upload this file to your website")

    # Create .well-known directory structure for easy upload
    wellknown_dir = Path("data/website/.well-known/appspecific")
    wellknown_dir.mkdir(parents=True, exist_ok=True)

    wellknown_file = wellknown_dir / "com.tesla.3p.public-key.pem"
    with open(wellknown_file, 'wb') as f:
        f.write(public_pem)

    print()
    print("=" * 60)
    print("✓ Keys generated successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Upload data/website/.well-known/appspecific/com.tesla.3p.public-key.pem")
    print("   to your website at:")
    print("   https://<your-domain>/.well-known/appspecific/com.tesla.3p.public-key.pem")
    print()
    print("2. Your public key content:")
    print("-" * 60)
    print(public_pem.decode('utf-8'))
    print("-" * 60)


if __name__ == "__main__":
    try:
        generate_keys()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
