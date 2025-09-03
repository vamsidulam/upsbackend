#!/usr/bin/env python3
"""
Real-Time UPS Monitoring and Failure Prediction System
Uses the trained ML model to continuously monitor UPS systems
"""

import time
import logging
import json
from datetime import datetime
from ml.enhanced_model_trainer import EnhancedUPSModelTrainer
from pymongo import MongoClient
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_time_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimeUPSMonitor:
    def __init__(self):
        self.model_trainer = EnhancedUPSModelTrainer()
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = "UPS_DATA_MONITORING"
        self.collection_name = "upsdata"
        self.prediction_collection_name = "ups_predictions"
        self.monitoring_interval = 15 * 60  # 15 minutes
        self.is_running = False
        
    def initialize(self):
        """Initialize the monitoring system"""
        try:
            # Load or train the ML model
            if not self.model_trainer.load_model():
                logger.info("No existing model found. Training new model...")
                if not self.model_trainer.train_model():
                    logger.error("Failed to train model. Cannot continue monitoring.")
                    return False
                logger.info("Model training completed successfully!")
            else:
                logger.info("ML model loaded successfully!")
            
            # Test MongoDB connection
            if not self.test_mongodb_connection():
                logger.error("MongoDB connection failed. Cannot continue monitoring.")
                return False
            
            logger.info("Real-time UPS monitoring system initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing monitoring system: {e}")
            return False
    
    def test_mongodb_connection(self):
        """Test MongoDB connection"""
        try:
            client = MongoClient(self.mongo_uri)
            client.admin.command('ping')
            client.close()
            logger.info("MongoDB connection test successful!")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            return False
    
    def get_ups_data_from_mongodb(self):
        """Get current UPS data from MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            
            # Get all UPS systems
            ups_systems = list(collection.find({}))
            client.close()
            
            if not ups_systems:
                logger.warning("No UPS systems found in database")
                return []
            
            logger.info(f"Retrieved {len(ups_systems)} UPS systems from database")
            return ups_systems
            
        except Exception as e:
            logger.error(f"Error retrieving UPS data from MongoDB: {e}")
            return []
    
    def save_prediction_to_mongodb(self, prediction_data):
        """Save prediction results to MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.prediction_collection_name]
            
            # Add timestamp if not present
            if 'timestamp' not in prediction_data:
                prediction_data['timestamp'] = datetime.now().isoformat()
            
            # Insert prediction
            result = collection.insert_one(prediction_data)
            client.close()
            
            logger.info(f"Prediction saved to MongoDB with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prediction to MongoDB: {e}")
            return False
    
    def monitor_ups_systems(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting real-time UPS monitoring...")
        self.is_running = True
        
        try:
            while self.is_running:
                current_time = datetime.now()
                logger.info(f"⏰ Monitoring cycle started at {current_time.strftime('%H:%M:%S')}")
                
                # Get current UPS data
                ups_systems = self.get_ups_data_from_mongodb()
                
                if ups_systems:
                    # Make predictions for each UPS system
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
                            
                            # Make prediction
                            prediction_result = self.model_trainer.predict_with_detailed_reasons(ups_data)
                            
                            if prediction_result:
                                # Add UPS identification
                                prediction_result['ups_id'] = ups.get('upsId', 'Unknown')
                                prediction_result['ups_name'] = ups.get('name', 'Unknown')
                                prediction_result['timestamp'] = current_time.isoformat()
                                
                                # Save prediction to database
                                if self.save_prediction_to_mongodb(prediction_result):
                                    predictions_made += 1
                                    
                                    # Log prediction details
                                    status = "🚨 WILL FAIL" if prediction_result['prediction'] == 1 else "✅ HEALTHY"
                                    logger.info(f"UPS {prediction_result['ups_id']} ({prediction_result['ups_name']}): {status}")
                                    logger.info(f"  Failure Probability: {prediction_result['probability_failure']:.1%}")
                                    logger.info(f"  Confidence: {prediction_result['confidence']:.1%}")
                                    
                                    # Log critical issues
                                    if prediction_result['prediction'] == 1:
                                        logger.warning(f"🚨 CRITICAL: UPS {prediction_result['ups_id']} predicted to fail!")
                                        for reason in prediction_result['failure_reasons']:
                                            logger.warning(f"  {reason}")
                                
                        except Exception as e:
                            logger.error(f"Error processing UPS {ups.get('upsId', 'Unknown')}: {e}")
                            continue
                    
                    logger.info(f"✅ Monitoring cycle completed. Made {predictions_made} predictions.")
                else:
                    logger.warning("No UPS systems to monitor in this cycle.")
                
                # Wait for next monitoring cycle
                logger.info(f"⏰ Next monitoring cycle in {self.monitoring_interval // 60} minutes...")
                time.sleep(self.monitoring_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
        finally:
            self.is_running = False
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        logger.info("🛑 Stopping UPS monitoring system...")
        self.is_running = False
    
    def run_simulation_mode(self, num_simulations=10, delay_seconds=2):
        """Run in simulation mode for testing"""
        logger.info(f"🎮 Running in simulation mode ({num_simulations} simulations, {delay_seconds}s delay)")
        
        if not self.model_trainer.load_model():
            logger.error("Cannot run simulation: Model not loaded")
            return
        
        self.model_trainer.simulate_real_time_predictions(
            num_simulations=num_simulations, 
            delay_seconds=delay_seconds
        )

def main():
    """Main function"""
    monitor = RealTimeUPSMonitor()
    
    # Initialize the system
    if not monitor.initialize():
        logger.error("Failed to initialize monitoring system. Exiting.")
        return
    
    try:
        # Check command line arguments for simulation mode
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--simulation':
            num_sims = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor.run_simulation_mode(num_simulations=num_sims, delay_seconds=1)
        else:
            # Run real-time monitoring
            monitor.monitor_ups_systems()
            
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
