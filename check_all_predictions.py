#!/usr/bin/env python3
"""
Check all predictions to find the newest ones
"""

from pymongo import MongoClient
from datetime import datetime

def check_all_predictions():
    """Check all predictions to find the newest ones"""
    
    try:
        # Connect to MongoDB
        import os
        from dotenv import load_dotenv
        load_dotenv()
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['UPS_DATA_MONITORING']
        predictions_collection = db['ups_predictions']
        
        print("🔍 Checking All Predictions")
        print("=" * 50)
        
        # Count total predictions
        total_count = predictions_collection.count_documents({})
        print(f"📊 Total predictions in database: {total_count}")
        
        # Get all predictions and sort by timestamp
        all_predictions = list(predictions_collection.find())
        
        # Sort by timestamp (newest first)
        all_predictions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"\n📋 Top 10 Most Recent Predictions:")
        print("-" * 40)
        
        for i, pred in enumerate(all_predictions[:10], 1):
            print(f"\n{i}. UPS: {pred.get('ups_name', 'Unknown')}")
            print(f"   Timestamp: {pred.get('timestamp', 'Unknown')}")
            print(f"   Failure Probability: {pred.get('probability_failure', 0):.1%}")
            print(f"   Has risk_assessment: {'risk_assessment' in pred}")
            
            if 'risk_assessment' in pred:
                risk_assessment = pred['risk_assessment']
                print(f"   Has technical_details: {'technical_details' in risk_assessment}")
                
                if 'technical_details' in risk_assessment:
                    tech_details = risk_assessment['technical_details']
                    print(f"   Technical Details Fields:")
                    for key, value in tech_details.items():
                        print(f"     {key}: {value}")
                else:
                    print("   ❌ No technical_details found")
            else:
                print("   ❌ No risk_assessment found")
        
        # Check for predictions with technical details
        with_tech_details = sum(1 for p in all_predictions if p.get('risk_assessment', {}).get('technical_details'))
        print(f"\n🔍 Predictions with Technical Details: {with_tech_details}")
        
        if with_tech_details > 0:
            print("✅ Some predictions have technical details stored")
        else:
            print("❌ No predictions have technical details stored")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error checking predictions: {e}")

if __name__ == "__main__":
    check_all_predictions()
