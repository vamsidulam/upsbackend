#!/usr/bin/env python3
"""
Integration script to connect ML predictions with your existing UPS monitoring system
"""

import asyncio
import logging
from datetime import datetime
from ml.enhanced_model_trainer import EnhancedUPSModelTrainer
from pymongo import MongoClient
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPredictionIntegrator:
    def __init__(self):
        self.model_trainer = EnhancedUPSModelTrainer()
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = "UPS_DATA_MONITORING"
        self.ups_collection = "upsdata"
        self.predictions_collection = "predictions"
        
    def initialize(self):
        """Initialize the ML prediction system"""
        try:
            # Load the trained model
            if not self.model_trainer.load_model():
                logger.error("Failed to load ML model")
                return False
            
            # Test MongoDB connection
            client = MongoClient(self.mongo_uri)
            client.admin.command('ping')
            client.close()
            
            logger.info("ML Prediction Integrator initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing ML system: {e}")
            return False
    
    def get_ups_systems(self):
        """Get all UPS systems from MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.ups_collection]
            
            ups_systems = list(collection.find({}))
            client.close()
            
            return ups_systems
            
        except Exception as e:
            logger.error(f"Error getting UPS systems: {e}")
            return []
    
    def save_prediction(self, prediction_data):
        """Save prediction to the predictions collection"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.predictions_collection]
            
            # Add timestamp if not present
            if 'timestamp' not in prediction_data:
                prediction_data['timestamp'] = datetime.now().isoformat()
            
            # Insert prediction
            result = collection.insert_one(prediction_data)
            client.close()
            
            logger.info(f"Prediction saved with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return False
    
    def generate_predictions_for_all_ups(self):
        """Generate predictions for all UPS systems"""
        try:
            ups_systems = self.get_ups_systems()
            
            if not ups_systems:
                logger.warning("No UPS systems found")
                return 0
            
            logger.info(f"Generating predictions for {len(ups_systems)} UPS systems...")
            
            predictions_made = 0
            
            for ups in ups_systems:
                try:
                    # Prepare UPS data for prediction
                    ups_data = {
                        'powerInput': ups.get('powerInput', 0),
                        'powerOutput': ups.get('powerOutput', 0),
                        'batteryLevel': ups.get('batteryLevel', 100),
                        'temperature': ups.get('temperature', 25),
                        'load': ups.get('load', 0)
                    }
                    
                    # Make ML prediction
                    prediction_result = self.model_trainer.predict_with_detailed_reasons(ups_data)
                    
                    if prediction_result:
                        # Add UPS identification
                        prediction_result['ups_id'] = ups.get('upsId', 'Unknown')
                        prediction_result['ups_name'] = ups.get('name', 'Unknown')
                        prediction_result['timestamp'] = datetime.now().isoformat()
                        
                        # Save prediction
                        if self.save_prediction(prediction_result):
                            predictions_made += 1
                            
                            # Log prediction details
                            status = "🚨 WILL FAIL" if prediction_result['prediction'] == 1 else "✅ HEALTHY"
                            logger.info(f"UPS {prediction_result['ups_id']}: {status}")
                            logger.info(f"  Failure Probability: {prediction_result['probability_failure']:.1%}")
                            
                            # Log critical issues
                            if prediction_result['prediction'] == 1:
                                logger.warning(f"🚨 CRITICAL: UPS {prediction_result['ups_id']} predicted to fail!")
                                for reason in prediction_result['failure_reasons']:
                                    logger.warning(f"  {reason}")
                
                except Exception as e:
                    logger.error(f"Error processing UPS {ups.get('upsId', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Generated {predictions_made} predictions successfully!")
            return predictions_made
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return 0
    
    def run_continuous_predictions(self, interval_minutes=15):
        """Run continuous predictions at specified interval"""
        logger.info(f"🚀 Starting continuous ML predictions every {interval_minutes} minutes...")
        
        try:
            while True:
                current_time = datetime.now()
                logger.info(f"⏰ Prediction cycle started at {current_time.strftime('%H:%M:%S')}")
                
                # Generate predictions for all UPS systems
                predictions_made = self.generate_predictions_for_all_ups()
                
                if predictions_made > 0:
                    logger.info(f"✅ Prediction cycle completed. Generated {predictions_made} predictions.")
                else:
                    logger.warning("⚠️ No predictions generated in this cycle.")
                
                # Wait for next cycle
                logger.info(f"⏰ Next prediction cycle in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("🛑 Continuous predictions stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in continuous predictions: {e}")

def main():
    """Main function"""
    integrator = MLPredictionIntegrator()
    
    # Initialize the system
    if not integrator.initialize():
        logger.error("Failed to initialize ML system. Exiting.")
        return
    
    try:
        # Check command line arguments
        import sys
        if len(sys.argv) > 1:
            if sys.argv[1] == '--once':
                # Generate predictions once
                integrator.generate_predictions_for_all_ups()
            elif sys.argv[1] == '--continuous':
                # Run continuous predictions
                interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
                integrator.run_continuous_predictions(interval)
            else:
                print("Usage:")
                print("  python integrate_ml_predictions.py --once          # Generate predictions once")
                print("  python integrate_ml_predictions.py --continuous   # Run continuous predictions (15 min)")
                print("  python integrate_ml_predictions.py --continuous 5 # Run continuous predictions (5 min)")
        else:
            # Default: generate predictions once
            integrator.generate_predictions_for_all_ups()
            
    except KeyboardInterrupt:
        logger.info("🛑 ML predictions stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
