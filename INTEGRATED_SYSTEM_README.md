# 🚀 UPS Monitoring System - Integrated Background Services

This system now integrates all background services directly into FastAPI, so you only need to run one command to start everything!

## 🎯 What This System Does

- **FastAPI Server**: Main API server on port 10000
- **Continuous Predictions**: ML predictions every 15 minutes using enhanced model trainer
- **UPS Monitoring**: Real-time UPS data updates every 1 minute
- **Gemini AI Integration**: AI-powered failure reason generation
- **MongoDB Integration**: Data storage and retrieval
- **Real-time Alerts**: ML-based failure predictions with detailed analysis

## 🚀 Quick Start

### Option 1: Using the Startup Scripts (Recommended)

#### Windows:
```bash
start_system.bat
```

#### Linux/Mac:
```bash
chmod +x start_system.sh
./start_system.sh
```

#### Python (Any OS):
```bash
python start_with_background_services.py
```

### Option 2: Direct Uvicorn Command

```bash
uvicorn main:app --host 0.0.0.0 --port 10000
```

## 🌐 System Access

Once started, you can access:

- **Main System**: http://localhost:10000
- **API Documentation**: http://localhost:10000/docs
- **Health Check**: http://localhost:10000/api/health
- **System Status**: http://localhost:10000/api/status
- **Alerts**: http://localhost:10000/api/alerts
- **Predictions**: http://localhost:10000/api/predictions
- **Enhanced Predictions**: http://localhost:10000/api/predictions/enhanced

## 📊 Background Services

### 1. Continuous Predictions Service
- **Frequency**: Every 15 minutes
- **Function**: Generates ML predictions using enhanced model trainer
- **Storage**: Saves to `ups_predictions` collection
- **Features**: Detailed failure analysis with Gemini AI integration

### 2. UPS Monitoring Service
- **Frequency**: Every 1 minute
- **Function**: Updates UPS data, generates alerts, runs predictive monitoring
- **Features**: Creates UPS systems if they don't exist, updates performance history

### 3. Gemini AI Service
- **Function**: Generates natural-language failure reasons
- **Integration**: Works with ML predictions to provide detailed analysis
- **API Key**: Configured in `atlas.env` file

## 🔧 Configuration

### Environment Variables (atlas.env)
```env
MONGODB_URI=your_mongodb_connection_string
DB_NAME=UPS_DATA_MONITORING
COLLECTION=upsdata
GEMINI_API_KEY=your_gemini_api_key
```

### Port Configuration
- **Default Port**: 10000
- **Change Port**: Modify `start_with_background_services.py` or use uvicorn directly

## 📈 Monitoring and Logs

### Log Files
- `continuous_predictions.log` - Prediction service logs
- `ups_monitor_service.log` - Monitoring service logs
- `predictive_monitor.log` - ML model logs

### Health Checks
- **API Health**: `/api/health` - Basic system health
- **System Status**: `/api/status` - Detailed service status

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 10000
   netstat -ano | findstr :10000  # Windows
   lsof -i :10000                 # Linux/Mac
   ```

2. **MongoDB Connection Issues**
   - Check your `atlas.env` file
   - Verify MongoDB is running
   - Check network connectivity

3. **Background Services Not Starting**
   - Check logs for errors
   - Verify all dependencies are installed
   - Check MongoDB connection

### Log Analysis
```bash
# Check recent logs
tail -f continuous_predictions.log
tail -f ups_monitor_service.log
```

## 🔄 Service Lifecycle

### Startup Sequence
1. FastAPI server starts
2. MongoDB connection established
3. Background services initialized
4. Services start running in background

### Shutdown
- Press `Ctrl+C` to stop all services
- All background tasks are properly terminated
- MongoDB connections are closed

## 📚 API Endpoints

### Core Endpoints
- `GET /api/health` - System health
- `GET /api/status` - Service status
- `GET /api/alerts` - ML prediction alerts
- `GET /api/predictions` - ML predictions
- `GET /api/predictions/enhanced` - Enhanced predictions with AI

### UPS Management
- `GET /api/ups` - List UPS systems
- `GET /api/ups/{id}` - Get UPS details
- `POST /api/ups` - Create new UPS

## 🎉 Benefits of Integration

1. **Single Command**: Start everything with one command
2. **Automatic Management**: Background services start/stop with the server
3. **Resource Efficiency**: No need for multiple terminal windows
4. **Easier Deployment**: Single service to deploy and monitor
5. **Better Logging**: Centralized logging and monitoring

## 🚀 Next Steps

1. **Start the system** using one of the startup methods
2. **Check the health endpoint** to verify all services are running
3. **Access the API documentation** to explore available endpoints
4. **Monitor the logs** to see background services in action
5. **Test the alerts endpoint** to see ML predictions with detailed failure reasons

## 📞 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify your environment configuration
3. Ensure all dependencies are installed
4. Check MongoDB connectivity

---

**🎯 Goal**: This integrated system provides a complete UPS monitoring solution with AI-powered failure prediction, all running from a single FastAPI instance!
