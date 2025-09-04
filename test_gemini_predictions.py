#!/usr/bin/env python3
"""
Test script for Gemini AI integration with UPS predictions
Generates enhanced predictions using Gemini AI for detailed failure reasons
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import logging

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.gemini_service import GeminiAIService
from ml.enhanced_model_trainer import EnhancedUPSModelTrainer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_service():
    """Test the Gemini AI service"""
    logger.info("Testing Gemini AI service...")
    
    # Initialize Gemini service
    gemini_service = GeminiAIService()
    
    if not gemini_service.model:
        logger.error("Gemini AI service failed to initialize")
        return False
    
    logger.info("Gemini AI service initialized successfully")
    
    # Test data
    test_ups_data = {
        'upsId': 'UPS001',
        'name': 'Test UPS',
        'batteryLevel': 25,
        'temperature': 45,
        'load': 85,
        'efficiency': 78,
        'powerInput': 1200,
        'powerOutput': 1000,
        'voltageInput': 220,
        'voltageOutput': 218,
        'frequency': 50,
        'uptime': 12000,
        'capacity': 1500
    }
    
    test_prediction_data = {
        'probability_failure': 0.85,
        'confidence': 0.92
    }
    
    # Generate failure reasons
    try:
        failure_reasons = gemini_service.generate_failure_reasons(test_ups_data, test_prediction_data)
        logger.info(f"Generated {len(failure_reasons)} failure reasons:")
        for i, reason in enumerate(failure_reasons, 1):
            logger.info(f"{i}. {reason}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating failure reasons: {e}")
        return False

def generate_enhanced_predictions():
    """Generate enhanced predictions using Gemini AI and store in database"""
    logger.info("Generating enhanced predictions with Gemini AI...")
    
    # Load environment variables from atlas.env
    load_dotenv('atlas.env')
    
    # Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "UPS_DATA_MONITORING")
    
    try:
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        ups_collection = db['upsdata']
        predictions_collection = db['ups_predictions']
        
        logger.info(f"Connected to MongoDB: {db_name}")
        
        # Get UPS data
        ups_data_cursor = ups_collection.find({})
        ups_data_list = list(ups_data_cursor)
        
        if not ups_data_list:
            logger.warning("No UPS data found")
            return
        
        logger.info(f"Found {len(ups_data_list)} UPS systems")
        
        # Initialize services
        gemini_service = GeminiAIService()
        enhanced_trainer = EnhancedUPSModelTrainer()
        
        # Generate predictions for each UPS
        enhanced_predictions = []
        for ups in ups_data_list[:5]:  # Limit to first 5 for testing
            try:
                logger.info(f"Processing UPS: {ups.get('name', 'Unknown')} (ID: {ups.get('upsId', 'Unknown')})")
                
                # Make prediction using enhanced model trainer
                prediction_result = enhanced_trainer.predict_with_detailed_reasons(ups)
                
                if prediction_result:
                    # Use Gemini AI to generate enhanced failure reasons
                    gemini_failure_reasons = gemini_service.generate_failure_reasons(ups, prediction_result)
                    
                    # Create enhanced prediction object
                    enhanced_prediction = {
                        'ups_id': ups.get('upsId', 'Unknown'),
                        'ups_name': ups.get('name', 'Unknown'),
                        'probability_failure': prediction_result['probability_failure'],
                        'probability_healthy': prediction_result['probability_healthy'],
                        'confidence': prediction_result['confidence'],
                        'timestamp': datetime.now().isoformat(),
                        'prediction_data': prediction_result['features_used'],
                        'risk_assessment': {
                            'risk_level': 'low' if prediction_result['probability_failure'] < 0.4 else 'medium' if prediction_result['probability_failure'] < 0.7 else 'high',
                            'timeframe': '24_hours' if prediction_result['probability_failure'] < 0.4 else '12_hours' if prediction_result['probability_failure'] < 0.7 else '6_hours',
                            'failure_reasons': gemini_failure_reasons,
                            'failure_summary': f"Enhanced ML model with Gemini AI predicts {prediction_result['probability_failure']:.1%} failure probability with {prediction_result['confidence']:.1%} confidence.",
                            'technical_details': {
                                'battery_health': ups.get('batteryLevel', 100),
                                'temperature_status': ups.get('temperature', 25),
                                'efficiency_rating': ups.get('efficiency', 100),
                                'load_percentage': ups.get('load', 0),
                                'power_balance': (ups.get('powerInput', 0) - ups.get('powerOutput', 0)),
                                'voltage_input': ups.get('voltageInput', 0),
                                'voltage_output': ups.get('voltageOutput', 0),
                                'frequency': ups.get('frequency', 50)
                            }
                        }
                    }
                    
                    enhanced_predictions.append(enhanced_prediction)
                    logger.info(f"Generated prediction for {ups.get('name', 'Unknown')} with {len(gemini_failure_reasons)} Gemini AI failure reasons")
                    
            except Exception as e:
                logger.error(f"Error generating prediction for UPS {ups.get('name', 'Unknown')}: {e}")
                continue
        
        # Store predictions in database
        if enhanced_predictions:
            try:
                # Insert new predictions
                result = predictions_collection.insert_many(enhanced_predictions)
                logger.info(f"Successfully stored {len(result.inserted_ids)} enhanced predictions in database")
                
                # Display sample prediction
                if enhanced_predictions:
                    sample = enhanced_predictions[0]
                    logger.info(f"\nSample Enhanced Prediction:")
                    logger.info(f"UPS: {sample['ups_name']} (ID: {sample['ups_id']})")
                    logger.info(f"Failure Probability: {sample['probability_failure']:.1%}")
                    logger.info(f"Risk Level: {sample['risk_assessment']['risk_level']}")
                    logger.info(f"Failure Reasons: {len(sample['risk_assessment']['failure_reasons'])}")
                    for i, reason in enumerate(sample['risk_assessment']['failure_reasons'][:2], 1):
                        logger.info(f"  {i}. {reason[:100]}...")
                
            except Exception as e:
                logger.error(f"Error storing predictions in database: {e}")
        else:
            logger.warning("No enhanced predictions generated")
        
    except Exception as e:
        logger.error(f"Error in generate_enhanced_predictions: {e}")
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Main function"""
    logger.info("Starting Gemini AI integration test...")
    
    # Test Gemini service
    if test_gemini_service():
        logger.info("Gemini AI service test passed")
        
        # Generate enhanced predictions
        generate_enhanced_predictions()
    else:
        logger.error("Gemini AI service test failed")
        return 1
    
    logger.info("Gemini AI integration test completed")
    return 0

if __name__ == "__main__":
    exit(main())
