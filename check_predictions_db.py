#!/usr/bin/env python3
"""
Check predictions stored in the database
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv('atlas.env')

def check_predictions():
    """Check predictions in the database"""
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('DB_NAME')]
        
        # Check collections
        collections = db.list_collection_names()
        print(f"📊 Available collections: {collections}")
        
        # Check ups_predictions collection
        if 'ups_predictions' in collections:
            predictions = db['ups_predictions']
            total_count = predictions.count_documents({})
            print(f"\n🔮 UPS Predictions Collection:")
            print(f"   Total predictions: {total_count}")
            
            if total_count > 0:
                # Get latest prediction
                latest = predictions.find_one({}, sort=[('timestamp', -1)])
                print(f"\n📅 Latest prediction:")
                print(f"   UPS ID: {latest.get('ups_id', 'Unknown')}")
                print(f"   UPS Name: {latest.get('ups_name', 'Unknown')}")
                print(f"   Failure Probability: {latest.get('probability_failure', 0):.2%}")
                print(f"   Risk Level: {latest.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
                print(f"   Timestamp: {latest.get('timestamp', 'Unknown')}")
                
                # Check risk level distribution
                print(f"\n📊 Risk Level Distribution:")
                pipeline = [
                    {'$group': {'_id': '$risk_assessment.risk_level', 'count': {'$sum': 1}}}
                ]
                for result in predictions.aggregate(pipeline):
                    risk_level = result['_id'] or 'unknown'
                    count = result['count']
                    print(f"   {risk_level}: {count}")
                
                # Check if predictions have failure reasons
                with_reasons = predictions.count_documents({
                    'risk_assessment.failure_reasons': {'$exists': True, '$ne': []}
                })
                print(f"\n💡 Predictions with failure reasons: {with_reasons}/{total_count}")
                
                # Sample of predictions with failure reasons
                if with_reasons > 0:
                    print(f"\n📝 Sample failure reasons:")
                    sample = predictions.find_one({
                        'risk_assessment.failure_reasons': {'$exists': True, '$ne': []}
                    })
                    if sample and 'risk_assessment' in sample:
                        reasons = sample['risk_assessment'].get('failure_reasons', [])
                        for i, reason in enumerate(reasons[:2], 1):  # Show first 2 reasons
                            print(f"   {i}. {reason[:100]}...")
            else:
                print("   ❌ No predictions found in database")
        
        # Check if there's also a 'predictions' collection
        if 'predictions' in collections:
            old_predictions = db['predictions']
            old_count = old_predictions.count_documents({})
            print(f"\n📊 Old 'predictions' Collection:")
            print(f"   Total predictions: {old_count}")
        
        # Check UPS data
        if 'upsdata' in collections:
            ups_data = db['upsdata']
            ups_count = ups_data.count_documents({})
            print(f"\n🔌 UPS Data Collection:")
            print(f"   Total UPS systems: {ups_count}")
            
            # Check UPS status distribution
            if ups_count > 0:
                print(f"   Status distribution:")
                pipeline = [
                    {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
                ]
                for result in ups_data.aggregate(pipeline):
                    status = result['_id'] or 'unknown'
                    count = result['count']
                    print(f"     {status}: {count}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error checking predictions: {e}")

if __name__ == "__main__":
    check_predictions()
