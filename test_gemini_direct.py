#!/usr/bin/env python3
"""
Test Gemini service directly to see if it's working
"""

import os
from dotenv import load_dotenv
from ml.gemini_service import GeminiAIService

# Load environment variables
load_dotenv('atlas.env')

def test_gemini_service():
    """Test Gemini service directly"""
    print("🧪 Testing Gemini AI Service")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"🔑 GEMINI_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    if api_key:
        print(f"   Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Initialize service
    print(f"\n🚀 Initializing Gemini Service...")
    gemini_service = GeminiAIService()
    
    if gemini_service.model:
        print("✅ Gemini AI service initialized successfully")
    else:
        print("❌ Gemini AI service failed to initialize")
        return
    
    # Test with sample UPS data
    print(f"\n📊 Testing with sample UPS data...")
    sample_ups_data = {
        'upsId': 'TEST001',
        'name': 'Test UPS',
        'batteryLevel': 25,
        'temperature': 45,
        'load': 85,
        'efficiency': 82,
        'powerInput': 2200,
        'powerOutput': 1800,
        'status': 'warning'
    }
    
    sample_prediction_data = {
        'probability_failure': 0.75,
        'confidence': 0.92
    }
    
    print(f"Sample UPS Data: {sample_ups_data}")
    print(f"Sample Prediction: {sample_prediction_data}")
    
    # Generate failure reasons
    print(f"\n🔮 Generating failure reasons...")
    try:
        failure_reasons = gemini_service.generate_failure_reasons(sample_ups_data, sample_prediction_data)
        
        if failure_reasons:
            print(f"✅ Generated {len(failure_reasons)} failure reasons:")
            for i, reason in enumerate(failure_reasons, 1):
                print(f"   {i}. {reason[:100]}...")
        else:
            print("❌ No failure reasons generated")
            
    except Exception as e:
        print(f"❌ Error generating failure reasons: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_service()
