#!/usr/bin/env python3
"""
Check detailed structure of predictions in the database
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
import json

# Load environment variables
load_dotenv('atlas.env')

def check_detailed_predictions():
    """Check detailed structure of predictions"""
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('DB_NAME')]
        
        # Check ups_predictions collection
        predictions = db['ups_predictions']
        total_count = predictions.count_documents({})
        print(f"🔮 Total predictions in ups_predictions: {total_count}")
        
        if total_count == 0:
            print("❌ No predictions found")
            return
        
        # Get a few sample predictions to examine structure
        print(f"\n📋 Examining sample predictions structure:")
        print("=" * 60)
        
        for i, pred in enumerate(predictions.find().limit(3), 1):
            print(f"\n--- Prediction {i} ---")
            print(f"UPS ID: {pred.get('ups_id', 'Unknown')}")
            print(f"UPS Name: {pred.get('ups_name', 'Unknown')}")
            print(f"Failure Probability: {pred.get('probability_failure', 0):.2%}")
            print(f"Timestamp: {pred.get('timestamp', 'Unknown')}")
            
            # Check if risk_assessment exists
            if 'risk_assessment' in pred:
                risk_assessment = pred['risk_assessment']
                print(f"✅ Risk Assessment exists:")
                print(f"   Risk Level: {risk_assessment.get('risk_level', 'Unknown')}")
                print(f"   Timeframe: {risk_assessment.get('timeframe', 'Unknown')}")
                
                # Check failure_reasons
                if 'failure_reasons' in risk_assessment:
                    reasons = risk_assessment['failure_reasons']
                    print(f"   Failure Reasons: {len(reasons)} reasons found")
                    for j, reason in enumerate(reasons, 1):
                        print(f"     {j}. {reason}")
                else:
                    print(f"   ❌ No failure_reasons field in risk_assessment")
                
                # Check other fields
                if 'failure_summary' in risk_assessment:
                    print(f"   Failure Summary: {risk_assessment['failure_summary']}")
                else:
                    print(f"   ❌ No failure_summary field")
                
                if 'technical_details' in risk_assessment:
                    print(f"   Technical Details: ✅ Present")
                else:
                    print(f"   ❌ No technical_details field")
            else:
                print(f"❌ No risk_assessment field found")
            
            # Check for top-level failure_reasons
            if 'failure_reasons' in pred:
                print(f"✅ Top-level failure_reasons: {len(pred['failure_reasons'])} reasons")
                for j, reason in enumerate(pred['failure_reasons'], 1):
                    print(f"     {j}. {reason}")
            else:
                print(f"❌ No top-level failure_reasons field")
            
            # Show all available fields
            print(f"\n📊 All available fields: {list(pred.keys())}")
            
            # Show full structure for first prediction
            if i == 1:
                print(f"\n🔍 Full structure of first prediction:")
                print(json.dumps(pred, indent=2, default=str))
        
        # Check what's actually being stored
        print(f"\n🔍 Checking what's actually stored:")
        print("=" * 60)
        
        # Count predictions with different structures
        with_risk_assessment = predictions.count_documents({'risk_assessment': {'$exists': True}})
        with_failure_reasons = predictions.count_documents({'risk_assessment.failure_reasons': {'$exists': True, '$ne': []}})
        with_technical_details = predictions.count_documents({'risk_assessment.technical_details': {'$exists': True}})
        
        print(f"Predictions with risk_assessment: {with_risk_assessment}/{total_count}")
        print(f"Predictions with failure_reasons: {with_failure_reasons}/{total_count}")
        print(f"Predictions with technical_details: {with_technical_details}/{total_count}")
        
        # Check if there are any predictions with actual detailed reasons
        detailed_predictions = predictions.find({
            'risk_assessment.failure_reasons': {'$exists': True, '$ne': []}
        })
        
        print(f"\n💡 Sample of predictions with failure reasons:")
        for pred in detailed_predictions.limit(2):
            print(f"\nUPS: {pred.get('ups_id')}")
            reasons = pred.get('risk_assessment', {}).get('failure_reasons', [])
            for reason in reasons:
                print(f"  - {reason[:100]}...")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error checking predictions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_detailed_predictions()
