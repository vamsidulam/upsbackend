#!/usr/bin/env python3
"""
Alert Service for UPS Monitoring System
Generates structured alerts based on UPS status and ML predictions
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import uuid

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = "UPS_DATA_MONITORING"
        self.collection_name = "upsdata"
        
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
    
    def generate_status_alerts(self, ups_data):
        """Generate alerts based on UPS status"""
        alerts = []
        
        for ups in ups_data:
            ups_id = str(ups.get('_id'))
            ups_name = ups.get('name', 'Unknown')
            status = ups.get('status', 'unknown')
            battery_level = ups.get('batteryLevel', 100)
            temperature = ups.get('temperature', 25)
            efficiency = ups.get('efficiency', 95)
            
            # Generate alerts based on status
            if status == 'failed':
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'status_alert',
                    'title': f'UPS {ups_name} - System Failure',
                    'message': f'UPS {ups_name} has failed. Battery: {battery_level}%, Temperature: {temperature}°C, Efficiency: {efficiency}%',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'system_status',
                    'value': status,
                    'threshold': 'operational',
                    'severity': 'critical',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': self._get_failure_reasons(battery_level, temperature, efficiency),
                    'risk_category': 'immediate',
                    'primary_risk': 'system_failure',
                    'prediction_timeframe': 'immediate',
                    'recommended_action': 'Immediate maintenance required. Check battery, temperature, and efficiency.',
                    'confidence': 1.0
                }
                alerts.append(alert)
                
            elif status == 'warning':
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'status_alert',
                    'title': f'UPS {ups_name} - Warning Condition',
                    'message': f'UPS {ups_name} is showing warning signs. Battery: {battery_level}%, Temperature: {temperature}°C, Efficiency: {efficiency}%',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'system_status',
                    'value': status,
                    'threshold': 'operational',
                    'severity': 'warning',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': self._get_failure_reasons(battery_level, temperature, efficiency),
                    'risk_category': 'elevated',
                    'primary_risk': 'performance_degradation',
                    'prediction_timeframe': '24_hours',
                    'recommended_action': 'Monitor closely. Schedule maintenance if conditions worsen.',
                    'confidence': 0.8
                }
                alerts.append(alert)
            
            # Generate specific metric alerts
            if battery_level < 20:
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'metric_alert',
                    'title': f'UPS {ups_name} - Low Battery',
                    'message': f'Battery level is critically low: {battery_level}%',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'battery_level',
                    'value': battery_level,
                    'threshold': 20,
                    'severity': 'critical' if battery_level < 10 else 'warning',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': ['low_battery'],
                    'risk_category': 'elevated' if battery_level < 10 else 'moderate',
                    'primary_risk': 'battery_failure',
                    'prediction_timeframe': 'immediate' if battery_level < 10 else '4_hours',
                    'recommended_action': 'Check battery health and consider replacement.',
                    'confidence': 0.9
                }
                alerts.append(alert)
            
            if temperature > 40:
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'metric_alert',
                    'title': f'UPS {ups_name} - High Temperature',
                    'message': f'Temperature is elevated: {temperature}°C',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'temperature',
                    'value': temperature,
                    'threshold': 40,
                    'severity': 'critical' if temperature > 45 else 'warning',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': ['high_temperature'],
                    'risk_category': 'elevated' if temperature > 45 else 'moderate',
                    'primary_risk': 'thermal_stress',
                    'prediction_timeframe': 'immediate' if temperature > 45 else '8_hours',
                    'recommended_action': 'Check cooling system and ventilation.',
                    'confidence': 0.85
                }
                alerts.append(alert)
            
            if efficiency < 90:
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'metric_alert',
                    'title': f'UPS {ups_name} - Low Efficiency',
                    'message': f'Efficiency is below normal: {efficiency}%',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'efficiency',
                    'value': efficiency,
                    'threshold': 90,
                    'severity': 'warning',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': ['low_efficiency'],
                    'risk_category': 'moderate',
                    'primary_risk': 'performance_degradation',
                    'prediction_timeframe': '24_hours',
                    'recommended_action': 'Monitor performance and schedule maintenance.',
                    'confidence': 0.7
                }
                alerts.append(alert)
        
        return alerts
    
    def generate_ml_prediction_alerts(self, predictions):
        """Generate alerts based on ML predictions"""
        alerts = []
        
        for prediction in predictions:
            ups_id = str(prediction.get('ups_id', ''))
            ups_name = prediction.get('ups_name', 'Unknown')
            probability_failure = prediction.get('probability_failure', 0)
            confidence = prediction.get('confidence', 0)
            
            if probability_failure > 0.7:  # High risk
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'ml_prediction',
                    'title': f'UPS {ups_name} - High Failure Risk',
                    'message': f'ML model predicts {probability_failure:.1%} chance of failure within 6 hours',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'ml_prediction',
                    'value': probability_failure,
                    'threshold': 0.7,
                    'severity': 'critical',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': ['ml_high_risk_prediction'],
                    'risk_category': 'high',
                    'primary_risk': 'predicted_failure',
                    'prediction_timeframe': '6_hours',
                    'recommended_action': 'Immediate inspection and preventive maintenance required.',
                    'confidence': confidence
                }
                alerts.append(alert)
                
            elif probability_failure > 0.5:  # Medium risk
                alert = {
                    '_id': str(uuid.uuid4()),
                    'type': 'ml_prediction',
                    'title': f'UPS {ups_name} - Elevated Failure Risk',
                    'message': f'ML model predicts {probability_failure:.1%} chance of failure within 24 hours',
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'ml_prediction',
                    'value': probability_failure,
                    'threshold': 0.5,
                    'severity': 'warning',
                    'status': 'active',
                    'ups_id': ups_id,
                    'ups_name': ups_name,
                    'failure_reasons': ['ml_medium_risk_prediction'],
                    'risk_category': 'elevated',
                    'primary_risk': 'predicted_failure',
                    'prediction_timeframe': '24_hours',
                    'recommended_action': 'Schedule maintenance and monitor closely.',
                    'confidence': confidence
                }
                alerts.append(alert)
        
        return alerts
    
    def _get_failure_reasons(self, battery_level, temperature, efficiency):
        """Get failure reasons based on metrics"""
        reasons = []
        
        if battery_level < 20:
            reasons.append('low_battery')
        if temperature > 40:
            reasons.append('high_temperature')
        if efficiency < 90:
            reasons.append('low_efficiency')
        
        return reasons if reasons else ['unknown']
    
    def update_ups_alerts(self):
        """Update alerts for all UPS systems"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return False
            
            # Get all UPS data
            cursor = collection.find({})
            ups_data = list(cursor)
            
            if not ups_data:
                logger.warning("⚠️ No UPS data found")
                client.close()
                return False
            
            # Generate status-based alerts
            status_alerts = self.generate_status_alerts(ups_data)
            
            # Get ML predictions if available and store them
            try:
                prediction_collection = client[self.db_name]['ups_predictions']
                predictions = list(prediction_collection.find().sort('timestamp', -1).limit(100))
                
                # Store predictions separately for the predictions API
                if predictions:
                    self.store_ml_predictions(predictions)
                
                ml_alerts = self.generate_ml_prediction_alerts(predictions)
            except:
                ml_alerts = []
            
            # Combine all alerts
            all_alerts = status_alerts + ml_alerts
            
            # Update each UPS with its alerts
            for ups in ups_data:
                ups_id = ups.get('_id')
                ups_alerts = [alert for alert in all_alerts if alert.get('ups_id') == str(ups_id)]
                
                # Update UPS document with alerts
                collection.update_one(
                    {'_id': ups_id},
                    {'$set': {'alerts': ups_alerts}}
                )
            
            logger.info(f"✅ Updated alerts for {len(ups_data)} UPS systems")
            logger.info(f"📊 Generated {len(all_alerts)} total alerts")
            
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating UPS alerts: {e}")
            return False
    
    def get_alerts_summary(self):
        """Get summary of all alerts"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return {}
            
            # Count alerts by severity
            pipeline = [
                {"$unwind": "$alerts"},
                {"$group": {
                    "_id": "$alerts.severity",
                    "count": {"$sum": 1}
                }}
            ]
            
            result = list(collection.aggregate(pipeline))
            
            summary = {
                'critical': 0,
                'warning': 0,
                'info': 0,
                'total': 0
            }
            
            for item in result:
                severity = item['_id']
                count = item['count']
                summary[severity] = count
                summary['total'] += count
            
            client.close()
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting alerts summary: {e}")
            return {'critical': 0, 'warning': 0, 'info': 0, 'total': 0}

    def get_latest_predictions(self, limit=20):
        """Get the latest ML predictions from the database"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return []
            
            # Get predictions collection
            db = client[self.db_name]
            predictions_collection = db['ups_predictions']
            
            # Get latest predictions sorted by timestamp
            cursor = predictions_collection.find().sort('timestamp', -1).limit(limit)
            predictions = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for pred in predictions:
                pred['_id'] = str(pred['_id'])
                pred['timestamp'] = pred['timestamp'].isoformat()
            
            logger.info(f"✅ Retrieved {len(predictions)} latest predictions")
            client.close()
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error getting latest predictions: {e}")
            return []

    def store_ml_predictions(self, predictions):
        """Store ML predictions separately in the database"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return False
            
            # Get or create predictions collection
            db = client[self.db_name]
            predictions_collection = db['ups_predictions']
            
            # Clear old predictions (keep last 100)
            predictions_collection.delete_many({})
            
            # Store new predictions with enhanced data
            for prediction in predictions:
                prediction_doc = {
                    '_id': str(uuid.uuid4()),
                    'ups_id': prediction.get('ups_id', ''),
                    'ups_name': prediction.get('ups_name', 'Unknown'),
                    'probability_failure': prediction.get('probability_failure', 0),
                    'confidence': prediction.get('confidence', 0),
                    'timestamp': datetime.now(),
                    'prediction_data': {
                        'battery_level': prediction.get('battery_level', 0),
                        'temperature': prediction.get('temperature', 0),
                        'efficiency': prediction.get('efficiency', 0),
                        'status': prediction.get('status', 'unknown')
                    },
                    'risk_assessment': {
                        'risk_level': 'high' if prediction.get('probability_failure', 0) > 0.7 else 'medium' if prediction.get('probability_failure', 0) > 0.5 else 'low',
                        'timeframe': '6_hours' if prediction.get('probability_failure', 0) > 0.7 else '24_hours',
                        'failure_reasons': self._get_failure_reasons(
                            prediction.get('battery_level', 0),
                            prediction.get('temperature', 0),
                            prediction.get('efficiency', 0)
                        )
                    }
                }
                
                predictions_collection.insert_one(prediction_doc)
            
            logger.info(f"✅ Stored {len(predictions)} ML predictions in database")
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing ML predictions: {e}")
            return False

def main():
    """Main function to run alert service"""
    print("🚀 UPS Alert Service")
    print("=" * 30)
    
    service = AlertService()
    
    # Update alerts
    if service.update_ups_alerts():
        print("✅ Alerts updated successfully")
        
        # Get summary
        summary = service.get_alerts_summary()
        print(f"\n📊 Alerts Summary:")
        print(f"   • Critical: {summary['critical']}")
        print(f"   • Warning: {summary['warning']}")
        print(f"   • Info: {summary['info']}")
        print(f"   • Total: {summary['total']}")
    else:
        print("❌ Failed to update alerts")

if __name__ == "__main__":
    main()
