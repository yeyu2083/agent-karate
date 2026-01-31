#!/usr/bin/env python3
"""
Quick MongoDB Connection Test
Verifica que la conexión a MongoDB está funcionando
"""

import os
import sys
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def test_mongo_connection():
    """Test MongoDB connection"""
    print("\n" + "="*60)
    print("🧪 MongoDB Connection Test")
    print("="*60 + "\n")
    
    mongo_uri = os.getenv("MONGO_URI")
    
    if not mongo_uri:
        print("❌ MONGO_URI not found")
        print("   Set in .env file or environment variable")
        return False
    
    print(f"📍 MONGO_URI (masked): {mongo_uri.split('@')[1] if '@' in mongo_uri else mongo_uri}")
    
    try:
        import pymongo
        print(f"✓ pymongo {pymongo.__version__} installed")
    except ImportError:
        print("❌ pymongo not installed")
        print("   pip install pymongo>=4.0.0")
        return False
    
    try:
        from pymongo import MongoClient
        print("✓ Attempting connection...")
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        
        db = client.get_database()
        print(f"✅ Connected to: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        if collections:
            print(f"\n📊 Collections ({len(collections)}):")
            for coll in collections:
                count = db[coll].count_documents({})
                print(f"   • {coll}: {count} documents")
        else:
            print("\n📊 No collections yet (will be created on first save)")
        
        # Test insert/query
        print("\n🧪 Testing insert & query...")
        test_coll = db["test_connection"]
        test_doc = {"test": "connection", "timestamp": str(__import__('datetime').datetime.utcnow())}
        result = test_coll.insert_one(test_doc)
        print(f"   ✓ Inserted document: {result.inserted_id}")
        
        found = test_coll.find_one({"test": "connection"})
        if found:
            print(f"   ✓ Retrieved document: {found.get('test')}")
        
        # Clean up
        test_coll.delete_one({"test": "connection"})
        print(f"   ✓ Cleanup done")
        
        client.close()
        print("\n" + "="*60)
        print("✅ MongoDB is working correctly!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection error:")
        print(f"   {type(e).__name__}: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check MONGO_URI in .env")
        print("   2. Verify password is correct")
        print("   3. Check IP whitelist in MongoDB Atlas:")
        print("      - Go to Security → Network Access")
        print("      - Add your IP or 0.0.0.0 for anywhere")
        print("   4. Ensure cluster is running (not paused)")
        print("\n" + "="*60 + "\n")
        return False


if __name__ == "__main__":
    success = test_mongo_connection()
    sys.exit(0 if success else 1)
