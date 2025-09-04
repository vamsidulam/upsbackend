import pandas as pd
import numpy as np
from .ml_utils import RandomForestClassifier, train_test_split, accuracy_score, classification_report, confusion_matrix
import pickle
import logging
import os
from datetime import datetime
from pymongo import MongoClient
from .gemini_service import GeminiAIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedUPSModelTrainer:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(os.path.dirname(__file__), 'ups_failure_model.pkl')
        # Mongo config (fallback to env)
        self.mongo_uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("DB_NAME", "UPS_DATA_MONITORING")
        self.history_collection = os.getenv("UPS_HISTORY_COLLECTION", "ups_history")
        # Initialize Gemini AI service for enhanced failure analysis
        self.gemini_service = GeminiAIService()
        # Expanded feature set covering all key UPS fields used across the app
        self.feature_names = [
            'powerInput', 'powerOutput', 'batteryLevel', 'temperature', 'efficiency', 'load',
            'voltageInput', 'voltageOutput', 'frequency', 'capacity', 'criticalLoad', 'uptime',
            'failureRisk'
        ]
        self.target_name = 'status'
        
    def load_and_prepare_data(self):
        """Load and prepare data from MongoDB ups_history for training."""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            coll = db[self.history_collection]
            # Fetch recent history (limit to reasonable size)
            docs = list(coll.find({}, {fn: 1 for fn in self.feature_names + [self.target_name]}).sort('timestamp', -1))
            client.close()
            if not docs:
                logger.error("No history data found in MongoDB for training")
                return None, None
            # Build DataFrame
            df = pd.DataFrame(docs)
            # Map status to classes: healthy=0, warning=1, risky=1, failed=2 (binary/ordinal)
            def map_status(s):
                if isinstance(s, str):
                    s_low = s.lower()
                    if s_low == 'healthy':
                        return 0
                    if s_low in ('warning', 'risky'):
                        return 1
                    if s_low == 'failed':
                        return 2
                return 1
            df[self.target_name] = df.get(self.target_name, 'healthy').apply(map_status)
            # Ensure all feature columns exist and fill defaults
            defaults = {
                'powerInput': 0.0, 'powerOutput': 0.0, 'batteryLevel': 100.0, 'temperature': 25.0,
                'efficiency': 95.0, 'load': 50.0, 'voltageInput': 230.0, 'voltageOutput': 230.0,
                'frequency': 50.0, 'capacity': 2000.0, 'criticalLoad': 500.0, 'uptime': 100.0,
                'failureRisk': 0.0
            }
            for col, default_val in defaults.items():
                if col not in df.columns:
                    df[col] = default_val
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default_val)
            X = df[self.feature_names].values
            y = df[self.target_name].values.astype(int)
            # Log stats
            logger.info(f"Loaded {len(df)} history records for training from MongoDB")
            for i, feature in enumerate(self.feature_names):
                try:
                    logger.info(f"  {feature}: min={np.min(X[:, i])}, max={np.max(X[:, i])}, mean={np.mean(X[:, i]):.2f}")
                except Exception:
                    pass
            return X, y
        except Exception as e:
            logger.error(f"Error loading data from MongoDB: {e}")
            return None, None
    
    def train_model(self):
        """Train the RandomForest model on the mock data"""
        try:
            # Load and prepare data
            X, y = self.load_and_prepare_data()
            if X is None or y is None:
                return False
            
            # Split data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            logger.info(f"Training set size: {len(X_train)}")
            logger.info(f"Testing set size: {len(X_test)}")
            
            # Initialize and train the model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=None,
                random_state=42,
                n_jobs=-1
            )
            
            logger.info("Training RandomForest model...")
            self.model.fit(X_train, y_train)
            
            # Evaluate the model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Model accuracy: {accuracy:.4f}")
            logger.info("Classification Report:")
            logger.info(classification_report(y_test, y_pred))
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': getattr(self.model, 'feature_importances_', np.zeros(len(self.feature_names)))
            }).sort_values('importance', ascending=False)
            
            logger.info("Feature Importance:")
            for _, row in feature_importance.iterrows():
                logger.info(f"  {row['feature']}: {row['importance']:.4f}")
            
            # Save the trained model
            self.save_model()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
    
    def save_model(self):
        """Save the trained model to disk"""
        try:
            if self.model is not None:
                with open(self.model_path, "wb") as f:
                    pickle.dump(self.model, f)
                logger.info(f"Model saved to {self.model_path}")
            else:
                logger.warning("No model to save")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load the trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"Model loaded from {self.model_path}")
                return True
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict_with_detailed_reasons(self, ups_data):
        """Make prediction with detailed failure reasons"""
        try:
            if self.model is None:
                logger.error("Model not loaded. Please train or load the model first.")
                return None
            
            # Extract expanded features in the correct order
            def get_num(d, key, default):
                try:
                    val = d.get(key, default)
                    return float(val)
                except Exception:
                    return default
            features_vec = [
                get_num(ups_data, 'powerInput', 0.0),
                get_num(ups_data, 'powerOutput', 0.0),
                get_num(ups_data, 'batteryLevel', 100.0),
                get_num(ups_data, 'temperature', 25.0),
                get_num(ups_data, 'efficiency', 95.0),
                get_num(ups_data, 'load', 50.0),
                get_num(ups_data, 'voltageInput', 230.0),
                get_num(ups_data, 'voltageOutput', 230.0),
                get_num(ups_data, 'frequency', 50.0),
                get_num(ups_data, 'capacity', 2000.0),
                get_num(ups_data, 'criticalLoad', 500.0),
                get_num(ups_data, 'uptime', 100.0),
                get_num(ups_data, 'failureRisk', 0.0),
            ]
            features = np.array(features_vec).reshape(1, -1)
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0]
            
            # Calculate confidence
            confidence = max(probability)
            
            # Calculate failure probability (inverse of healthy probability)
            failure_probability = probability[1] if len(probability) > 1 else 0.5
            
            # Generate detailed failure reasons using Gemini AI service
            prediction_data = {
                'probability_failure': failure_probability,
                'confidence': confidence,
                'features_used': dict(zip(self.feature_names, features[0]))
            }
            failure_reasons = self.gemini_service.generate_failure_reasons(ups_data, prediction_data)
            
            return {
                'prediction': int(prediction),
                'probability_failure': float(failure_probability),
                'probability_healthy': float(probability[0]) if len(probability) > 1 else 1 - failure_probability,
                'confidence': float(confidence),
                'failure_reasons': failure_reasons,
                'features_used': dict(zip(self.feature_names, features[0]))
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def _analyze_failure_reasons(self, ups_data):
        """Analyze UPS data and generate detailed failure reasons"""
        reasons = []
        
        # Battery analysis
        battery_level = ups_data.get('batteryLevel', 100)
        if battery_level < 20:
            reasons.append(f"🚨 CRITICAL BATTERY FAILURE IMMINENT: Battery level at {battery_level}% indicates severe degradation. The UPS will fail to provide backup power during outages, potentially causing immediate system shutdowns. Battery replacement is critical within 24 hours.")
        elif battery_level < 30:
            reasons.append(f"🚨 HIGH BATTERY FAILURE RISK: Battery level at {battery_level}% shows critical wear. The UPS may fail to sustain load during power interruptions, risking data loss and equipment damage. Schedule emergency battery replacement.")
        elif battery_level < 40:
            reasons.append(f"⚠️ MODERATE BATTERY FAILURE RISK: Battery level at {battery_level}% indicates accelerated aging. The UPS backup time is significantly reduced, increasing failure probability during extended outages. Plan battery replacement within 1 week.")
        elif battery_level < 60:
            reasons.append(f"ℹ️ ELEVATED BATTERY WEAR: Battery level at {battery_level}% shows normal aging but reduced backup capacity. Monitor closely as this accelerates failure risk during high-load conditions.")
        
        # Temperature analysis
        temperature = ups_data.get('temperature', 25)
        if temperature > 50:
            reasons.append(f"🚨 CRITICAL TEMPERATURE FAILURE IMMINENT: Temperature at {temperature}°C exceeds safe operating limits. This will cause immediate thermal shutdown to prevent component damage. The UPS will fail and cannot be restarted until cooled. Check cooling system immediately.")
        elif temperature > 45:
            reasons.append(f"⚠️ HIGH TEMPERATURE FAILURE RISK: Temperature at {temperature}°C is approaching critical limits. Prolonged exposure will damage internal components, capacitors, and reduce battery life. The UPS may fail unexpectedly during high-load operations. Inspect cooling system within 4 hours.")
        elif temperature > 40:
            reasons.append(f"ℹ️ ELEVATED TEMPERATURE RISK: Temperature at {temperature}°C is above optimal range. This accelerates component aging and increases failure probability during peak loads. Monitor cooling efficiency and ensure proper ventilation.")
        
        # Load analysis
        load = ups_data.get('load', 0)
        if load > 95:
            reasons.append(f"🚨 CRITICAL LOAD FAILURE IMMINENT: Load at {load}% exceeds safe operating capacity. The UPS is operating beyond its design limits and will fail catastrophically, potentially causing immediate shutdown and equipment damage. Reduce load immediately or add additional UPS capacity.")
        elif load > 90:
            reasons.append(f"⚠️ HIGH LOAD FAILURE RISK: Load at {load}% is approaching maximum capacity. The UPS is under significant stress, increasing heat generation and component wear. During power outages, the UPS may fail to sustain this load, causing system shutdowns. Consider load balancing or capacity upgrade.")
        elif load > 80:
            reasons.append(f"ℹ️ ELEVATED LOAD MONITORING: Load at {load}% is above optimal range. While not immediately dangerous, this increases UPS stress and reduces backup time. Monitor closely during peak operations as this accelerates component aging.")
        
        # Power balance analysis
        power_input = ups_data.get('powerInput', 0)
        power_output = ups_data.get('powerOutput', 0)
        if power_input > 0 and power_output > 0:
            power_balance = power_input - power_output
            if abs(power_balance) > 50:
                reasons.append(f"🚨 CRITICAL POWER IMBALANCE: Power imbalance of {power_balance}W indicates severe electrical problems. The UPS is not properly regulating power flow, which will cause voltage fluctuations and equipment damage. This requires immediate electrical inspection and repair.")
            elif abs(power_balance) > 20:
                reasons.append(f"⚠️ MODERATE POWER IMBALANCE: Power imbalance of {power_balance}W shows electrical regulation issues. The UPS is not efficiently managing power distribution, increasing failure risk during load changes. Schedule electrical maintenance within 24 hours.")
        
        # If no specific reasons found, add general analysis
        if not reasons:
            reasons.append("✅ System operating within normal parameters. Continue regular monitoring and maintenance.")
        
        return reasons
    
    def simulate_real_time_predictions(self, num_simulations=10, delay_seconds=2):
        """Simulate real-time UPS monitoring with predictions"""
        logger.info(f"Starting real-time prediction simulation ({num_simulations} readings, {delay_seconds}s delay)")
        
        for i in range(num_simulations):
            # Generate random UPS data (simulating real-time readings)
            new_data = {
                'powerInput': np.random.randint(2000, 2500),
                'powerOutput': np.random.randint(1800, 2400),
                'batteryLevel': np.random.randint(40, 100),
                'temperature': np.random.randint(20, 60),
                'load': np.random.randint(20, 110)
            }
            
            # Make prediction
            result = self.predict_with_detailed_reasons(new_data)
            
            if result:
                status = "🚨 WILL FAIL" if result['prediction'] == 1 else "✅ HEALTHY"
                confidence = result['confidence']
                failure_prob = result['probability_failure']
                
                print(f"\n[Reading {i+1}] {status}")
                print(f"Data: Power In={new_data['powerInput']}W, Out={new_data['powerOutput']}W, Battery={new_data['batteryLevel']}%, Temp={new_data['temperature']}°C, Load={new_data['load']}%")
                print(f"ML Prediction: {status} (Confidence: {confidence:.1%}, Failure Probability: {failure_prob:.1%})")
                print("Failure Reasons:")
                for reason in result['failure_reasons']:
                    print(f"  {reason}")
                
                # Wait before next reading
                if i < num_simulations - 1:
                    import time
                    time.sleep(delay_seconds)
            else:
                print(f"[Reading {i+1}] Error: Could not make prediction")
        
        logger.info("Real-time prediction simulation completed")

def main():
    """Main function to demonstrate the enhanced model trainer"""
    trainer = EnhancedUPSModelTrainer()
    
    # Try to load existing model first
    if not trainer.load_model():
        logger.info("No existing model found. Training new model...")
        if trainer.train_model():
            logger.info("Model training completed successfully!")
        else:
            logger.error("Model training failed!")
            return
    
    # Run real-time simulation
    trainer.simulate_real_time_predictions(num_simulations=5, delay_seconds=1)

if __name__ == "__main__":
    main()
