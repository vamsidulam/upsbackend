#!/usr/bin/env python3
"""
Test script for Gemini AI integration only
Generates detailed failure reasons using Gemini AI for UPS predictions
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_gemini_predictions():
    """Generate predictions using only Gemini AI and store in database"""
    logger.info("Generating predictions with Gemini AI...")
    
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
        
        # Initialize Gemini service
        gemini_service = GeminiAIService()
        
        if not gemini_service.model:
            logger.error("Gemini AI service not available")
            return
        
        # Generate predictions for each UPS
        enhanced_predictions = []
        for ups in ups_data_list[:5]:  # Limit to first 5 for testing
            try:
                logger.info(f"Processing UPS: {ups.get('name', 'Unknown')} (ID: {ups.get('upsId', 'Unknown')})")
                
                # Simulate ML prediction data based on UPS metrics
                battery_level = ups.get('batteryLevel', 100)
                temperature = ups.get('temperature', 25)
                load = ups.get('load', 0)
                efficiency = ups.get('efficiency', 100)
                
                # Calculate failure probability based on metrics
                failure_score = 0
                if battery_level < 30: failure_score += 0.4
                elif battery_level < 50: failure_score += 0.2
                
                if temperature > 45: failure_score += 0.3
                elif temperature > 40: failure_score += 0.15
                
                if load > 90: failure_score += 0.3
                elif load > 80: failure_score += 0.15
                
                if efficiency < 80: failure_score += 0.2
                elif efficiency < 90: failure_score += 0.1
                
                probability_failure = min(failure_score, 0.95)  # Cap at 95%
                confidence = 0.85 + (probability_failure * 0.1)  # Higher confidence for higher failure probability
                
                # Create prediction data for Gemini
                prediction_data = {
                    'probability_failure': probability_failure,
                    'confidence': confidence
                }
                
                # Use Gemini AI to generate enhanced failure reasons
                gemini_failure_reasons = gemini_service.generate_failure_reasons(ups, prediction_data)
                
                # Create enhanced prediction object
                enhanced_prediction = {
                    'ups_id': ups.get('upsId', 'Unknown'),
                    'ups_name': ups.get('name', 'Unknown'),
                    'probability_failure': probability_failure,
                    'probability_healthy': 1 - probability_failure,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat(),
                    'prediction_data': {
                        'battery_level': battery_level,
                        'temperature': temperature,
                        'load': load,
                        'efficiency': efficiency,
                        'power_input': ups.get('powerInput', 0),
                        'power_output': ups.get('powerOutput', 0),
                        'voltage_input': ups.get('voltageInput', 0),
                        'voltage_output': ups.get('voltageOutput', 0),
                        'frequency': ups.get('frequency', 50),
                        'uptime': ups.get('uptime', 0),
                        'capacity': ups.get('capacity', 0)
                    },
                    'risk_assessment': {
                        'risk_level': 'low' if probability_failure < 0.4 else 'medium' if probability_failure < 0.7 else 'high',
                        'timeframe': '24_hours' if probability_failure < 0.4 else '12_hours' if probability_failure < 0.7 else '6_hours',
                        'failure_reasons': gemini_failure_reasons,
                        'failure_summary': f"Gemini AI enhanced analysis predicts {probability_failure:.1%} failure probability with {confidence:.1%} confidence.",
                        'technical_details': {
                            'battery_health': battery_level,
                            'temperature_status': temperature,
                            'efficiency_rating': efficiency,
                            'load_percentage': load,
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
        logger.error(f"Error in generate_gemini_predictions: {e}")
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Main function"""
    logger.info("Starting Gemini AI only test...")
    
    # Generate predictions using Gemini AI
    generate_gemini_predictions()
    
    logger.info("Gemini AI only test completed")
    return 0

if __name__ == "__main__":
    exit(main())
