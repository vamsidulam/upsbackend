import pandas as pd
import numpy as np
from pymongo import MongoClient
from .ml_utils import RandomForestClassifier, StandardScaler, train_test_split, classification_report, confusion_matrix
import joblib
import logging
from datetime import datetime, timedelta
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UPSModelTrainer:
    def __init__(self):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.mongo_uri = os.getenv("MONGODB_URI")
        self.db_name = "UPS_DATA_MONITORING"
        self.collection_name = "upsdata"
        
        # Use absolute paths for model files
        ml_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(ml_dir, "model.pkl")
        self.scaler_path = os.path.join(ml_dir, "scaler.pkl")
        
        self.model = None
        self.scaler = None
        
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
    
    def load_data_from_mongodb(self):
        """Load UPS data from MongoDB"""
        try:
            collection, client = self.connect_to_mongodb()
            if collection is None:
                return None
            
            # Get all UPS data
            cursor = collection.find({})
            data = list(cursor)
            
            if not data:
                logger.warning("⚠️ No data found in MongoDB")
                return None
            
            logger.info(f"✅ Loaded {len(data)} UPS records from MongoDB")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error loading data from MongoDB: {e}")
            return None
    
    def prepare_training_data(self, data):
        """Prepare training data from UPS records"""
        try:
            features = []
            targets = []
            
            for ups_record in data:
                # Extract basic features
                power_input = ups_record.get('powerInput', 0)
                power_output = ups_record.get('powerOutput', 0)
                battery_level = ups_record.get('batteryLevel', 100)
                temperature = ups_record.get('temperature', 25)
                efficiency = ups_record.get('efficiency', 95)
                uptime = ups_record.get('uptime', 100)
                capacity = ups_record.get('capacity', 1000)
                critical_load = ups_record.get('criticalLoad', 500)
                
                # Calculate derived features
                load_percentage = (power_output / capacity) * 100 if capacity > 0 else 0
                power_ratio = power_output / power_input if power_input > 0 else 0
                battery_health = battery_level / 100
                
                # Extract performance history features if available
                performance_features = self.extract_performance_features(ups_record)
                
                # Combine all features
                feature_vector = [
                    power_input,
                    power_output,
                    battery_level,
                    temperature,
                    efficiency,
                    uptime,
                    load_percentage,
                    power_ratio,
                    battery_health,
                    capacity,
                    critical_load
                ] + performance_features
                
                features.append(feature_vector)
                
                # Determine target (1 for failed/warning, 0 for healthy)
                status = ups_record.get('status', 'healthy')
                if status in ['failed', 'warning']:
                    targets.append(1)
                else:
                    targets.append(0)
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            logger.error(f"❌ Error preparing training data: {e}")
            return None, None
    
    def extract_performance_features(self, ups_record):
        """Extract features from performance history"""
        try:
            performance_history = ups_record.get('performanceHistory', [])
            
            if not performance_history:
                # Return default values if no history
                return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 10 default features
            
            # Get recent data (last 24 hours = 96 records for 15-min intervals)
            recent_data = performance_history[-96:] if len(performance_history) >= 96 else performance_history
            
            if len(recent_data) < 12:  # Need at least 3 hours of data
                return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            
            # Extract values
            power_input_values = [d.get('powerInput', 0) for d in recent_data]
            power_output_values = [d.get('powerOutput', 0) for d in recent_data]
            battery_values = [d.get('batteryLevel', 100) for d in recent_data]
            temp_values = [d.get('temperature', 25) for d in recent_data]
            efficiency_values = [d.get('efficiency', 95) for d in recent_data]
            
            # Calculate statistical features
            features = [
                np.mean(power_input_values),
                np.std(power_input_values),
                np.mean(battery_values),
                np.std(battery_values),
                np.min(battery_values),
                np.mean(temp_values),
                np.std(temp_values),
                np.max(temp_values),
                np.mean(efficiency_values),
                np.std(efficiency_values)
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error extracting performance features: {e}")
            return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    def train_model(self, X, y):
        """Train the Random Forest model"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            
            logger.info("📊 Model Training Results:")
            logger.info(f"Training samples: {len(X_train)}")
            logger.info(f"Test samples: {len(X_test)}")
            logger.info(f"Feature count: {X.shape[1]}")
            
            # Print classification report
            report = classification_report(y_test, y_pred, target_names=['Healthy', 'Failed/Warning'])
            logger.info(f"\nClassification Report:\n{report}")
            
            # Print confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            logger.info(f"\nConfusion Matrix:\n{cm}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training model: {e}")
            return False
    
    def save_model(self):
        """Save the trained model and scaler"""
        try:
            if self.model and self.scaler:
                joblib.dump(self.model, self.model_path)
                joblib.dump(self.scaler, self.scaler_path)
                logger.info(f"✅ Model saved to {self.model_path}")
                logger.info(f"✅ Scaler saved to {self.scaler_path}")
                return True
            else:
                logger.error("❌ No model or scaler to save")
                return False
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")
            return False
    
    def load_model(self):
        """Load the trained model and scaler"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("✅ Model and scaler loaded successfully")
                return True
            else:
                logger.warning("⚠️ Model files not found")
                return False
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def predict_ups_status(self, ups_data):
        """Predict UPS status using the trained model"""
        try:
            if not self.model or not self.scaler:
                logger.error("❌ Model not loaded")
                return None
            
            # Prepare features for prediction
            features = self.prepare_training_data([ups_data])
            if features is None:
                return None
            
            X, _ = features
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            probability = self.model.predict_proba(X_scaled)[0]
            
            return {
                'prediction': int(prediction),
                'probability_failure': float(probability[1]),
                'probability_healthy': float(probability[0]),
                'confidence': float(max(probability))
            }
            
        except Exception as e:
            logger.error(f"❌ Error making prediction: {e}")
            return None
    
    def run_training_pipeline(self):
        """Run the complete training pipeline"""
        logger.info("🚀 Starting UPS Model Training Pipeline...")
        
        # Load data
        data = self.load_data_from_mongodb()
        if not data:
            logger.error("❌ Failed to load data")
            return False
        
        # Prepare training data
        X, y = self.prepare_training_data(data)
        if X is None or y is None:
            logger.error("❌ Failed to prepare training data")
            return False
        
        # Train model
        if not self.train_model(X, y):
            logger.error("❌ Failed to train model")
            return False

        # Save model
        if not self.save_model():
            logger.error("❌ Failed to save model")
            return False
        
        logger.info("🎉 Model training pipeline completed successfully!")
        return True

def main():
    """Main function to run the training pipeline"""
    trainer = UPSModelTrainer()
    success = trainer.run_training_pipeline()
    
    if success:
        logger.info("✅ Model training completed successfully!")
        logger.info("📁 Model files created:")
        logger.info(f"   - {trainer.model_path}")
        logger.info(f"   - {trainer.scaler_path}")
    else:
        logger.error("❌ Model training failed!")

if __name__ == "__main__":
    main()
