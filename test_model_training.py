#!/usr/bin/env python3
"""
Test script for UPS ML model training
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml.enhanced_model_trainer import EnhancedUPSModelTrainer

def test_model_training():
    """Test the model training functionality"""
    print("🧪 Testing UPS ML Model Training...")
    print("=" * 50)
    
    # Create trainer instance
    trainer = EnhancedUPSModelTrainer()
    
    # Test data loading
    print("\n1️⃣ Testing data loading...")
    X, y = trainer.load_and_prepare_data()
    
    if X is not None and y is not None:
        print(f"✅ Data loaded successfully!")
        print(f"   Features: {X.shape[1]}")
        print(f"   Samples: {X.shape[0]}")
        print(f"   Target distribution: {len(y[y==0])} healthy, {len(y[y==1])} will fail")
    else:
        print("❌ Data loading failed!")
        return False
    
    # Test model training
    print("\n2️⃣ Testing model training...")
    if trainer.train_model():
        print("✅ Model training completed successfully!")
        print(f"   Model saved to: {trainer.model_path}")
    else:
        print("❌ Model training failed!")
        return False
    
    # Test model loading
    print("\n3️⃣ Testing model loading...")
    if trainer.load_model():
        print("✅ Model loading successful!")
    else:
        print("❌ Model loading failed!")
        return False
    
    # Test predictions
    print("\n4️⃣ Testing predictions...")
    
    # Test case 1: Healthy UPS
    healthy_ups = {
        'powerInput': 2200,
        'powerOutput': 2100,
        'batteryLevel': 85,
        'temperature': 35,
        'load': 65
    }
    
    result1 = trainer.predict_with_detailed_reasons(healthy_ups)
    if result1:
        status = "🚨 WILL FAIL" if result1['prediction'] == 1 else "✅ HEALTHY"
        print(f"   Healthy UPS Test: {status}")
        print(f"   Failure Probability: {result1['probability_failure']:.1%}")
        print(f"   Confidence: {result1['confidence']:.1%}")
    
    # Test case 2: Failing UPS
    failing_ups = {
        'powerInput': 2400,
        'powerOutput': 2300,
        'batteryLevel': 25,
        'temperature': 55,
        'load': 95
    }
    
    result2 = trainer.predict_with_detailed_reasons(failing_ups)
    if result2:
        status = "🚨 WILL FAIL" if result2['prediction'] == 1 else "✅ HEALTHY"
        print(f"   Failing UPS Test: {status}")
        print(f"   Failure Probability: {result2['probability_failure']:.1%}")
        print(f"   Confidence: {result2['confidence']:.1%}")
        print("   Failure Reasons:")
        for reason in result2['failure_reasons']:
            print(f"     {reason}")
    
    print("\n5️⃣ Testing real-time simulation...")
    trainer.simulate_real_time_predictions(num_simulations=3, delay_seconds=1)
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_model_training()
        if success:
            print("\n✅ Model training system is working correctly!")
            print("You can now use this for real-time UPS monitoring.")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
