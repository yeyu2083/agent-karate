#!/usr/bin/env python3
"""
Simple script to test TestRail connection and configuration
"""

import os
import sys
from dotenv import load_dotenv
from testrail_client import TestRailClient, TestRailSettings

# Load environment
load_dotenv()

def test_connection():
    """Test TestRail connection"""
    print("🧪 Testing TestRail Connection")
    print("=" * 40)
    
    try:
        settings = TestRailSettings()
        print(f"✅ Configuration loaded:")
        print(f"   URL: {settings.testrail_url}")
        print(f"   Email: {settings.testrail_email}")
        print(f"   Project ID: {settings.testrail_project_id}")
        print(f"   Suite ID: {settings.testrail_suite_id}")
        
        client = TestRailClient(settings)
        
        print("\n🔌 Testing connection...")
        if client.check_connection():
            print("✅ Connection successful!")
            
            # Test getting project
            print(f"\n📋 Testing project access...")
            project = client.get_project(settings.testrail_project_id)
            if project:
                print(f"✅ Project: {project.get('name', 'Unknown')}")
            else:
                print(f"❌ Could not access project {settings.testrail_project_id}")
            
            # Test getting suite
            print(f"\n📁 Testing suite access...")
            suite = client.get_suite(settings.testrail_suite_id)
            if suite:
                print(f"✅ Suite: {suite.get('name', 'Unknown')}")
            else:
                print(f"❌ Could not access suite {settings.testrail_suite_id}")
                
            return True
        else:
            print("❌ Connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)