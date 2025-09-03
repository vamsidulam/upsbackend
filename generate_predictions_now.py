#!/usr/bin/env python3
"""
Manually generate predictions right now to test the system
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path to import ml modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_predictions():
    """Generate predictions manually"""
    try:
        print("🔮 Generating predictions manually...")
        
        # Import the predictive monitor
        from ml.predictive_monitor import UPSPredictiveMonitor
        
        # Create monitor instance
        monitor = UPSPredictiveMonitor()
        print("✅ Predictive monitor created")
        
        # Load UPS data
        print("📊 Loading UPS data...")
        ups_data_result = monitor.load_ups_data()
        if ups_data_result is None:
            print("❌ Failed to load UPS data")
            return False
        
        ups_data, client = ups_data_result
        print(f"✅ Loaded {len(ups_data)} UPS records")
        
        # Make predictions
        print("🔮 Making predictions...")
        predictions = monitor.make_predictions(ups_data)
        if not predictions:
            print("❌ Failed to make predictions")
            return False
        
        print(f"✅ Generated {len(predictions)} predictions")
        
        # Save predictions
        print("💾 Saving predictions...")
        if monitor.save_predictions(predictions):
            print("✅ Predictions saved to database")
        else:
            print("❌ Failed to save predictions")
            return False
        
        # Generate health report
        print("📋 Generating health report...")
        report = monitor.generate_health_report(ups_data, predictions)
        if report:
            print("✅ Health report generated")
        else:
            print("❌ Failed to generate health report")
        
        # Show prediction summary
        print(f"\n📊 Prediction Summary:")
        print(f"   Total predictions: {len(predictions)}")
        
        high_risk = sum(1 for p in predictions if p.get('probability_failure', 0) > 0.7)
        medium_risk = sum(1 for p in predictions if 0.4 < p.get('probability_failure', 0) <= 0.7)
        low_risk = sum(1 for p in predictions if p.get('probability_failure', 0) <= 0.4)
        
        print(f"   High risk (>70%): {high_risk}")
        print(f"   Medium risk (40-70%): {medium_risk}")
        print(f"   Low risk (<40%): {low_risk}")
        
        # Show sample predictions
        print(f"\n🔍 Sample Predictions:")
        for i, pred in enumerate(predictions[:3], 1):
            print(f"   {i}. {pred.get('ups_name', 'Unknown')}")
            print(f"      Failure probability: {pred.get('probability_failure', 0):.1%}")
            print(f"      Confidence: {pred.get('confidence', 0):.1%}")
            print(f"      Status: {pred.get('current_status', 'Unknown')}")
        
        # Close MongoDB connection
        if client:
            client.close()
        
        print(f"\n✅ Predictions generated successfully at {datetime.now().strftime('%H:%M:%S')}")
        print(f"📊 Check the frontend dashboard to see the new predictions!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating predictions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = generate_predictions()
    if success:
        print("\n🎉 Success! Predictions are now available in the database.")
        print("🌐 Check the frontend at http://localhost:5173")
    else:
        print("\n❌ Failed to generate predictions. Check the error messages above.")
