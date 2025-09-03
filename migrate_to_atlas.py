#!/usr/bin/env python3
"""
MongoDB Migration Script: Local to Atlas
This script migrates data from local MongoDB to MongoDB Atlas
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import json
from datetime import datetime
import time

# Configuration
LOCAL_MONGODB_URI = "mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
LOCAL_DB_NAME = "UPS_DATA_MONITORING"

# MongoDB Atlas connection string
ATLAS_MONGODB_URI = "mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ATLAS_DB_NAME = "UPS_DATA_MONITORING"

# Collections to migrate
COLLECTIONS = ['upsdata', 'ups_predictions', 'alerts']

def test_connection(uri, db_name, label):
    """Test MongoDB connection"""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[db_name]
        print(f"✅ {label} connection successful")
        return client, db
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ {label} connection failed: {e}")
        return None, None

def get_collection_stats(db, collection_name):
    """Get collection statistics"""
    try:
        collection = db[collection_name]
        count = collection.count_documents({})
        print(f"   📊 {collection_name}: {count} documents")
        return count
    except Exception as e:
        print(f"   ❌ Error getting stats for {collection_name}: {e}")
        return 0

def export_collection_data(db, collection_name):
    """Export collection data to JSON format"""
    try:
        collection = db[collection_name]
        documents = list(collection.find({}))
        
        # Convert ObjectIds to strings for JSON serialization
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        print(f"   📤 Exported {len(documents)} documents from {collection_name}")
        return documents
    except Exception as e:
        print(f"   ❌ Error exporting {collection_name}: {e}")
        return []

def import_collection_data(db, collection_name, documents):
    """Import collection data from JSON format"""
    try:
        collection = db[collection_name]
        
        if documents:
            # Clear existing collection
            collection.delete_many({})
            print(f"   🗑️  Cleared existing {collection_name} collection")
            
            # Insert documents
            result = collection.insert_many(documents)
            print(f"   📥 Imported {len(result.inserted_ids)} documents to {collection_name}")
            return len(result.inserted_ids)
        else:
            print(f"   ⚠️  No documents to import for {collection_name}")
            return 0
    except Exception as e:
        print(f"   ❌ Error importing to {collection_name}: {e}")
        return 0

def create_indexes(db, collection_name):
    """Create indexes for optimal performance"""
    try:
        collection = db[collection_name]
        
        if collection_name == 'upsdata':
            collection.create_index([("timestamp", -1)])
            collection.create_index([("ups_id", 1)])
            collection.create_index([("status", 1)])
        elif collection_name == 'ups_predictions':
            collection.create_index([("timestamp", -1)])
            collection.create_index([("ups_id", 1)])
            collection.create_index([("prediction_date", -1)])
        elif collection_name == 'alerts':
            collection.create_index([("timestamp", -1)])
            collection.create_index([("ups_id", 1)])
            collection.create_index([("alert_type", 1)])
        
        print(f"   🔍 Created indexes for {collection_name}")
    except Exception as e:
        print(f"   ❌ Error creating indexes for {collection_name}: {e}")

def migrate_collection(local_db, atlas_db, collection_name):
    """Migrate a single collection"""
    print(f"\n🔄 Migrating collection: {collection_name}")
    print("-" * 50)
    
    # Export from local
    print("📤 Exporting from local MongoDB...")
    documents = export_collection_data(local_db, collection_name)
    
    if not documents:
        print(f"   ⚠️  No documents found in local {collection_name}")
        return 0
    
    # Import to Atlas
    print("📥 Importing to MongoDB Atlas...")
    imported_count = import_collection_data(atlas_db, collection_name, documents)
    
    # Create indexes
    print("🔍 Creating indexes...")
    create_indexes(atlas_db, collection_name)
    
    return imported_count

def update_environment_file():
    """Update .env file with Atlas connection string"""
    env_file = ".env"
    env_content = f"""# MongoDB Atlas Configuration
MONGODB_URI={ATLAS_MONGODB_URI}
DB_NAME={ATLAS_DB_NAME}
COLLECTION=upsdata

