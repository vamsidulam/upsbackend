#!/usr/bin/env python3
"""
Comprehensive MongoDB Migration Script: All Local Databases to Atlas
This script migrates data from all local MongoDB databases to MongoDB Atlas
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import json
from datetime import datetime
import time

# Configuration
LOCAL_MONGODB_URI = "mongodb://localhost:27017"

# MongoDB Atlas connection string
ATLAS_MONGODB_URI = "mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Database mappings: local_db_name -> atlas_db_name
DATABASE_MAPPINGS = {
    'UPS_DATA_MONITORING': 'UPS_DATA_MONITORING',  # Keep same name
    'ups_monitoring': 'ups_monitoring'             # Keep same name
}

# Collection mappings for each database
COLLECTION_MAPPINGS = {
    'UPS_DATA_MONITORING': ['upsdata', 'ups_predictions', 'predictions'],
    'ups_monitoring': ['ups_alerts', 'ups_health_logs', 'ups_events']
}

def test_connection(uri, label):
    """Test MongoDB connection"""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✅ {label} connection successful")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ {label} connection failed: {e}")
        return None

def get_database_stats(client, db_name):
    """Get database statistics"""
    try:
        db = client[db_name]
        collections = db.list_collection_names()
        
        print(f"   📊 Database: {db_name}")
        total_docs = 0
        
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"      📁 {collection}: {count} documents")
            total_docs += count
        
        print(f"      📈 Total documents: {total_docs}")
        return total_docs
        
    except Exception as e:
        print(f"   ❌ Error getting stats for {db_name}: {e}")
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
        
        print(f"      📤 Exported {len(documents)} documents from {collection_name}")
        return documents
    except Exception as e:
        print(f"      ❌ Error exporting {collection_name}: {e}")
        return []

def import_collection_data(db, collection_name, documents):
    """Import collection data from JSON format"""
    try:
        collection = db[collection_name]
        
        if documents:
            # Clear existing collection
            collection.delete_many({})
            print(f"      🗑️  Cleared existing {collection_name} collection")
            
            # Insert documents
            result = collection.insert_many(documents)
            print(f"      📥 Imported {len(result.inserted_ids)} documents to {collection_name}")
            return len(result.inserted_ids)
        else:
            print(f"      ⚠️  No documents to import for {collection_name}")
            return 0
    except Exception as e:
        print(f"      ❌ Error importing to {collection_name}: {e}")
        return 0

def create_indexes(db, collection_name):
    """Create indexes for optimal performance"""
    try:
        collection = db[collection_name]
        
        # Create common indexes
        collection.create_index([("timestamp", -1)])
        collection.create_index([("ups_id", 1)])
        
        # Create specific indexes based on collection
        if collection_name in ['upsdata', 'ups_health_logs']:
            collection.create_index([("status", 1)])
        elif collection_name in ['ups_predictions', 'predictions']:
            collection.create_index([("prediction_date", -1)])
        elif collection_name in ['ups_alerts', 'ups_events']:
            collection.create_index([("alert_type", 1)])
            collection.create_index([("event_type", 1)])
        
        print(f"      🔍 Created indexes for {collection_name}")
    except Exception as e:
        print(f"      ❌ Error creating indexes for {collection_name}: {e}")

def migrate_database(local_client, atlas_client, local_db_name, atlas_db_name):
    """Migrate a single database"""
    print(f"\n🔄 Migrating database: {local_db_name} -> {atlas_db_name}")
    print("-" * 60)
    
    local_db = local_client[local_db_name]
    atlas_db = atlas_client[atlas_db_name]
    
    collections = COLLECTION_MAPPINGS.get(local_db_name, [])
    total_migrated = 0
    
    for collection_name in collections:
        if collection_name in local_db.list_collection_names():
            print(f"\n📁 Migrating collection: {collection_name}")
            
            # Export from local
            documents = export_collection_data(local_db, collection_name)
            
            if documents:
                # Import to Atlas
                imported_count = import_collection_data(atlas_db, collection_name, documents)
                total_migrated += imported_count
                
                # Create indexes
                create_indexes(atlas_db, collection_name)
            else:
                print(f"      ⚠️  No documents found in {collection_name}")
        else:
            print(f"      ⏭️  Collection {collection_name} not found in {local_db_name}")
    
    return total_migrated

def main():
    """Main migration function"""
    print("🚀 Comprehensive MongoDB Migration: All Local Databases to Atlas")
    print("=" * 80)
    print(f"📅 Migration started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test local connection
    print("🔍 Testing local MongoDB connection...")
    local_client = test_connection(LOCAL_MONGODB_URI, "Local MongoDB")
    if not local_client:
        print("❌ Cannot proceed without local MongoDB connection")
        sys.exit(1)
    
    # Test Atlas connection
    print("\n🔍 Testing MongoDB Atlas connection...")
    atlas_client = test_connection(ATLAS_MONGODB_URI, "MongoDB Atlas")
    if not atlas_client:
        print("❌ Cannot proceed without Atlas connection")
        local_client.close()
        sys.exit(1)
    
    # Show current database stats
    print(f"\n📊 Local Database Stats:")
    local_stats = {}
    for db_name in DATABASE_MAPPINGS.keys():
        if db_name in local_client.list_database_names():
            local_stats[db_name] = get_database_stats(local_client, db_name)
        else:
            print(f"   ⚠️  Database {db_name} not found")
    
    print(f"\n📊 Atlas Database Stats (before migration):")
    atlas_stats = {}
    for atlas_db_name in DATABASE_MAPPINGS.values():
        if atlas_db_name in atlas_client.list_database_names():
            atlas_stats[atlas_db_name] = get_database_stats(atlas_client, atlas_db_name)
        else:
            print(f"   📁 Database {atlas_db_name} will be created")
    
    # Calculate total documents to migrate
    total_local_docs = sum(local_stats.values())
    print(f"\n📈 Total documents to migrate: {total_local_docs}")
    
    if total_local_docs == 0:
        print("❌ No documents found to migrate")
        local_client.close()
        atlas_client.close()
        sys.exit(1)
    
    # Perform migration
    print(f"\n🚀 Starting migration...")
    migration_start = time.time()
    
    total_migrated = 0
    for local_db_name, atlas_db_name in DATABASE_MAPPINGS.items():
        if local_stats.get(local_db_name, 0) > 0:
            migrated_count = migrate_database(local_client, atlas_client, local_db_name, atlas_db_name)
            total_migrated += migrated_count
        else:
            print(f"\n⏭️  Skipping {local_db_name} (no documents)")
    
    migration_time = time.time() - migration_start
    
    # Show final stats
    print(f"\n📊 Migration Complete!")
    print("=" * 80)
    print(f"✅ Total documents migrated: {total_migrated}")
    print(f"⏱️  Migration time: {migration_time:.2f} seconds")
    
    print(f"\n📊 Final Atlas Database Stats:")
    for atlas_db_name in DATABASE_MAPPINGS.values():
        if atlas_db_name in atlas_client.list_database_names():
            get_database_stats(atlas_client, atlas_db_name)
    
    # Close connections
    local_client.close()
    atlas_client.close()
    
    print(f"\n🎉 Migration completed successfully!")
    print(f"📝 Next steps:")
    print(f"   1. Test your application with the new Atlas connection")
    print(f"   2. Verify all functionality works with Atlas")
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
