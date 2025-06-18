#!/usr/bin/env python3
"""
Chapter 1.3.1: Environment Setup for ADK Streaming
Complete environment configuration for bidirectional streaming with ADK.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def setup_streaming_environment():
    """
    Set up the development environment for ADK streaming applications.
    This includes API keys, environment variables, and basic validation.
    """
    # Load environment variables from .env file
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
    else:
        print("⚠ No .env file found. Please create one with required variables.")
    
    # Required environment variables for streaming
    required_vars = {
        'GOOGLE_API_KEY': 'Required for Gemini Live API access',
        'GOOGLE_CLOUD_PROJECT': 'Optional: For Google Cloud features',
        'GOOGLE_CLOUD_LOCATION': 'Optional: Default is us-central1'
    }
    
    print("\n🔧 Environment Configuration:")
    print("=" * 50)
    
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if var == 'GOOGLE_API_KEY' and not value:
            missing_required.append(var)
            print(f"❌ {var}: Not set - {description}")
        elif value:
            # Mask sensitive values
            masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
            print(f"✓ {var}: {masked_value}")
        else:
            print(f"○ {var}: Not set - {description}")
    
    # Validate critical requirements
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        print("\nTo get started:")
        print("1. Sign up for Google AI Studio: https://aistudio.google.com/")
        print("2. Create an API key")
        print("3. Add to .env file: GOOGLE_API_KEY=your_api_key_here")
        return False
    
    print("\n✅ Environment setup complete!")
    return True

def create_sample_env_file():
    """Create a sample .env file with required variables."""
    env_content = """# ADK Streaming Environment Configuration
# Required for Gemini Live API
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Google Cloud configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional: Development settings
DEBUG=true
LOG_LEVEL=INFO
"""
    
    env_path = Path('.env.example')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"📝 Created sample environment file: {env_path}")
    print("Copy .env.example to .env and update with your values.")

def verify_adk_installation():
    """Verify that ADK is properly installed with streaming support."""
    try:
        import google.adk
        from google.adk.agents import LiveRequestQueue
        from google.adk.runners import InMemoryRunner
        
        print("✅ ADK installation verified")
        print(f"   Version: {getattr(google.adk, '__version__', 'unknown')}")
        print("   Streaming components available: LiveRequestQueue, InMemoryRunner")
        return True
        
    except ImportError as e:
        print(f"❌ ADK not properly installed: {e}")
        print("\nTo install ADK:")
        print("pip install google-adk")
        return False

if __name__ == "__main__":
    print("🚀 ADK Streaming Environment Setup")
    print("=" * 40)
    
    # Check ADK installation
    if not verify_adk_installation():
        exit(1)
    
    # Setup environment
    if not setup_streaming_environment():
        print("\n📝 Creating sample .env file...")
        create_sample_env_file()
        exit(1)
    
    print("\n🎉 Ready to build streaming agents!")