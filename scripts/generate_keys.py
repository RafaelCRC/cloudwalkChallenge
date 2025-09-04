#!/usr/bin/env python3
"""Generate secure keys for the fraud monitoring system."""

import secrets
import os

def generate_secure_password(length=32):
    """Generate a secure password."""
    return secrets.token_urlsafe(length)

def main():
    """Generate all necessary keys and passwords."""
    print("🔐 Generating secure keys for Fraud Monitor...")
    print()
    
    # Generate keys
    db_password = generate_secure_password()
    
    # Print keys
    print("Generated keys (add these to your .env file):")
    print("=" * 50)
    print(f"DB_PASSWORD={db_password}")
    print("=" * 50)
    
    # Optionally update .env file
    env_file = ".env"
    if os.path.exists(env_file):
        response = input(f"Update {env_file} with these keys? (y/N): ")
        if response.lower() == 'y':
            try:
                # Read current .env
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Replace placeholders
                content = content.replace('secure_password_here', db_password)
                
                # Write back
                with open(env_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated {env_file} with new keys")
                
            except Exception as e:
                print(f"❌ Failed to update {env_file}: {e}")
    else:
        print(f"⚠️  {env_file} not found. Create it from env.example first.")
    
    print()
    print("🔒 Keep these keys secure and never commit them to version control!")


if __name__ == "__main__":
    main()

