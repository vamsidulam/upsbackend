#!/usr/bin/env python3
"""
Check the most recent predictions for technical details
"""

from pymongo import MongoClient

def check_recent_predictions():
    """Check the most recent predictions for technical details"""
    
    try:
        # Connect to MongoDB
        import os
        from dotenv import load_dotenv
        load_dotenv()
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['UPS_DATA_MONITORING']
        predictions_collection = db['ups_predictions']
        
        print("🔍 Checking Most Recent Predictions")
        print("=" * 50)
        
        # Get the 3 most recent predictions
        recent_predictions = list(predictions_collection.find().sort('timestamp', -1).limit(3))
        
        print(f"📋 Most Recent Predictions (showing {len(recent_predictions)}):")
        print("-" * 40)
        
        for i, pred in enumerate(recent_predictions, 1):
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
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error checking recent predictions: {e}")

if __name__ == "__main__":
    check_recent_predictions()
