import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
import random
import os
import sys

# Add the parent directory to the path to import ml modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.predictive_monitor import UPSPredictiveMonitor
from scripts.alert_service import AlertService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ups_monitor_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UPSMonitorService:
    def __init__(self):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = "UPS_DATA_MONITORING"
        self.collection_name = "upsdata"
        self.history_collection_name = "ups_history"
        self.monitoring_interval = 1 * 60  # 1 minute
        self.prediction_interval = 15 * 60  # 15 minutes
        self.last_prediction_time = None
        self.predictive_monitor = UPSPredictiveMonitor()
        self.alert_service = AlertService()
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
            # Ensure history indexes exist (idempotent)
            try:
                history_collection = db[self.history_collection_name]
                history_collection.create_index([("upsId", 1), ("timestamp", -1)])
            except Exception as idx_err:
                logger.warning(f"Index creation on ups_history failed or skipped: {idx_err}")
            return collection, client
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return None, None
    
    def create_ups_systems(self):
        """Create 12 UPS systems if they don't exist"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return False
            
            # Check if UPS systems already exist
            existing_count = collection.count_documents({})
            if existing_count >= 12:
                logger.info(f"✅ {existing_count} UPS systems already exist")
                client.close()
                return True
            
            # Create 12 UPS systems
            ups_systems = []
            for i in range(12):
                ups_system = {
                    'name': f'UPS-{i+1:02d}',
                    'location': f'Datacenter-{((i % 3) + 1)}',
                    'capacity': random.randint(1000, 5000),
                    'criticalLoad': random.randint(500, 2500),
                    'status': 'healthy',
                    'batteryLevel': random.randint(80, 100),
                    'temperature': random.randint(20, 35),
                    'efficiency': random.randint(90, 98),
                    'uptime': random.randint(95, 100),
                    'powerInput': random.randint(800, 4500),
                    'powerOutput': random.randint(600, 4000),
                    'lastUpdate': datetime.now(),
                    'performanceHistory': [],
                    'alerts': []  # Initialize empty alerts array
                }
                ups_systems.append(ups_system)
            
            # Insert UPS systems
            result = collection.insert_many(ups_systems)
            logger.info(f"✅ Created {len(result.inserted_ids)} UPS systems")
            
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating UPS systems: {e}")
            return False
    
    def update_ups_data(self):
        """Update UPS data with realistic variations"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return False
            
            # Get all UPS systems
            cursor = collection.find({})
            ups_systems = list(cursor)
            
            if not ups_systems:
                logger.warning("⚠️ No UPS systems found")
                client.close()
                return False
            
            updated_count = 0
            for ups in ups_systems:
                try:
                    # Generate realistic variations
                    current_time = datetime.now()
                    current_status = ups.get('status', 'healthy')
                    
                    # Update battery level (gradual decrease with occasional recharge)
                    current_battery = ups.get('batteryLevel', 100)
                    if current_battery < 20:
                        # Recharge when low (80% chance)
                        if random.random() < 0.8:
                            new_battery = min(100, current_battery + random.randint(5, 15))
                        else:
                            # Continue discharging (20% chance)
                            new_battery = max(0, current_battery - random.uniform(0.1, 0.5))
                    else:
                        # Gradual discharge
                        new_battery = max(0, current_battery - random.uniform(0.1, 0.5))
                    
                    # Update temperature (realistic variations)
                    current_temp = ups.get('temperature', 25)
                    temp_change = random.uniform(-2, 2)
                    new_temp = max(15, min(45, current_temp + temp_change))
                    
                    # Update efficiency (slight variations)
                    current_efficiency = ups.get('efficiency', 95)
                    efficiency_change = random.uniform(-0.5, 0.5)
                    new_efficiency = max(85, min(99, current_efficiency + efficiency_change))
                    
                    # Update power values
                    current_power_input = ups.get('powerInput', 1000)
                    power_input_change = random.uniform(-50, 50)
                    new_power_input = max(100, current_power_input + power_input_change)
                    
                    current_power_output = ups.get('powerOutput', 800)
                    power_output_change = random.uniform(-30, 30)
                    new_power_output = max(50, current_power_output + power_output_change)
                    
                    # Determine status based on conditions (more realistic)
                    new_status = current_status  # Keep current status by default
                    
                    # Only change status if conditions are really bad
                    if new_battery < 10:
                        new_status = 'failed'
                    elif new_battery < 20 and new_temp > 40:
                        new_status = 'warning'
                    elif new_temp > 45:
                        new_status = 'warning'
                    elif new_efficiency < 85:
                        new_status = 'warning'
                    elif new_battery > 30 and new_temp < 40 and new_efficiency > 90:
                        # Recovery conditions
                        if current_status in ['warning', 'failed']:
                            new_status = 'healthy'
                    
                    # Create performance history entry
                    performance_entry = {
                        'timestamp': current_time,
                        'batteryLevel': new_battery,
                        'temperature': new_temp,
                        'efficiency': new_efficiency,
                        'powerInput': new_power_input,
                        'powerOutput': new_power_output,
                        'status': new_status
                    }
                    
                    # Update UPS document
                    update_data = {
                        'batteryLevel': round(new_battery, 2),
                        'temperature': round(new_temp, 2),
                        'efficiency': round(new_efficiency, 2),
                        'powerInput': round(new_power_input, 2),
                        'powerOutput': round(new_power_output, 2),
                        'status': new_status,
                        'lastUpdate': current_time,
                        '$push': {
                            'performanceHistory': {
                                '$each': [performance_entry],
                                '$slice': -96  # Keep last 96 entries (24 hours at 15-min intervals)
                            }
                        }
                    }
                    
                    # Remove the $push operator for the update
                    push_data = update_data.pop('$push')
                    
                    # Update the document
                    collection.update_one(
                        {'_id': ups['_id']},
                        {'$set': update_data}
                    )
                    
                    # Add performance history separately
                    collection.update_one(
                        {'_id': ups['_id']},
                        {'$push': push_data}
                    )
                    
                    # Append a full snapshot to ups_history (separate collection)
                    try:
                        db = client[self.db_name]
                        history_collection = db[self.history_collection_name]
                        history_doc = {
                            'upsId': ups.get('upsId') or ups.get('name'),
                            'upsObjectId': ups.get('_id'),
                            'timestamp': current_time,
                            'batteryLevel': round(new_battery, 2),
                            'temperature': round(new_temp, 2),
                            'efficiency': round(new_efficiency, 2),
                            'powerInput': round(new_power_input, 2),
                            'powerOutput': round(new_power_output, 2),
                            'status': new_status,
                        }
                        history_collection.insert_one(history_doc)
                    except Exception as hist_err:
                        logger.warning(f"Failed to insert history for UPS {ups.get('upsId') or ups.get('name')}: {hist_err}")

                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error updating UPS {ups.get('name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Updated {updated_count} UPS systems")
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating UPS data: {e}")
            return False
    
    def update_alerts(self):
        """Update alerts for all UPS systems"""
        try:
            logger.info("🚨 Updating alerts...")
            if self.alert_service.update_ups_alerts():
                logger.info("✅ Alerts updated successfully")
                return True
            else:
                logger.error("❌ Failed to update alerts")
                return False
        except Exception as e:
            logger.error(f"❌ Error updating alerts: {e}")
            return False
    
    def run_predictions(self):
        """Run predictive monitoring"""
        try:
            if (self.last_prediction_time is None or 
                (datetime.now() - self.last_prediction_time).total_seconds() >= self.prediction_interval):
                
                logger.info("🔮 Running predictive monitoring...")
                
                # Load current UPS data
                ups_data_result = self.predictive_monitor.load_ups_data()
                if ups_data_result is None:
                    logger.warning("⚠️ No UPS data available for predictions")
                    return
                
                ups_data, client = ups_data_result
                
                # Make predictions
                predictions = self.predictive_monitor.make_predictions(ups_data)
                
                if predictions:
                    # Save predictions
                    self.predictive_monitor.save_predictions(predictions)
                    
                    # Generate health report
                    self.predictive_monitor.generate_health_report(ups_data, predictions)
                    
                    self.last_prediction_time = datetime.now()
                    logger.info("✅ Predictive monitoring completed")
                
                # Close MongoDB connection
                if client:
                    client.close()
                    
        except Exception as e:
            logger.error(f"❌ Error running predictions: {e}")
    
    async def run_loop(self):
        """Async run method for FastAPI integration"""
        logger.info("🚀 Starting UPS Monitoring Service as FastAPI background task...")
        
        # Create UPS systems if they don't exist
        if not self.create_ups_systems():
            logger.error("❌ Failed to create UPS systems")
            return
        
        while True:
            try:
                current_time = datetime.now()
                
                # Update UPS data every 1 minute
                logger.info(f"📊 Starting UPS data update cycle at {current_time.strftime('%H:%M:%S')}...")
                if self.update_ups_data():
                    logger.info(f"✅ UPS data update completed at {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Update alerts after data update
                    self.update_alerts()
                else:
                    logger.error(f"❌ UPS data update failed at {datetime.now().strftime('%H:%M:%S')}")
                
                # Run predictions every 15 minutes
                self.run_predictions()
                
                # Wait for next monitoring cycle
                next_update = current_time + timedelta(minutes=1)
                logger.info(f"⏰ Next UPS data update cycle scheduled for {next_update.strftime('%H:%M:%S')} (in {self.monitoring_interval // 60} minutes)...")
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def monitor_ups_systems(self):
        """Main monitoring loop (standalone mode)"""
        logger.info("🚀 Starting UPS Monitoring Service...")
        
        # Create UPS systems if they don't exist
        if not self.create_ups_systems():
            logger.error("❌ Failed to create UPS systems")
            return
        
        while True:
            try:
                current_time = datetime.now()
                
                # Update UPS data every 1 minute
                logger.info(f"📊 Starting UPS data update cycle at {current_time.strftime('%H:%M:%S')}...")
                if self.update_ups_data():
                    logger.info(f"✅ UPS data update completed at {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Update alerts after data update
                    self.update_alerts()
                else:
                    logger.error(f"❌ UPS data update failed at {datetime.now().strftime('%H:%M:%S')}")
                
                # Run predictions every 15 minutes
                self.run_predictions()
                
                # Wait for next monitoring cycle
                next_update = current_time + timedelta(minutes=1)
                logger.info(f"⏰ Next UPS data update cycle scheduled for {next_update.strftime('%H:%M:%S')} (in {self.monitoring_interval // 60} minutes)...")
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def start_service(self):
        """Start the monitoring service"""
        try:
            asyncio.run(self.monitor_ups_systems())
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error in monitoring service: {e}")

def main():
    """Main function to start the monitoring service"""
    service = UPSMonitorService()
    service.start_service()

if __name__ == "__main__":
    main()
