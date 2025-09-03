#!/usr/bin/env python3
"""
Continuous Prediction Service for UPS Monitoring
Generates ML predictions every 15 minutes and stores them in MongoDB
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml.enhanced_model_trainer import EnhancedUPSModelTrainer
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuous_predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousPredictionService:
    def __init__(self):
        self.enhanced_trainer = EnhancedUPSModelTrainer()
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("DB_NAME", "UPS_DATA_MONITORING")
        self.collection_name = "ups_predictions"
        
        # Initialize MongoDB connection
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"✅ Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def generate_predictions(self):
        """Generate predictions and save to database using enhanced model trainer"""
        try:
            logger.info("🔄 Starting enhanced prediction generation cycle...")
            
            # Load the enhanced model
            if not self.enhanced_trainer.load_model():
                logger.error("❌ Failed to load enhanced model")
                return
            
            # Load UPS data directly from MongoDB
            try:
                client = MongoClient(self.mongodb_uri)
                db = client[self.db_name]
                ups_collection = db['upsdata']
                ups_data = list(ups_collection.find({}))
                client.close()
                
                if not ups_data:
                    logger.warning("⚠️ No UPS data available for predictions")
                    return
                
                logger.info(f"📊 Loaded {len(ups_data)} UPS records")
            except Exception as e:
                logger.error(f"❌ Failed to load UPS data: {e}")
                return
            
            # Generate enhanced predictions with detailed failure analysis
            predictions = []
            for ups in ups_data:
                try:
                    prediction_result = self.enhanced_trainer.predict_with_detailed_reasons(ups)
                    
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
                        predictions.append(enhanced_prediction)
                        
                        # Log high-risk predictions
                        if prediction_result['probability_failure'] > 0.7:
                            logger.warning(f"🚨 High failure risk for UPS {ups.get('name', 'Unknown')}: {prediction_result['probability_failure']:.2%}")
                        
                except Exception as e:
                    logger.error(f"❌ Error predicting for UPS {ups.get('name', 'Unknown')}: {e}")
                    continue
            
            if not predictions:
                logger.warning("⚠️ No enhanced predictions generated")
                return
            
            logger.info(f"🔮 Generated {len(predictions)} enhanced predictions with detailed failure analysis")
            
            # Save enhanced predictions to database
            try:
                client = MongoClient(self.mongodb_uri)
                db = client[self.db_name]
                prediction_collection = db[self.collection_name]
                
                # Clear old predictions and insert new ones
                prediction_collection.delete_many({})
                for prediction in predictions:
                    prediction_collection.insert_one(prediction)
                
                logger.info(f"💾 Saved {len(predictions)} enhanced predictions to database")
                client.close()
            except Exception as e:
                logger.error(f"❌ Failed to save enhanced predictions: {e}")
                return
            
            # Log summary
            high_risk = len([p for p in predictions if p.get('probability_failure', 0) > 0.7])
            medium_risk = len([p for p in predictions if 0.4 <= p.get('probability_failure', 0) <= 0.7])
            low_risk = len([p for p in predictions if p.get('probability_failure', 0) < 0.4])
            
            logger.info(f"📊 Prediction Summary:")
            logger.info(f"   High risk (>70%): {high_risk}")
            logger.info(f"   Medium risk (40-70%): {medium_risk}")
            logger.info(f"   Low risk (<40%): {low_risk}")
            
            logger.info(f"✅ Prediction cycle completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"❌ Error in prediction generation: {e}")
            logger.exception("Full traceback:")
    
    async def run_loop(self):
        """Async run method for FastAPI integration"""
        logger.info("🚀 Starting Continuous Prediction Service as FastAPI background task...")
        logger.info("⏰ Predictions will be generated every 15 minutes")
        
        # Generate initial predictions
        logger.info("🔄 Generating initial predictions...")
        self.generate_predictions()
        
        # Main loop
        try:
            while True:
                # Schedule predictions every 15 minutes
                await asyncio.sleep(30 * 60)  # Wait 15 minutes
                logger.info("🔄 Running scheduled prediction generation...")
                self.generate_predictions()
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in continuous prediction service: {e}")
        finally:
            if hasattr(self, 'client'):
                self.client.close()
                logger.info("🔌 MongoDB connection closed")
    
    def start_continuous_service(self):
        """Start the continuous prediction service (standalone mode)"""
        logger.info("🚀 Starting Continuous Prediction Service...")
        logger.info("⏰ Predictions will be generated every 15 minutes")
        
        # Schedule predictions every 15 minutes
        schedule.every(15).minutes.do(self.generate_predictions)
        
        # Generate initial predictions
        logger.info("🔄 Generating initial predictions...")
        self.generate_predictions()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Continuous Prediction Service stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            if hasattr(self, 'client'):
                self.client.close()
                logger.info("🔌 MongoDB connection closed")

def main():
    """Main function to start the continuous prediction service"""
    try:
        service = ContinuousPredictionService()
        service.start_continuous_service()
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
