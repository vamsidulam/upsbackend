# 🚀 UPS ML Failure Prediction System

This system provides **real-time UPS failure predictions** using machine learning trained on your `mock_ups_data.csv` file.

## 📁 Files Overview

- **`ml/enhanced_model_trainer.py`** - Core ML model trainer and predictor
- **`real_time_monitor.py`** - Real-time monitoring system
- **`test_model_training.py`** - Test script to verify the system
- **`data/Data/mock_ups_data.csv`** - Training data (1000+ UPS readings)

## 🎯 What This System Does

1. **Trains a RandomForest model** on your mock UPS data
2. **Makes real-time predictions** every 15 minutes
3. **Provides detailed failure reasons** explaining WHY each UPS will fail
4. **Saves predictions** to MongoDB for the frontend to display
5. **Simulates real-time monitoring** for testing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Test the Model Training
```bash
python test_model_training.py
```

This will:
- Load your `mock_ups_data.csv`
- Train the RandomForest model
- Test predictions on sample data
- Run a simulation

### 3. Run Real-Time Monitoring
```bash
# Start real-time monitoring (15-minute intervals)
python real_time_monitor.py

# Or run in simulation mode
python real_time_monitor.py --simulation 10
```

## 🔧 How It Works

### Data Structure
Your `mock_ups_data.csv` contains:
- `power_input` - Input power in watts
- `power_output` - Output power in watts  
- `battery_level` - Battery percentage (0-100)
- `temperature` - Temperature in Celsius
- `load` - Load percentage (0-100+)
- `status` - Target: 0=healthy, 1=will fail

### ML Model
- **Algorithm**: RandomForest Classifier
- **Features**: 5 UPS parameters
- **Output**: Failure prediction (0/1) + probability + detailed reasons
- **Accuracy**: Typically 85-95% on test data

### Prediction Process
1. **Load current UPS data** from MongoDB
2. **Extract features** (power, battery, temp, load)
3. **Make ML prediction** using trained model
4. **Generate detailed failure reasons** based on actual values
5. **Save prediction** to database
6. **Wait 15 minutes** and repeat

## 📊 Example Predictions

### Healthy UPS Example
```
✅ HEALTHY
Failure Probability: 15%
Confidence: 92%
Failure Reasons:
  ✅ System operating within normal parameters. Continue regular monitoring and maintenance.
```

### Failing UPS Example
```
🚨 WILL FAIL
Failure Probability: 87%
Confidence: 89%
Failure Reasons:
  🚨 CRITICAL BATTERY FAILURE IMMINENT: Battery level at 15% indicates severe degradation. 
     The UPS will fail to provide backup power during outages, potentially causing immediate 
     system shutdowns. Battery replacement is critical within 24 hours.
  
  🚨 CRITICAL TEMPERATURE FAILURE IMMINENT: Temperature at 52°C exceeds safe operating limits. 
     This will cause immediate thermal shutdown to prevent component damage.
  
  🚨 CRITICAL LOAD FAILURE IMMINENT: Load at 97% exceeds safe operating capacity. 
     The UPS is operating beyond its design limits and will fail catastrophically.
```

## 🎮 Simulation Mode

Test the system without real data:

```bash
# Run 5 simulations with 1-second delays
python real_time_monitor.py --simulation 5

# Run 20 simulations with 2-second delays  
python real_time_monitor.py --simulation 20
```

## 🔄 Integration with Your System

### Frontend Integration
- Predictions are saved to `ups_predictions` collection
- Frontend reads from `/api/predictions` endpoint
- Real-time updates every 15 minutes

### Backend Integration
- Uses existing MongoDB connection
- Integrates with your current UPS data structure
- Compatible with existing FastAPI endpoints

## 📈 Monitoring Dashboard

The system provides real-time logs:

```
⏰ Monitoring cycle started at 14:30:00
✅ Retrieved 12 UPS systems from database
UPS UPS-001 (Main Server): ✅ HEALTHY
  Failure Probability: 12%
  Confidence: 94%
UPS UPS-002 (Backup Server): 🚨 WILL FAIL
  Failure Probability: 89%
  Confidence: 91%
🚨 CRITICAL: UPS UPS-002 predicted to fail!
  🚨 CRITICAL BATTERY FAILURE IMMINENT: Battery level at 18%...
✅ Monitoring cycle completed. Made 12 predictions.
⏰ Next monitoring cycle in 15 minutes...
```

## 🛠️ Customization

### Modify Failure Thresholds
Edit `ml/enhanced_model_trainer.py`:

```python
# Battery thresholds
if battery_level < 20:  # Critical
if battery_level < 30:  # High risk
if battery_level < 40:  # Moderate risk

# Temperature thresholds  
if temperature > 50:  # Critical
if temperature > 45:  # High risk
if temperature > 40:  # Elevated risk
```

### Change Monitoring Interval
Edit `real_time_monitor.py`:

```python
self.monitoring_interval = 5 * 60  # 5 minutes instead of 15
```

### Add New Features
1. Add new columns to your CSV data
2. Update `feature_names` in the trainer
3. Retrain the model

## 🔍 Troubleshooting

### Common Issues

1. **"Data file not found"**
   - Check `backend/data/Data/mock_ups_data.csv` exists
   - Verify file path in `enhanced_model_trainer.py`

2. **"Model training failed"**
   - Check CSV data format
   - Ensure all required columns exist
   - Verify scikit-learn installation

3. **"MongoDB connection failed"**
   - Start MongoDB service
   - Check connection string
   - Verify database name

### Debug Mode
Enable detailed logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### EnhancedUPSModelTrainer Class

```python
trainer = EnhancedUPSModelTrainer()

# Train model
success = trainer.train_model()

# Load existing model
success = trainer.load_model()

# Make prediction
result = trainer.predict_with_detailed_reasons(ups_data)

# Run simulation
trainer.simulate_real_time_predictions(num_simulations=10, delay_seconds=2)
```

### RealTimeUPSMonitor Class

```python
monitor = RealTimeUPSMonitor()

# Initialize system
success = monitor.initialize()

# Start monitoring
monitor.monitor_ups_systems()

# Run simulation
monitor.run_simulation_mode(num_simulations=5, delay_seconds=1)
```

## 🎯 Next Steps

1. **Test the system**: Run `python test_model_training.py`
2. **Verify predictions**: Check the detailed failure reasons
3. **Start monitoring**: Run `python real_time_monitor.py`
4. **Monitor logs**: Watch for real-time predictions
5. **Check frontend**: Verify predictions appear in `/alerts` page

## 🆘 Support

If you encounter issues:
1. Check the logs in `real_time_monitor.log`
2. Verify your CSV data format
3. Ensure all dependencies are installed
4. Check MongoDB connection

---

**🎉 Your UPS monitoring system now has AI-powered failure predictions with detailed explanations!**
