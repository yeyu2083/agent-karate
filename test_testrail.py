#!/usr/bin/env python3
"""
Test script for TestRail connection with detailed logging
"""

from dotenv import load_dotenv
import os
import sys

# Load .env
load_dotenv('agent/.env')

print("=" * 60)
print("TESTRAIL CONNECTION TEST")
print("=" * 60)

# Check environment variables
print("\n📋 Environment Variables Loaded:")
print(f"  TESTRAIL_URL: {os.getenv('TESTRAIL_URL', 'NOT SET')}")
print(f"  TESTRAIL_EMAIL: {os.getenv('TESTRAIL_EMAIL', 'NOT SET')}")
print(f"  TESTRAIL_API_KEY: {os.getenv('TESTRAIL_API_KEY', 'NOT SET')[:20]}..." if os.getenv('TESTRAIL_API_KEY') else "  TESTRAIL_API_KEY: NOT SET")
print(f"  TESTRAIL_PROJECT_ID: {os.getenv('TESTRAIL_PROJECT_ID', 'NOT SET')}")
print(f"  TESTRAIL_SUITE_ID: {os.getenv('TESTRAIL_SUITE_ID', 'NOT SET')}")

# Import client
try:
    from agent.testrail_client import TestRailClient, TestRailSettings
    print("\n✅ Imports successful")
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    sys.exit(1)

# Create settings
try:
    settings = TestRailSettings()
    print("\n✅ Settings loaded:")
    print(f"  URL: {settings.testrail_url}")
    print(f"  Email: {settings.testrail_email}")
    print(f"  Project ID: {settings.testrail_project_id}")
    print(f"  Suite ID: {settings.testrail_suite_id}")
except Exception as e:
    print(f"\n❌ Settings creation failed: {e}")
    sys.exit(1)

# Create client
try:
    client = TestRailClient(settings)
    print(f"\n✅ Client created")
    print(f"  Base URL: {client.base_url}")
    print(f"  Auth: ({settings.testrail_email}, ***)")
except Exception as e:
    print(f"\n❌ Client creation failed: {e}")
    sys.exit(1)

# Test connection
print("\n🔌 Testing connection...")
import requests

test_url = f"{client.base_url}/get_projects"
print(f"  Requesting: {test_url}")

try:
    response = requests.get(
        test_url,
        auth=client.auth,
        headers=client.headers
    )
    print(f"  Status Code: {response.status_code}")
    print(f"  Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Response Body: {data}")
        print(f"\n✅ SUCCESS: Connected as {data.get('name')} ({data.get('email')})")
    else:
        print(f"  Response Body: {response.text}")
        print(f"\n❌ FAILED: Status {response.status_code}")
        if response.status_code == 400:
            print("   → This usually means malformed URL or invalid API format")
        elif response.status_code == 401:
            print("   → Check your email and API key")
        elif response.status_code == 403:
            print("   → Check your permissions in TestRail")
        
except Exception as e:
    print(f"\n❌ Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
