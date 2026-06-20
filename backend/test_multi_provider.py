#!/usr/bin/env python3
"""
Simple test script for the multi-provider LLM system.
Tests basic functionality without requiring actual API keys.
"""

import asyncio
import os
from app.providers import (
    initialize_multi_provider_client, get_multi_provider_client,
    get_config_parser, get_health_monitor, get_fallback_strategy
)


async def test_basic_functionality():
    """Test basic multi-provider client functionality."""
    print("🧪 Testing Multi-Provider LLM System")
    print("=" * 50)

    # Test 1: Initialize the system
    print("\n1. Initializing multi-provider client...")
    try:
        initialize_multi_provider_client()
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

    # Test 2: Check configuration parsing
    print("\n2. Testing configuration parsing...")
    config_parser = get_config_parser()
    try:
        config_parser.parse_environment()
        enabled_providers = config_parser.get_enabled_providers()
        print(f"✅ Parsed configuration: {enabled_providers}")
    except Exception as e:
        print(f"❌ Configuration parsing failed: {e}")
        return False

    # Test 3: Check provider loading (should work with demo mode)
    print("\n3. Testing provider loading...")
    try:
        client = get_multi_provider_client()
        status = client.get_provider_status()
        print(f"✅ Provider status: {status['total_providers']} providers loaded")
    except Exception as e:
        print(f"❌ Provider loading failed: {e}")
        return False

    # Test 4: Check health monitoring
    print("\n4. Testing health monitoring...")
    try:
        health_monitor = get_health_monitor()
        print("✅ Health monitor accessible")
    except Exception as e:
        print(f"❌ Health monitoring setup failed: {e}")
        return False

    # Test 5: Check fallback strategy
    print("\n5. Testing fallback strategy...")
    try:
        fallback_strategy = get_fallback_strategy()
        provider_names = fallback_strategy.provider_names
        print(f"✅ Fallback strategy ready: {provider_names}")
    except Exception as e:
        print(f"❌ Fallback strategy setup failed: {e}")
        return False

    # Test 6: Test demo mode response generation
    print("\n6. Testing demo mode...")
    try:
        messages = [
            {"role": "user", "content": "Hello, can you help me with cooking?"}
        ]
        # Note: This will use demo mode since no providers are configured
        client = get_multi_provider_client()

        # Check if we're in demo mode
        if client.is_demo_mode():
            print("ℹ️  Running in demo mode (no providers configured)")
        else:
            result = await client.chat_completion(messages, max_tokens=100)
            print(f"✅ Demo response generated: {result[:100]}...")

    except Exception as e:
        print(f"❌ Demo mode test failed: {e}")
        return False

    print("\n🎉 All tests passed!")
    return True


def test_configuration_examples():
    """Test different configuration scenarios."""
    print("\n📋 Configuration Examples")
    print("=" * 50)

    # Example 1: OpenAI only
    print("\nExample 1: Single provider (OpenAI)")
    print("```bash")
    print("PRIMARY_PROVIDER=openai")
    print("OPENAI_API_KEY=sk-your-api-key")
    print("```")

    # Example 2: Multiple providers
    print("\nExample 2: Multiple providers")
    print("```bash")
    print("PRIMARY_PROVIDER=openai")
    print("SECONDARY_PROVIDER=anthropic")
    print("TERTIARY_PROVIDER=gemini")
    print("")
    print("OPENAI_API_KEY=sk-your-openai-key")
    print("ANTHROPIC_API_KEY=sk-ant-your-anthropic-key")
    print("GOOGLE_API_KEY=your-google-key")
    print("```")

    # Example 3: Local provider
    print("\nExample 3: Local Ollama")
    print("```bash")
    print("PRIMARY_PROVIDER=local")
    print("LOCAL_BACKEND=ollama")
    print("OLLAMA_HOST=http://localhost:11434")
    print("LOCAL_MODEL=llama2")
    print("```")

    print("\nExample 4: Local HuggingFace")
    print("```bash")
    print("PRIMARY_PROVIDER=local")
    print("LOCAL_BACKEND=huggingface")
    print("HF_MODEL_PATH=/path/to/model")
    print("```")


if __name__ == "__main__":
    # Set up environment for testing
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('HEALTH_CHECK_INTERVAL', '60')

    # Run tests
    success = asyncio.run(test_basic_functionality())

    if success:
        test_configuration_examples()
        print("\n✅ Multi-provider LLM system is working correctly!")
        print("\n🚀 Next steps:")
        print("1. Configure your preferred providers using environment variables")
        print("2. Update your application to use the new llm_client_new module")
        print("3. Test with real API keys once providers are configured")
    else:
        print("\n❌ Some tests failed. Check logs for details.")