# Local MongoDB (commented out after migration)
# MONGODB_URI=mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
# DB_NAME=UPS_DATA_MONITORING
# COLLECTION=upsdata
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Updated {env_file} with Atlas configuration")
    except Exception as e:
        print(f"❌ Error updating {env_file}: {e}")

def create_atlas_config_file():
    """Create a configuration file for Atlas connection"""
    config_content = f"""# MongoDB Atlas Configuration
# This file contains the Atlas connection details

ATLAS_MONGODB_URI = "{ATLAS_MONGODB_URI}"
ATLAS_DB_NAME = "{ATLAS_DB_NAME}"

# Usage in Python:
# from pymongo import MongoClient
# client = MongoClient(ATLAS_MONGODB_URI)
# db = client[ATLAS_DB_NAME]
"""
    
    try:
        with open("atlas_config.py", 'w') as f:
            f.write(config_content)
        print("✅ Created atlas_config.py with Atlas configuration")
    except Exception as e:
        print(f"❌ Error creating atlas_config.py: {e}")

def main():
    """Main migration function"""
    print("🚀 MongoDB Migration: Local to Atlas")
    print("=" * 60)
    print(f"📅 Migration started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test local connection
    print("🔍 Testing local MongoDB connection...")
    local_client, local_db = test_connection(LOCAL_MONGODB_URI, LOCAL_DB_NAME, "Local MongoDB")
    if not local_client:
        print("❌ Cannot proceed without local MongoDB connection")
        sys.exit(1)
    
    # Test Atlas connection
    print("\n🔍 Testing MongoDB Atlas connection...")
    atlas_client, atlas_db = test_connection(ATLAS_MONGODB_URI, ATLAS_DB_NAME, "MongoDB Atlas")
    if not atlas_client:
        print("❌ Cannot proceed without Atlas connection")
        local_client.close()
        sys.exit(1)
    
    # Show current database stats
    print(f"\n📊 Local Database Stats ({LOCAL_DB_NAME}):")
    local_stats = {}
    for collection in COLLECTIONS:
        local_stats[collection] = get_collection_stats(local_db, collection)
    
    print(f"\n📊 Atlas Database Stats ({ATLAS_DB_NAME}):")
    atlas_stats = {}
    for collection in COLLECTIONS:
        atlas_stats[collection] = get_collection_stats(atlas_db, collection)
    
    # Confirm migration
    print(f"\n⚠️  Migration Summary:")
    print(f"   Source: Local MongoDB ({LOCAL_DB_NAME})")
    print(f"   Destination: MongoDB Atlas ({ATLAS_DB_NAME})")
    print(f"   Collections: {', '.join(COLLECTIONS)}")
    
    total_local_docs = sum(local_stats.values())
    print(f"   Total documents to migrate: {total_local_docs}")
    
    if total_local_docs == 0:
        print("❌ No documents found to migrate")
        local_client.close()
        atlas_client.close()
        sys.exit(1)
    
    # Perform migration
    print(f"\n🚀 Starting migration...")
    migration_start = time.time()
    
    total_migrated = 0
    for collection in COLLECTIONS:
        if local_stats[collection] > 0:
            migrated_count = migrate_collection(local_db, atlas_db, collection)
            total_migrated += migrated_count
        else:
            print(f"\n⏭️  Skipping {collection} (no documents)")
    
    migration_time = time.time() - migration_start
    
    # Show final stats
    print(f"\n📊 Migration Complete!")
    print("=" * 60)
    print(f"✅ Total documents migrated: {total_migrated}")
    print(f"⏱️  Migration time: {migration_time:.2f} seconds")
    
    print(f"\n📊 Final Atlas Database Stats:")
    for collection in COLLECTIONS:
        get_collection_stats(atlas_db, collection)
    
    # Update configuration files
    print(f"\n🔧 Updating configuration files...")
    update_environment_file()
    create_atlas_config_file()
    
    # Close connections
    local_client.close()
    atlas_client.close()
    
    print(f"\n🎉 Migration completed successfully!")
    print(f"📝 Next steps:")
    print(f"   1. Update your application to use the new Atlas connection string")
    print(f"   2. Test your application with the new Atlas database")
    print(f"   3. Once confirmed working, you can stop your local MongoDB")
    print(f"   4. Update docker-compose.yml to remove local MongoDB service")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

