import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
from ml.enhanced_model_trainer import EnhancedUPSModelTrainer
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('predictive_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UPSPredictiveMonitor:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = "UPS_DATA_MONITORING"
        self.collection_name = "upsdata"
        self.history_collection_name = "ups_history"
        self.model_trainer = EnhancedUPSModelTrainer()
        self.monitoring_interval = 15 * 60  # 15 minutes
        self.prediction_interval = 15 * 60  # 15 minutes
        self.last_prediction_time = None
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
            return collection, client
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return None, None
    
    def _fetch_recent_history(self, ups_id: str, minutes: int = 60, limit: int = 60):
        """Fetch recent history rows for a UPS from ups_history."""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            coll = db[self.history_collection_name]
            cursor = coll.find({"upsId": ups_id}).sort("timestamp", -1).limit(limit)
            data = list(cursor)
            client.close()
            return data
        except Exception as e:
            logger.error(f"Error fetching history for {ups_id}: {e}")
            return []

    def _compute_history_risk(self, history: list) -> float:
        """Compute a simple failure risk score (0..1) from recent history."""
        if not history:
            return 0.0
        try:
            # Use last values and trends
            temps = [float(h.get('temperature', 25.0)) for h in history]
            bats = [float(h.get('batteryLevel', 100.0)) for h in history]
            effs = [float(h.get('efficiency', 95.0)) for h in history]
            loads = [float(h.get('load', 50.0)) if 'load' in h else None for h in history]
            loads = [l for l in loads if l is not None]

            # Normalize components to 0..1
            temp_component = 0.0
            if temps:
                t_max = max(temps)
                # 28C -> 0, 45C -> 1
                temp_component = max(0.0, min(1.0, (t_max - 28.0) / (45.0 - 28.0)))

            battery_component = 0.0
            if bats:
                b_now = bats[0]
                b_min = min(bats)
                # Lower battery and steep recent drop increases risk
                level_component = 1.0 - max(0.0, min(1.0, b_now / 100.0))
                drop = bats[0] - bats[-1] if len(bats) > 1 else 0.0
                drop_component = max(0.0, min(1.0, abs(drop) / 20.0))
                battery_component = 0.6 * level_component + 0.4 * drop_component

            efficiency_component = 0.0
            if effs:
                e_now = effs[0]
                # 95% -> 0, 80% -> 1
                efficiency_component = max(0.0, min(1.0, (95.0 - e_now) / (95.0 - 80.0)))

            load_component = 0.0
            if loads:
                l_max = max(loads)
                # 70% -> 0, 95% -> 1
                load_component = max(0.0, min(1.0, (l_max - 70.0) / (95.0 - 70.0)))

            # Weighted sum
            risk = 0.3 * temp_component + 0.3 * battery_component + 0.2 * efficiency_component + 0.2 * load_component
            return float(max(0.0, min(1.0, risk)))
        except Exception as e:
            logger.error(f"Error computing history risk: {e}")
            return 0.0

    def load_ups_data(self):
        """Load current UPS data from MongoDB"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return None
            
            # Get all UPS data
            cursor = collection.find({})
            data = list(cursor)
            
            if not data:
                logger.warning("⚠️ No UPS data found in MongoDB")
                return None
            
            logger.info(f"✅ Loaded {len(data)} UPS records")
            return data, client
            
        except Exception as e:
            logger.error(f"❌ Error loading UPS data: {e}")
            return None, None
    
    def make_predictions(self, ups_data):
        """Make predictions for all UPS systems"""
        try:
            if not self.model_trainer.load_model():
                logger.warning("⚠️ Model not loaded, skipping predictions")
                return []
            
            predictions = []
            for ups in ups_data:
                try:
                    ups_id = ups.get('upsId') or ups.get('name') or str(ups.get('_id'))
                    # Fetch recent history and compute derived risk
                    history = self._fetch_recent_history(ups_id, minutes=60, limit=60)
                    history_risk = self._compute_history_risk(history)
                    # Inject history-derived features
                    ups['failureRisk'] = history_risk
                    # Optionally adjust temperature/efficiency/load with recent averages if available
                    if history:
                        try:
                            ups['temperature'] = float(np.mean([h.get('temperature', ups.get('temperature', 25.0)) for h in history[:5]]))
                            ups['efficiency'] = float(np.mean([h.get('efficiency', ups.get('efficiency', 95.0)) for h in history[:5]]))
                            # keep load if present; not all history rows have load
                            recent_loads = [h.get('load') for h in history[:5] if 'load' in h]
                            if recent_loads:
                                ups['load'] = float(np.mean(recent_loads))
                        except Exception:
                            pass
                    prediction = self.model_trainer.predict_with_detailed_reasons(ups)
                    if prediction:
                        prediction_data = {
                            'ups_id': ups.get('upsId', 'Unknown'),
                            'ups_name': ups.get('name', 'Unknown'),
                            'ups_object_id': str(ups.get('_id')),  # Store MongoDB ObjectId as reference
                            'timestamp': datetime.now().isoformat(),
                            'prediction': prediction['prediction'],
                            'probability_failure': prediction['probability_failure'],
                            'probability_healthy': prediction['probability_healthy'],
                            'confidence': prediction['confidence'],
                            'current_status': ups.get('status', 'unknown'),
                            # Add enhanced failure analysis data from enhanced model trainer
                            'risk_assessment': {
                                'risk_level': 'high' if prediction['probability_failure'] > 0.7 else 'medium' if prediction['probability_failure'] > 0.4 else 'low',
                                'timeframe': '6_hours' if prediction['probability_failure'] > 0.7 else '12_hours' if prediction['probability_failure'] > 0.4 else '24_hours',
                                'failure_reasons': prediction.get('failure_reasons', []),
                                'failure_summary': f"Enhanced ML model predicts {prediction['probability_failure']:.1%} chance of failure in next {('6_hours' if prediction['probability_failure'] > 0.7 else '12_hours' if prediction['probability_failure'] > 0.4 else '24_hours')}. Monitor closely.",
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
                        predictions.append(prediction_data)
                        
                        # Log high-risk predictions
                        if prediction['probability_failure'] > 0.7:
                            logger.warning(f"🚨 High failure risk for UPS {ups.get('name', 'Unknown')}: {prediction['probability_failure']:.2%}")
                        
                except Exception as e:
                    logger.error(f"❌ Error predicting for UPS {ups.get('name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Made predictions for {len(predictions)} UPS systems")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error making predictions: {e}")
            return []
    
    def save_predictions(self, predictions):
        """Save predictions to MongoDB"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return False
            
            # Save predictions to a separate collection
            prediction_collection = client[self.db_name]['ups_predictions']
            
            for prediction in predictions:
                prediction_collection.insert_one(prediction)
            
            logger.info(f"✅ Saved {len(predictions)} predictions to MongoDB")
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving predictions: {e}")
            return False
    
    def generate_health_report(self, ups_data, predictions):
        """Generate comprehensive health report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_ups': len(ups_data),
                'healthy_count': 0,
                'warning_count': 0,
                'failed_count': 0,
                'high_risk_count': 0,
                'predictions_summary': {
                    'total_predictions': len(predictions),
                    'healthy_predictions': 0,
                    'failure_predictions': 0,
                    'average_confidence': 0.0
                },
                'ups_details': []
            }
            
            # Count current statuses
            for ups in ups_data:
                status = ups.get('status', 'unknown')
                if status == 'healthy':
                    report['healthy_count'] += 1
                elif status == 'warning':
                    report['warning_count'] += 1
                elif status == 'failed':
                    report['failed_count'] += 1
            
            # Analyze predictions
            if predictions:
                failure_predictions = sum(1 for p in predictions if p['prediction'] == 1)
                report['predictions_summary']['failure_predictions'] = failure_predictions
                report['predictions_summary']['healthy_predictions'] = len(predictions) - failure_predictions
                
                avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)
                report['predictions_summary']['average_confidence'] = round(avg_confidence, 3)
                
                # Count high-risk UPS
                report['high_risk_count'] = sum(1 for p in predictions if p['probability_failure'] > 0.7)
            
            # Add UPS details
            for ups in ups_data:
                ups_detail = {
                    'id': str(ups.get('_id')),
                    'name': ups.get('name', 'Unknown'),
                    'status': ups.get('status', 'unknown'),
                    'battery_level': ups.get('batteryLevel', 0),
                    'temperature': ups.get('temperature', 0),
                    'efficiency': ups.get('efficiency', 0)
                }
                
                # Find corresponding prediction
                prediction = next((p for p in predictions if p['ups_id'] == ups.get('_id')), None)
                if prediction:
                    ups_detail['prediction'] = {
                        'status': 'failure' if prediction['prediction'] == 1 else 'healthy',
                        'probability_failure': prediction['probability_failure'],
                        'confidence': prediction['confidence']
                    }
                
                report['ups_details'].append(ups_detail)
            
            # Save report to file
            report_file = 'ups_model_prediction.health_report.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"✅ Health report generated and saved to {report_file}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating health report: {e}")
            return None
    
    async def monitor_ups_systems(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting UPS Predictive Monitoring System...")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Load current UPS data
                ups_data_result = self.load_ups_data()
                if ups_data_result is None:
                    logger.error("❌ Failed to load UPS data, retrying in 5 minutes...")
                    await asyncio.sleep(300)
                    continue
                
                ups_data, client = ups_data_result
                
                # Make predictions every 15 minutes
                if (self.last_prediction_time is None or 
                    (current_time - self.last_prediction_time).total_seconds() >= self.prediction_interval):
                    
                    logger.info("🔮 Making predictions for all UPS systems...")
                    predictions = self.make_predictions(ups_data)
                    
                    if predictions:
                        # Save predictions
                        self.save_predictions(predictions)
                        
                        # Generate health report
                        self.generate_health_report(ups_data, predictions)
                        
                        self.last_prediction_time = current_time
                        
                        logger.info(f"✅ Prediction cycle completed at {current_time.strftime('%H:%M:%S')}")
                
                # Close MongoDB connection
                if client:
                    client.close()
                
                # Wait for next monitoring cycle
                logger.info(f"⏰ Next monitoring cycle in {self.monitoring_interval // 60} minutes...")
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def start_monitoring(self):
        """Start the monitoring system"""
        try:
            asyncio.run(self.monitor_ups_systems())
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring system stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error in monitoring system: {e}")

def main():
    """Main function to start the predictive monitor"""
    monitor = UPSPredictiveMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
