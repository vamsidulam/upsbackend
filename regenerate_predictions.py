#!/usr/bin/env python3
"""
Regenerate predictions with detailed failure reasons using the fixed Gemini service
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from ml.enhanced_model_trainer import EnhancedUPSModelTrainer
from datetime import datetime
import logging

# Load environment variables
load_dotenv('atlas.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_predictions():
    """Regenerate predictions with detailed failure reasons"""
    try:
        logger.info("🔄 Starting prediction regeneration with detailed failure reasons...")
        
        # Initialize enhanced model trainer
        enhanced_trainer = EnhancedUPSModelTrainer()
        
        # Load the enhanced model
        if not enhanced_trainer.load_model():
            logger.error("❌ Failed to load enhanced model")
            return False
        
        logger.info("✅ Enhanced model loaded successfully")
        
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('DB_NAME')]
        ups_collection = db['upsdata']
        predictions_collection = db['ups_predictions']
        
        # Get current UPS data
        ups_data = list(ups_collection.find({}))
        if not ups_data:
            logger.error("❌ No UPS data found")
            return False
        
        logger.info(f"📊 Found {len(ups_data)} UPS systems")
        
        # Clear old predictions
        logger.info("🗑️ Clearing old predictions...")
        predictions_collection.delete_many({})
        
        # Generate new predictions with detailed failure reasons
        new_predictions = []
        for ups in ups_data:
            try:
                logger.info(f"🔮 Generating prediction for {ups.get('name', 'Unknown')}...")
                
                # Make prediction using enhanced model trainer
                prediction_result = enhanced_trainer.predict_with_detailed_reasons(ups)
                
                if prediction_result and prediction_result['probability_failure'] >= 0.4:  # Only non-healthy
                    # Create enhanced prediction with detailed failure analysis
                    enhanced_prediction = {
                        'ups_id': ups.get('upsId', 'Unknown'),
                        'ups_name': ups.get('name', 'Unknown'),
                        'ups_object_id': str(ups.get('_id')),
                        'timestamp': datetime.now().isoformat(),
                        'prediction': prediction_result['prediction'],
                        'probability_failure': prediction_result['probability_failure'],
                        'probability_healthy': prediction_result['probability_healthy'],
                        'confidence': prediction_result['confidence'],
                        'current_status': ups.get('status', 'unknown'),
                        'risk_assessment': {
                            'risk_level': 'high' if prediction_result['probability_failure'] > 0.7 else 'medium' if prediction_result['probability_failure'] > 0.4 else 'low',
                            'timeframe': '6_hours' if prediction_result['probability_failure'] > 0.7 else '12_hours' if prediction_result['probability_failure'] > 0.4 else '24_hours',
                            'failure_reasons': prediction_result['failure_reasons'],
                            'failure_summary': f"Enhanced AI model predicts {prediction_result['probability_failure']:.1%} chance of failure in next {('6_hours' if prediction_result['probability_failure'] > 0.7 else '12_hours' if prediction_result['probability_failure'] > 0.4 else '24_hours')}. Monitor closely.",
                            'technical_details': {
                                'battery_health': ups.get('batteryLevel', 100),
                                'temperature_status': ups.get('temperature', 25),
                                'efficiency_rating': ups.get('efficiency', 100),
                                'load_percentage': ups.get('load', 0),
                                'power_balance': (ups.get('powerInput', 0) - ups.get('powerOutput', 0)),
                                'capacity': ups.get('capacity', 2000),
                                'uptime': ups.get('uptime', 100),
                                'manufacturer': ups.get('manufacturer', 'Unknown'),
                                'model': ups.get('model', 'Unknown')
                            }
                        }
                    }
                    
                    new_predictions.append(enhanced_prediction)
                    
                    # Log the detailed failure reasons
                    if prediction_result.get('failure_reasons'):
                        logger.info(f"✅ Generated {len(prediction_result['failure_reasons'])} detailed failure reasons for {ups.get('name', 'Unknown')}")
                        for i, reason in enumerate(prediction_result['failure_reasons'][:2], 1):  # Show first 2
                            logger.info(f"   {i}. {reason[:100]}...")
                    else:
                        logger.warning(f"⚠️ No failure reasons generated for {ups.get('name', 'Unknown')}")
                        
            except Exception as e:
                logger.error(f"❌ Error predicting for UPS {ups.get('name', 'Unknown')}: {e}")
                continue
        
        if not new_predictions:
            logger.warning("⚠️ No enhanced predictions generated")
            return False
        
        logger.info(f"🔮 Generated {len(new_predictions)} enhanced predictions with detailed failure analysis")
        
        # Save new predictions to database
        try:
            for prediction in new_predictions:
                predictions_collection.insert_one(prediction)
            
            logger.info(f"💾 Saved {len(new_predictions)} enhanced predictions to database")
            
            # Log summary
            high_risk = len([p for p in new_predictions if p.get('probability_failure', 0) > 0.7])
            medium_risk = len([p for p in new_predictions if 0.4 <= p.get('probability_failure', 0) <= 0.7])
            low_risk = len([p for p in new_predictions if p.get('probability_failure', 0) < 0.4])
            
            logger.info(f"📊 Prediction Summary:")
            logger.info(f"   High risk (>70%): {high_risk}")
            logger.info(f"   Medium risk (40-70%): {medium_risk}")
            logger.info(f"   Low risk (<40%): {low_risk}")
            
            logger.info(f"✅ Prediction regeneration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save enhanced predictions: {e}")
            return False
            
        finally:
            client.close()
        
    except Exception as e:
        logger.error(f"❌ Error in prediction regeneration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = regenerate_predictions()
    if success:
        print("\n🎉 Predictions regenerated successfully with detailed failure reasons!")
        print("🔍 Check the database to see the new detailed predictions.")
    else:
        print("\n❌ Failed to regenerate predictions.")
        print("🔍 Check the logs for error details.")
