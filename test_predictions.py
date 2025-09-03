#!/usr/bin/env python3
"""
Test ML Predictions
"""

from ml.predictive_monitor import UPSPredictiveMonitor

def test_predictions():
    print("🔮 Testing ML Predictions...")
    print("=" * 40)
    
    try:
        # Create monitor instance
        monitor = UPSPredictiveMonitor()
        print("✅ Monitor instance created")
        
        # Load UPS data
        print("\n📊 Loading UPS data...")
        result = monitor.load_ups_data()
        
        if result is None:
            print("❌ Failed to load UPS data")
            return
        
        ups_data, client = result
        print(f"✅ Loaded {len(ups_data)} UPS systems")
        
        # Make predictions
        print("\n🔮 Generating predictions...")
        predictions = monitor.make_predictions(ups_data)
        
        if predictions:
            print(f"✅ Generated {len(predictions)} predictions")
            
            # Show sample predictions
            print("\n📋 Sample Predictions:")
            for i, pred in enumerate(predictions[:3]):  # Show first 3
                print(f"   {i+1}. UPS: {pred.get('ups_name', 'Unknown')}")
                print(f"      Failure Risk: {pred.get('probability_failure', 0):.1%}")
                print(f"      Confidence: {pred.get('confidence', 0):.1%}")
                print(f"      Risk Level: {pred.get('risk_level', 'Unknown')}")
                print()
        else:
            print("⚠️ No predictions generated")
        
        # Save predictions
        print("💾 Saving predictions...")
        if monitor.save_predictions(predictions):
            print("✅ Predictions saved successfully")
        else:
            print("❌ Failed to save predictions")
        
        # Generate health report
        print("\n📄 Generating health report...")
        if monitor.generate_health_report(ups_data, predictions):
            print("✅ Health report generated successfully")
        else:
            print("❌ Failed to generate health report")
        
        # Close MongoDB connection
        client.close()
        print("\n🎉 ML Prediction test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during prediction test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_predictions()
