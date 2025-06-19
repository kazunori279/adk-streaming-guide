#!/usr/bin/env python3
"""
Chapter 1.3.1: Environment Setup Validation
Comprehensive script to validate ADK streaming environment configuration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_environment():
    """Validate ADK streaming environment setup."""
    
    print("🔧 ADK Streaming Environment Validation")
    print("=" * 45)
    
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Environment file loaded: {env_path}")
    else:
        print(f"❌ Environment file not found: {env_path}")
        return False
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version {python_version.major}.{python_version.minor} - requires 3.8+")
        return False
    
    # Test ADK installation
    try:
        import google.adk
        print(f"✓ ADK import successful")
        
        # Try to get version if available
        try:
            from google.adk.version import __version__
            print(f"✓ ADK version: {__version__}")
        except:
            print("ℹ️ ADK version info not available")
            
    except ImportError as e:
        print(f"❌ ADK import failed: {e}")
        return False
    
    # Check essential imports
    essential_imports = [
        ('google.adk.agents', 'Agent, LiveRequestQueue'),
        ('google.adk.runners', 'InMemoryRunner'),
        ('google.genai.types', 'Content, Part, Blob'),
    ]
    
    for module, components in essential_imports:
        try:
            __import__(module)
            print(f"✓ Import: {module}")
        except ImportError as e:
            print(f"❌ Import failed: {module} - {e}")
            return False
    
    # Validate environment variables
    env_checks = [
        ('GOOGLE_GENAI_USE_VERTEXAI', 'Platform configuration'),
        ('GOOGLE_API_KEY', 'API authentication'),
    ]
    
    for env_var, description in env_checks:
        value = os.getenv(env_var)
        if value:
            # Mask API key for security
            display_value = value if env_var != 'GOOGLE_API_KEY' else f"{value[:10]}..."
            print(f"✓ {description}: {display_value}")
        else:
            print(f"❌ Missing: {env_var} ({description})")
            return False
    
    # Test basic ADK functionality
    try:
        from google.adk.agents import LiveRequestQueue
        from google.genai.types import Content, Part
        
        # Create test queue
        queue = LiveRequestQueue()
        test_content = Content(parts=[Part(text="Test message")])
        queue.send_content(test_content)
        queue.close()
        
        print("✓ Basic ADK functionality test passed")
        
    except Exception as e:
        print(f"❌ ADK functionality test failed: {e}")
        return False
    
    print("\n🎉 Environment validation successful!")
    print("\nNext steps:")
    print("• Start building your streaming agents in src/agents/")
    print("• Create custom tools in src/tools/")
    print("• Add utility functions in src/utils/")
    print("• Test with Chapter 3 examples")
    
    print("\n" + "=" * 45)
    print("📋 Expected Output:")
    print("=" * 45)
    print("""🔧 ADK Streaming Environment Validation
=============================================
✓ Environment file loaded: /path/to/your-streaming-project/.env
✓ Python version: 3.12.8
✓ ADK import successful
✓ ADK version: 1.3.0
✓ Import: google.adk.agents
✓ Import: google.adk.runners
✓ Import: google.genai.types
✓ Platform configuration: FALSE
✓ API authentication: AIzaSyAolZ...
✓ Basic ADK functionality test passed

🎉 Environment validation successful!

Next steps:
• Start building your streaming agents in src/agents/
• Create custom tools in src/tools/
• Add utility functions in src/utils/
• Test with Chapter 3 examples""")
    
    return True

def main():
    """Run environment validation."""
    
    try:
        success = validate_environment()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()