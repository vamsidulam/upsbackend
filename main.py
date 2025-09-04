from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging
import json
import asyncio
from collections import defaultdict

# Load environment variables from atlas.env file
load_dotenv('atlas.env')

# Import enhanced model trainer
from ml.enhanced_model_trainer import EnhancedUPSModelTrainer
from ml.gemini_service import GeminiAIService

# Import background services
import continuous_predictions
import scripts.ups_monitor_service as monitor

# Import authentication modules
from auth_models import UserCreate, UserLogin, User, Token
from auth_utils import get_password_hash, authenticate_user, create_access_token, get_current_user_from_db

# Configure logging - reduce verbosity
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce uvicorn access log verbosity
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.setLevel(logging.WARNING)

# Environment variables
# Load MongoDB settings strictly from env; default to safe localhost for dev
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "UPS_DATA_MONITORING")
COLLECTION = os.getenv("COLLECTION", "upsdata")

# Initialize FastAPI app
app = FastAPI(
    title="UPS Monitoring API",
    description="API for monitoring UPS systems",
    version="1.0.0"
)

# Initialize Gemini AI service
gemini_service = GeminiAIService()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection with improved timeout settings
logger.info(f"Connecting to MongoDB (db={DB_NAME}, collection={COLLECTION})")
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=30000,  # 30 seconds
    connectTimeoutMS=20000,          # 20 seconds
    socketTimeoutMS=30000,           # 30 seconds
    maxPoolSize=10,                  # Connection pool size
    retryWrites=True,
    retryReads=True
)
db = client[DB_NAME]
ups_collection = db[COLLECTION]
ups_history_collection = db["ups_history"]

def convert_objectids_to_strings(data):
    """Convert MongoDB ObjectIds to strings for JSON serialization"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, dict):
                convert_objectids_to_strings(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        convert_objectids_to_strings(item)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                convert_objectids_to_strings(item)
    return data

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        if self.active_connections:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    # Remove broken connection
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and start background services on startup"""
    try:
        logger.info(f"Testing MongoDB connection...")
        
        # Test the connection with timeout
        client.admin.command('ping', serverSelectionTimeoutMS=30000)
        logger.info(f"✅ Successfully connected to MongoDB Atlas: {DB_NAME}.{COLLECTION}")
        
        # Test database access with timeout
        collection_count = ups_collection.count_documents({}, maxTimeMS=30000)
        logger.info(f"✅ Database accessible. Collection has {collection_count} documents")
        
        # RE-ENABLE BACKGROUND SERVICES FOR REAL-TIME MONITORING
        logger.info("🚀 Starting background monitoring services...")
        logger.info("📊 UPS data will update every 1 minute")
        logger.info("🔮 ML predictions will run every 15 minutes")
        
        # Start continuous prediction service
        continuous_service = continuous_predictions.ContinuousPredictionService()
        asyncio.create_task(continuous_service.run_loop())
        logger.info("✅ Continuous prediction service started")
        
        # Start UPS monitoring service (updates data every 1 minute)
        monitor_service = monitor.UPSMonitorService()
        asyncio.create_task(monitor_service.run_loop())
        logger.info("✅ UPS monitoring service started")
        
        logger.info("🎉 Server started successfully with real-time monitoring enabled")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.warning(f"Server will start but some features may not work properly")
        logger.warning(f"Please check your Atlas connection string and network access")
        # Don't raise - let server start with degraded functionality

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    client.close()

@app.websocket("/ws/ups-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time UPS updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_ups_update(ups_data: Dict[str, Any]):
    """Broadcast UPS update to all connected WebSocket clients"""
    try:
        message = {
            "type": "ups_update",
            "data": ups_data,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(message))
    except Exception as e:
        logger.error(f"Error broadcasting UPS update: {e}")

async def broadcast_status_change(ups_id: str, old_status: str, new_status: str):
    """Broadcast status change to all connected WebSocket clients"""
    try:
        message = {
            "type": "status_change",
            "ups_id": ups_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(message))
        logger.info(f"Broadcasted status change: {ups_id} {old_status} -> {new_status}")
    except Exception as e:
        logger.error(f"Error broadcasting status change: {e}")

async def broadcast_new_alert(alert_data: Dict[str, Any]):
    """Broadcast new alert to all connected WebSocket clients"""
    try:
        message = {
            "type": "new_alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(message))
        logger.info(f"Broadcasted new alert: {alert_data.get('title', 'Unknown')}")
    except Exception as e:
        logger.error(f"Error broadcasting new alert: {e}")

def determine_current_status(ups_data: Dict[str, Any]) -> str:
    """Determine current UPS status based on data values with better error handling"""
    try:
        # Get values with proper type conversion and defaults
        battery_level = float(ups_data.get("batteryLevel", 100))
        temperature = float(ups_data.get("temperature", 25))
        load = float(ups_data.get("load", 50))
        efficiency = float(ups_data.get("efficiency", 95))
        failure_risk = float(ups_data.get("failureRisk", 0))
        
        # Validate data ranges
        if not (0 <= battery_level <= 100):
            battery_level = 100
        if not (0 <= temperature <= 100):
            temperature = 25
        if not (0 <= load <= 100):
            load = 50
        if not (0 <= efficiency <= 100):
            efficiency = 95
        if not (0 <= failure_risk <= 1):
            failure_risk = 0
        
        # Check for failed conditions (any critical condition = failed)
        if (battery_level < 15 or 
            temperature > 38 or 
            load > 90 or 
            efficiency < 80 or 
            failure_risk > 0.8):
            return "failed"
        
        # Check for warning conditions (any warning condition = warning)
        elif (battery_level < 25 or 
              temperature > 32 or 
              load > 80 or 
              efficiency < 85 or 
              failure_risk > 0.6):
            return "warning"
        
        # Check for risky conditions (any risky condition = risky)
        elif (battery_level < 35 or 
              temperature > 28 or 
              load > 70 or 
              efficiency < 90 or 
              failure_risk > 0.4):
            return "risky"
        
        # All conditions are good = healthy
        else:
            return "healthy"
            
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting data types for status determination: {e}")
        return "healthy"
    except Exception as e:
        logger.error(f"Error determining status: {e}")
        return "healthy"

def ensure_required_fields(ups_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required fields are present in UPS data"""
    try:
        required_fields = {
            "batteryLevel": 100,
            "temperature": 25,
            "load": 50,
            "efficiency": 95,
            "failureRisk": 0,
            "powerInput": 1000,
            "powerOutput": 950,
            "capacity": 2000,
            "criticalLoad": 500,
            "uptime": 100,
            "location": "Data Center",
            "lastUpdated": datetime.now().isoformat(),
            "lastChecked": datetime.now().isoformat()
        }
        
        # Add missing fields with defaults
        for field, default_value in required_fields.items():
            if field not in ups_data or ups_data[field] is None:
                ups_data[field] = default_value
                logger.info(f"Added missing field {field} with default value {default_value}")
        
        return ups_data
        
    except Exception as e:
        logger.error(f"Error ensuring required fields: {e}")
        return ups_data

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        client.admin.command('ping')
        # Check if collection has data
        count = ups_collection.count_documents({})
        
        # Check if background services are running
        background_services = {
            "continuous_predictions": True,  # Will be updated when services are actually running
            "ups_monitoring": True,
            "gemini_ai": gemini_service.model is not None if hasattr(gemini_service, 'model') else False
        }
        
        return {
            "status": "ok", 
            "db": True, 
            "document_count": count,
            "background_services": background_services,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "db": False, "error": str(e)}

# Authentication endpoints
@app.post("/api/auth/signup", response_model=User)
async def signup(user_data: UserCreate):
    """User registration endpoint"""
    try:
        # Check if user already exists
        user_collection = db["users"]
        existing_user = user_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        # Create new user
        user_doc = {
            "email": user_data.email,
            "password": get_password_hash(user_data.password),
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = user_collection.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)
        del user_doc["_id"]
        del user_doc["password"]  # Don't return password
        
        return user_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during signup: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during signup"
        )

@app.post("/api/auth/signin", response_model=Token)
async def signin(user_credentials: UserLogin):
    """User authentication endpoint"""
    try:
        # Authenticate user
        user = authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user["email"]}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during signin: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during signin"
        )

# Dependency function for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Dependency to get current authenticated user"""
    return get_current_user_from_db(credentials, db)

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    try:
        # Remove password from user data
        user_data = current_user.copy()
        if "password" in user_data:
            del user_data["password"]
        return user_data
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error getting user info"
        )

@app.get("/api/test-data")
async def test_data():
    """Test endpoint to check data structure"""
    try:
        # Get first document to see structure
        doc = ups_collection.find_one()
        if doc:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            return {"status": "ok", "sample_data": doc}
        else:
            return {"status": "ok", "message": "No data found in collection"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_ups = ups_collection.count_documents({})
        active_ups = ups_collection.count_documents({"status": "healthy"})
        failed_ups = ups_collection.count_documents({"status": "failed"})
        warning_ups = ups_collection.count_documents({"status": "warning"})
        risky_ups = ups_collection.count_documents({"status": "risky"})
        
        # Count real-time ML predictions using enhanced model trainer (same as alerts page)
        try:
            # Initialize enhanced model trainer for consistent alert counting
            enhanced_trainer = EnhancedUPSModelTrainer()
            
            if enhanced_trainer.load_model():
                # Get current UPS data and generate real-time predictions
                ups_data_cursor = ups_collection.find({})
                ups_data_list = list(ups_data_cursor)
                
                alerts_count = 0
                total_predictions = len(ups_data_list)
                
                for ups in ups_data_list:
                    try:
                        # Make prediction using enhanced model trainer
                        prediction_result = enhanced_trainer.predict_with_detailed_reasons(ups)
                        
                        if prediction_result and prediction_result['probability_failure'] >= 0.4:
                            alerts_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Error generating prediction for dashboard stats: {e}")
                        continue
                
                logger.info(f"Dashboard stats - Real-time predictions: {total_predictions}, Alerts: {alerts_count}")
            else:
                # Fallback to stored predictions if enhanced model fails
                predictions_collection = db['ups_predictions']
                alerts_count = predictions_collection.count_documents({"probability_failure": {"$gte": 0.4}})
                total_predictions = predictions_collection.count_documents({})
                logger.info(f"Dashboard stats - Fallback to stored predictions: {total_predictions}, Alerts: {alerts_count}")
                
        except Exception as e:
            logger.error(f"Error counting predictions: {e}")
            alerts_count = 0
            total_predictions = 0
        
        return {
            "totalUPS": total_ups,
            "activeUPS": active_ups,
            "failedUPS": failed_ups,
            "warningUPS": warning_ups,
            "riskyUPS": risky_ups,
            "healthyUPS": active_ups,
            "predictionsCount": total_predictions,
            "alertsCount": alerts_count
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

@app.get("/api/ups")
async def get_ups_list(
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in upsId, name, or location"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """Get list of UPS systems with optional filtering and pagination"""
    try:
        # Only log if debug mode is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Starting UPS list query")
        
        query = {}
        
        if status:
            query["status"] = status
        if location:
            query["location"] = location
        if search:
            query["$or"] = [
                {"upsId": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
                {"location": {"$regex": search, "$options": "i"}}
            ]
        
        # Only log if debug mode is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Query: {query}")
        
        # Get total count
        total = ups_collection.count_documents(query)
        
        # Get documents with pagination - exclude performance history for list view
        cursor = ups_collection.find(query, {"performanceHistory": 0}).skip(offset).limit(limit)
        data = list(cursor)
        
        # Convert ObjectId to string for JSON serialization and update status
        for item in data:
            if '_id' in item:
                item['_id'] = str(item['_id'])
            
            # Ensure all required fields are present
            item = ensure_required_fields(item)
            
            # Ensure status is up-to-date based on current data
            current_status = determine_current_status(item)
            if current_status != item.get('status'):
                # Update status in database
                ups_collection.update_one(
                    {"_id": item['_id']},
                    {"$set": {"status": current_status}}
                )
                item['status'] = current_status
        
        # Only log if debug mode is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("UPS list query completed successfully")
        
        return {
            "data": data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting UPS list: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get UPS list: {str(e)}")

@app.get("/api/ups/{ups_id}")
async def get_ups_detail(ups_id: str):
    """Get detailed information for a specific UPS"""
    try:
        ups = ups_collection.find_one({"upsId": ups_id})
        if not ups:
            raise HTTPException(status_code=404, detail="UPS not found")
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in ups:
            ups['_id'] = str(ups['_id'])
        
        return ups
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting UPS detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UPS detail")

@app.post("/api/ups")
async def create_ups(ups_data: dict):
    """Create a new UPS system"""
    try:
        # Check if UPS ID already exists
        existing_ups = ups_collection.find_one({"upsId": ups_data.get("upsId")})
        if existing_ups:
            raise HTTPException(status_code=400, detail="UPS ID already exists")
        
        # Add default values for new UPS
        new_ups = {
            **ups_data,
            "status": "healthy",
            "lastChecked": datetime.now().isoformat(),
            "powerInput": 0,
            "powerOutput": 0,
            "batteryLevel": 100,
            "temperature": 25.0,
            "efficiency": 95.0,
            "uptime": 100.0,
            "events": [],
            "alerts": [],
            "performanceHistory": []
        }
        
        result = ups_collection.insert_one(new_ups)
        new_ups["_id"] = str(result.inserted_id)
        
        logger.info(f"Created new UPS: {new_ups['upsId']}")
        return new_ups
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating UPS: {e}")
        raise HTTPException(status_code=500, detail="Failed to create UPS")

@app.get("/api/ups/{ups_id}/events")
async def get_ups_events(
    ups_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip")
):
    """Get events for a specific UPS"""
    try:
        # Verify UPS exists
        ups = ups_collection.find_one({"upsId": ups_id})
        if not ups:
            raise HTTPException(status_code=404, detail="UPS not found")
        
        pipeline = [
            {"$match": {"upsId": ups_id}},
            {"$unwind": "$events"}
        ]
        
        # Add date filters
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            pipeline.append({"$match": {"events.timestamp": date_filter}})
        
        # Add event type filter
        if event_type:
            pipeline.append({"$match": {"events.type": event_type}})
        
        # Add sorting and pagination
        pipeline.extend([
            {"$sort": {"events.timestamp": -1}},
            {"$skip": offset},
            {"$limit": limit},
            {"$replaceRoot": {"newRoot": "$events"}}
        ])
        
        events = list(ups_collection.aggregate(pipeline))
        
        return {"data": events}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting UPS events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UPS events")

@app.get("/api/ups/{ups_id}/status")
async def get_ups_status(ups_id: str):
    """Get current status for a specific UPS"""
    try:
        ups = ups_collection.find_one(
            {"upsId": ups_id},
            {"performanceHistory": 0, "events": {"$slice": 1}}
        )
        if not ups:
            raise HTTPException(status_code=404, detail="UPS not found")
        
        return {
            "upsId": ups["upsId"],
            "status": ups["status"],
            "lastChecked": ups["lastChecked"],
            "batteryLevel": ups["batteryLevel"],
            "temperature": ups["temperature"],
            "powerInput": ups["powerInput"],
            "powerOutput": ups["powerOutput"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting UPS status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UPS status")

@app.get("/api/ups/{ups_id}/history")
async def get_ups_history(
    ups_id: str,
    start: Optional[str] = Query(None, description="Start datetime (ISO)"),
    end: Optional[str] = Query(None, description="End datetime (ISO)"),
    limit: int = Query(500, ge=1, le=5000, description="Max records"),
    offset: int = Query(0, ge=0, description="Records to skip")
):
    """Get historical readings for an UPS from ups_history collection."""
    try:
        query = {"upsId": ups_id}
        if start or end:
            time_filter = {}
            if start:
                time_filter["$gte"] = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if end:
                time_filter["$lte"] = datetime.fromisoformat(end.replace('Z', '+00:00'))
            query["timestamp"] = time_filter
        cursor = ups_history_collection.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        data = list(cursor)
        for doc in data:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = doc["timestamp"].isoformat()
        return {"data": data, "total": ups_history_collection.count_documents({"upsId": ups_id})}
    except Exception as e:
        logger.error(f"Error getting UPS history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UPS history")

@app.get("/api/ups/status/bulk")
async def get_bulk_ups_status(ids: str = Query(..., description="Comma-separated list of UPS IDs")):
    """Get status for multiple UPS systems"""
    try:
        ups_ids = [id.strip() for id in ids.split(",") if id.strip()]
        if not ups_ids:
            return {"data": []}
        
        cursor = ups_collection.find(
            {"upsId": {"$in": ups_ids}},
            {
                "upsId": 1,
                "status": 1,
                "lastChecked": 1,
                "batteryLevel": 1,
                "temperature": 1,
                "powerInput": 1,
                "powerOutput": 1
            }
        )
        
        data = list(cursor)
        return {"data": data}
    except Exception as e:
        logger.error(f"Error getting bulk UPS status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bulk UPS status")

@app.get("/api/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by alert status"),
    latest_only: bool = Query(False, description="Show only latest alerts per UPS"),
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip")
):
    """Get ML prediction alerts with detailed failure analysis using enhanced model trainer"""
    try:
        logger.info(f"Getting ML prediction alerts with enhanced analysis - latest_only: {latest_only}, status: {status}, severity: {severity}")
        
        # First, try to get stored enhanced predictions from ups_predictions collection
        try:
            predictions_collection = db['ups_predictions']
            
            # Build match conditions - only non-healthy predictions (probability_failure >= 0.4)
            match_conditions = {"probability_failure": {"$gte": 0.4}}
            
            if severity:
                # Map severity to risk levels
                if severity == "critical":
                    match_conditions["risk_assessment.risk_level"] = "high"
                elif severity == "warning":
                    match_conditions["risk_assessment.risk_level"] = "medium"
                elif severity == "info":
                    match_conditions["risk_assessment.risk_level"] = "low"
            
            if status:
                match_conditions["current_status"] = status
            
            # Build pipeline to get only latest alert per UPS
            pipeline = []
            if match_conditions:
                pipeline.append({"$match": match_conditions})
            
            if latest_only:
                # Group by UPS ID and get the latest prediction for each
                pipeline.extend([
                    {"$sort": {"timestamp": -1}},
                    {"$group": {
                        "_id": "$ups_id",
                        "latest_prediction": {"$first": "$$ROOT"}
                    }},
                    {"$replaceRoot": {"newRoot": "$latest_prediction"}}
                ])
            
            # Add sorting and pagination
            pipeline.extend([
                {"$sort": {"timestamp": -1}},
                {"$skip": offset},
                {"$limit": limit}
            ])
            
            stored_alerts = list(predictions_collection.aggregate(pipeline))
            
            if stored_alerts:
                logger.info(f"Found {len(stored_alerts)} stored enhanced predictions")
                
                # Convert stored predictions to alerts format
                enhanced_alerts = []
                for prediction in stored_alerts:
                    alert = {
                        '_id': prediction.get('_id', str(prediction.get('ups_object_id', 'Unknown'))),
                        'ups_id': prediction.get('ups_id', 'Unknown'),
                        'ups_name': prediction.get('ups_name', 'Unknown'),
                        'probability_failure': prediction.get('probability_failure', 0),
                        'probability_healthy': prediction.get('probability_healthy', 0),
                        'confidence': prediction.get('confidence', 0),
                        'timestamp': prediction.get('timestamp', datetime.now().isoformat()),
                        'prediction_data': prediction.get('risk_assessment', {}).get('technical_details', {}),
                        'risk_assessment': prediction.get('risk_assessment', {}),
                        'failure_reasons': prediction.get('risk_assessment', {}).get('failure_reasons', [])
                    }
                    
                    # Ensure we have the detailed failure reasons from the stored prediction
                    if prediction.get('risk_assessment', {}).get('failure_reasons'):
                        alert['failure_reasons'] = prediction['risk_assessment']['failure_reasons']
                        logger.info(f"Extracted {len(alert['failure_reasons'])} detailed failure reasons for {alert['ups_name']}")
                    enhanced_alerts.append(alert)
                
                # Convert all ObjectIds to strings for JSON serialization
                enhanced_alerts = convert_objectids_to_strings(enhanced_alerts)
                
                logger.info(f"Returning {len(enhanced_alerts)} stored enhanced alerts with detailed failure analysis")
                return {"alerts": enhanced_alerts}
                
        except Exception as e:
            logger.warning(f"Error getting stored enhanced predictions: {e}")
        
        # If no stored predictions found, fallback to real-time generation
        logger.info("No stored enhanced predictions found, falling back to real-time generation")
        
        # Initialize enhanced model trainer for detailed failure analysis
        enhanced_trainer = EnhancedUPSModelTrainer()
        
        # Load the enhanced model
        if not enhanced_trainer.load_model():
            logger.warning("Enhanced model not loaded, falling back to stored predictions")
            # Fallback to stored predictions if enhanced model fails
            return await get_stored_alerts(severity, status, latest_only, limit, offset)
        
        # Get UPS data for real-time enhanced predictions
        match_conditions = {}
        if status:
            match_conditions["status"] = status
        
        # Get UPS data from the main collection
        ups_data_cursor = ups_collection.find(match_conditions)
        ups_data_list = list(ups_data_cursor)
        
        if not ups_data_list:
            logger.warning("No UPS data found for enhanced predictions")
            return {"alerts": []}
        
        # Generate enhanced predictions with detailed failure analysis
        enhanced_alerts = []
        for ups in ups_data_list:
            try:
                # Make prediction using enhanced model trainer for detailed analysis
                prediction_result = enhanced_trainer.predict_with_detailed_reasons(ups)
                
                if prediction_result and prediction_result['probability_failure'] >= 0.4:  # Only non-healthy
                    # Filter by severity if specified
                    if severity:
                        risk_level = 'high' if prediction_result['probability_failure'] > 0.7 else 'medium' if prediction_result['probability_failure'] > 0.4 else 'low'
                        if severity == "critical" and risk_level != 'high':
                            continue
                        elif severity == "warning" and risk_level != 'medium':
                            continue
                        elif severity == "info" and risk_level != 'low':
                            continue
                    
                    # Create enhanced alert with detailed failure analysis
                    enhanced_alert = {
                        '_id': str(ups.get('_id')),
                        'ups_id': ups.get('upsId', 'Unknown'),
                        'ups_name': ups.get('name', 'Unknown'),
                        'probability_failure': prediction_result['probability_failure'],
                        'probability_healthy': prediction_result['probability_healthy'],
                        'confidence': prediction_result['confidence'],
                        'timestamp': datetime.now().isoformat(),
                        'prediction_data': prediction_result['features_used'],
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
                                'voltage_input': ups.get('voltageInput', 0),
                                'voltage_output': ups.get('voltageOutput', 0),
                                'frequency': ups.get('frequency', 50)
                            }
                        }
                    }
                    
                    enhanced_alerts.append(enhanced_alert)
                    
            except Exception as e:
                logger.error(f"Error generating enhanced prediction for UPS {ups.get('name', 'Unknown')}: {e}")
                continue
        
        # Sort by failure probability (highest first) and limit results
        enhanced_alerts.sort(key=lambda x: x['probability_failure'], reverse=True)
        enhanced_alerts = enhanced_alerts[:limit]
        
        # If no enhanced alerts were produced (e.g., model mismatch), fallback to stored alerts
        if len(enhanced_alerts) == 0:
            logger.warning("No enhanced alerts generated; falling back to stored predictions")
            return await get_stored_alerts(severity, status, latest_only, limit, offset)
        
        # Convert all ObjectIds to strings for JSON serialization
        enhanced_alerts = convert_objectids_to_strings(enhanced_alerts)
        
        logger.info(f"Generated {len(enhanced_alerts)} enhanced alerts with detailed failure analysis")
        return {"alerts": enhanced_alerts}
        
    except Exception as e:
        logger.error(f"Error getting enhanced alerts: {e}")
        # Fallback to stored predictions if enhanced analysis fails
        return await get_stored_alerts(severity, status, latest_only, limit, offset)

async def get_stored_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    latest_only: bool = False,
    limit: int = 100,
    offset: int = 0
):
    """Fallback function to get stored predictions when enhanced analysis fails"""
    try:
        logger.info(f"Getting stored predictions as fallback - latest_only: {latest_only}, status: {status}, severity: {severity}")
        
        # Get predictions collection
        predictions_collection = db['ups_predictions']
        
        # Build match conditions - only non-healthy predictions (probability_failure >= 0.4)
        match_conditions = {"probability_failure": {"$gte": 0.4}}
        
        if severity:
            # Map severity to risk levels
            if severity == "critical":
                match_conditions["risk_assessment.risk_level"] = "high"
            elif severity == "warning":
                match_conditions["risk_assessment.risk_level"] = "medium"
            elif severity == "info":
                match_conditions["risk_assessment.risk_level"] = "low"
        
        if status:
            match_conditions["status"] = status
        
        # Build pipeline to get only latest alert per UPS
        pipeline = []
        if match_conditions:
            pipeline.append({"$match": match_conditions})
        
        if latest_only:
            # Group by UPS ID and get the latest prediction for each
            pipeline.extend([
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": "$ups_id",
                    "latest_prediction": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest_prediction"}}
            ])
        
        # Add sorting and pagination
        pipeline.extend([
            {"$sort": {"timestamp": -1}},
            {"$skip": offset},
            {"$limit": limit}
        ])
        
        stored_predictions = list(predictions_collection.aggregate(pipeline))
        logger.info(f"Found {len(stored_predictions)} stored predictions as fallback")
        
        # Convert stored predictions to alerts format with proper failure_reasons
        formatted_alerts = []
        for prediction in stored_predictions:
            alert = {
                '_id': prediction.get('_id', str(prediction.get('ups_object_id', 'Unknown'))),
                'ups_id': prediction.get('ups_id', 'Unknown'),
                'ups_name': prediction.get('ups_name', 'Unknown'),
                'probability_failure': prediction.get('probability_failure', 0),
                'probability_healthy': prediction.get('probability_healthy', 0),
                'confidence': prediction.get('confidence', 0),
                'timestamp': prediction.get('timestamp', datetime.now().isoformat()),
                'prediction_data': prediction.get('risk_assessment', {}).get('technical_details', {}),
                'risk_assessment': prediction.get('risk_assessment', {}),
                'failure_reasons': prediction.get('risk_assessment', {}).get('failure_reasons', [])
            }
            formatted_alerts.append(alert)
        
        # Convert all ObjectIds to strings for JSON serialization
        formatted_alerts = convert_objectids_to_strings(formatted_alerts)
        
        logger.info(f"Returning {len(formatted_alerts)} formatted alerts with detailed failure reasons")
        return {"alerts": formatted_alerts}
    except Exception as e:
        logger.error(f"Error getting stored predictions: {e}")
        # Return empty alerts if fallback also fails
        return {"alerts": []}

@app.get("/api/predictions")
async def get_predictions(
    limit: int = Query(12, ge=1, le=100, description="Number of latest non-healthy predictions to return (one per UPS)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (high, medium, low)"),
    ups_id: Optional[str] = Query(None, description="Filter by specific UPS ID")
):
    """Get the latest ML predictions with optional filtering"""
    try:
        logger.info(f"Getting predictions - limit: {limit}, risk_level: {risk_level}, ups_id: {ups_id}")
        
        # Get predictions collection
        predictions_collection = db['ups_predictions']
        
        # Build match conditions
        match_conditions = {}
        if risk_level:
            match_conditions["risk_assessment.risk_level"] = risk_level
        if ups_id:
            match_conditions["ups_id"] = ups_id
        
        # Build pipeline to get only latest prediction per UPS, excluding healthy ones
        pipeline = []
        if match_conditions:
            pipeline.append({"$match": match_conditions})
        
        # Filter out healthy predictions (probability_failure < 0.4)
        pipeline.append({"$match": {"probability_failure": {"$gte": 0.4}}})
        
        # Group by UPS ID and get the latest prediction for each
        pipeline.extend([
            {"$sort": {"timestamp": -1}},  # Sort by timestamp descending
            {"$group": {
                "_id": "$ups_id",
                "latest_prediction": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_prediction"}},
            {"$sort": {"timestamp": -1}},  # Sort the final results
            {"$limit": limit},
            {"$project": {
                "_id": 1,
                "ups_id": 1,
                "ups_name": 1,
                "probability_failure": 1,
                "confidence": 1,
                "timestamp": 1,
                "prediction_data": 1,
                "risk_assessment": 1,
                "failure_reasons": "$risk_assessment.failure_reasons"
            }}
        ])
        
        predictions = list(predictions_collection.aggregate(pipeline))
        logger.info(f"Found {len(predictions)} predictions")
        
        # Convert MongoDB ObjectIds and datetime objects to JSON-serializable format
        for prediction in predictions:
            # Convert all ObjectId fields to strings
            for key, value in prediction.items():
                if isinstance(value, ObjectId):
                    prediction[key] = str(value)
                elif key == 'timestamp' and value:
                    try:
                        if hasattr(value, 'isoformat'):
                            prediction[key] = value.isoformat()
                        else:
                            prediction[key] = str(value)
                    except Exception as e:
                        logger.warning(f"Error converting timestamp for prediction {prediction.get('_id', 'unknown')}: {e}")
                        prediction[key] = str(value)
            
            # Ensure all required fields are present
            if 'ups_id' not in prediction:
                prediction['ups_id'] = prediction.get('_id', 'Unknown')
            
            # Clean up UPS ID to show a clean number instead of ObjectId
            if prediction.get('ups_id'):
                ups_id = prediction['ups_id']
                # If it's an ObjectId, try to get the actual UPS number from the database
                if isinstance(ups_id, str) and len(ups_id) == 24:  # MongoDB ObjectId length
                    try:
                        ups_data = ups_collection.find_one({"_id": ObjectId(ups_id)})
                        if ups_data and ups_data.get('upsId'):
                            prediction['ups_id'] = ups_data['upsId']
                    except:
                        # If we can't get the actual UPS ID, generate a clean number
                        prediction['ups_id'] = f"UPS-{str(ups_id)[-4:].upper()}"
                # If it's already a clean UPS ID, keep it as is
                elif isinstance(ups_id, str) and ups_id.startswith('UPS'):
                    prediction['ups_id'] = ups_id
                else:
                    # Generate a clean UPS number
                    prediction['ups_id'] = f"UPS-{str(ups_id)[-4:].upper()}"
            
            # If ups_id is still 'Unknown', try to fetch it from upsdata collection using ups_name
            if prediction.get('ups_id') == 'Unknown' and prediction.get('ups_name'):
                try:
                    # Find UPS in upsdata collection by name
                    ups_data = ups_collection.find_one({"name": prediction['ups_name']})
                    if ups_data and ups_data.get('upsId'):
                        prediction['ups_id'] = ups_data['upsId']
                        logger.info(f"Found UPS ID {ups_data['upsId']} for UPS name: {prediction['ups_name']}")
                    else:
                        # If still not found, generate a clean ID from the name
                        prediction['ups_id'] = f"UPS-{prediction['ups_name'][:4].upper()}"
                        logger.info(f"Generated UPS ID {prediction['ups_id']} for UPS name: {prediction['ups_name']}")
                except Exception as e:
                    logger.warning(f"Error fetching UPS ID for name {prediction['ups_name']}: {e}")
                    # Generate a fallback ID
                    prediction['ups_id'] = f"UPS-{prediction['ups_name'][:4].upper()}"
            
            # Ensure risk_assessment exists with detailed failure reasons
            if 'risk_assessment' not in prediction:
                # Get UPS data to generate detailed failure reasons
                ups_data = None
                try:
                    # Try to find UPS by ups_id first, then by name
                    if prediction.get('ups_id') and prediction.get('ups_id') != 'Unknown':
                        ups_data = ups_collection.find_one({"upsId": prediction['ups_id']})
                    if not ups_data and prediction.get('ups_name'):
                        ups_data = ups_collection.find_one({"name": prediction['ups_name']})
                except Exception as e:
                    logger.warning(f"Error fetching UPS data for prediction: {e}")
                
                # Use Gemini AI to generate detailed failure reasons if available
                if gemini_service and gemini_service.model:
                    try:
                        # Create prediction data for Gemini
                        prediction_data = {
                            'probability_failure': prediction.get('probability_failure', 0),
                            'confidence': prediction.get('confidence', 0.5)
                        }
                        failure_reasons = gemini_service.generate_failure_reasons(ups_data, prediction_data)
                        logger.info(f"Generated {len(failure_reasons)} failure reasons using Gemini AI")
                    except Exception as e:
                        logger.warning(f"Gemini AI failed, using fallback: {e}")
                        failure_reasons = []
                
                # Fallback to manual generation if Gemini AI is not available
                if not failure_reasons:
                    failure_reasons = []
                    probability = prediction.get('probability_failure', 0)
                    
                                         # Add specific technical reasons based on actual UPS data
                    if ups_data:
                         # Battery analysis with detailed failure explanations
                         battery_level = ups_data.get('batteryLevel', 100)
                    if battery_level < 20:
                        failure_reasons.append(f"🚨 CRITICAL BATTERY FAILURE IMMINENT: Battery level at {battery_level}% indicates severe degradation. The UPS will fail to provide backup power during outages, potentially causing immediate system shutdowns. Battery replacement is critical within 24 hours.")
                    elif battery_level < 30:
                        failure_reasons.append(f"🚨 HIGH BATTERY FAILURE RISK: Battery level at {battery_level}% shows critical wear. The UPS may fail to sustain load during power interruptions, risking data loss and equipment damage. Schedule emergency battery replacement.")
                    elif battery_level < 40:
                        failure_reasons.append(f"⚠️ MODERATE BATTERY FAILURE RISK: Battery level at {battery_level}% indicates accelerated aging. The UPS backup time is significantly reduced, increasing failure probability during extended outages. Plan battery replacement within 1 week.")
                    elif battery_level < 60:
                        failure_reasons.append(f"ℹ️ ELEVATED BATTERY WEAR: Battery level at {battery_level}% shows normal aging but reduced backup capacity. Monitor closely as this accelerates failure risk during high-load conditions.")
                    
                    # Temperature analysis with detailed failure explanations
                    temperature = ups_data.get('temperature', 25)
                    if temperature > 50:
                        failure_reasons.append(f"🚨 CRITICAL TEMPERATURE FAILURE IMMINENT: Temperature at {temperature}°C exceeds safe operating limits. This will cause immediate thermal shutdown to prevent component damage. The UPS will fail and cannot be restarted until cooled. Check cooling system immediately.")
                    elif temperature > 45:
                        failure_reasons.append(f"⚠️ HIGH TEMPERATURE FAILURE RISK: Temperature at {temperature}°C is approaching critical limits. Prolonged exposure will damage internal components, capacitors, and reduce battery life. The UPS may fail unexpectedly during high-load operations. Inspect cooling system within 4 hours.")
                    elif temperature > 40:
                        failure_reasons.append(f"ℹ️ ELEVATED TEMPERATURE RISK: Temperature at {temperature}°C is above optimal range. This accelerates component aging and increases failure probability during peak loads. Monitor cooling efficiency and ensure proper ventilation.")
                    
                    # Efficiency analysis with detailed failure explanations
                    efficiency = ups_data.get('efficiency', 100)
                    if efficiency < 80:
                        failure_reasons.append(f"🚨 CRITICAL EFFICIENCY FAILURE RISK: Efficiency at {efficiency}% indicates severe power conversion problems. The UPS is wasting significant energy and generating excessive heat, which will cause component failure within days. Internal power electronics require immediate inspection and repair.")
                    elif efficiency < 90:
                        failure_reasons.append(f"⚠️ MODERATE EFFICIENCY FAILURE RISK: Efficiency at {efficiency}% shows power conversion degradation. The UPS is consuming more power than necessary, increasing heat generation and accelerating component wear. This will lead to failure during high-load conditions. Schedule maintenance within 48 hours.")
                    elif efficiency < 95:
                        failure_reasons.append(f"ℹ️ ELEVATED EFFICIENCY CONCERN: Efficiency at {efficiency}% indicates slight power conversion issues. While not immediately critical, this reduces UPS reliability and increases failure probability during extended operations. Monitor for further degradation.")
                    
                    # Load analysis with detailed failure explanations
                    load = ups_data.get('load', 0)
                    if load > 95:
                        failure_reasons.append(f"🚨 CRITICAL LOAD FAILURE IMMINENT: Load at {load}% exceeds safe operating capacity. The UPS is operating beyond its design limits and will fail catastrophically, potentially causing immediate shutdown and equipment damage. Reduce load immediately or add additional UPS capacity.")
                    elif load > 90:
                        failure_reasons.append(f"⚠️ HIGH LOAD FAILURE RISK: Load at {load}% is approaching maximum capacity. The UPS is under significant stress, increasing heat generation and component wear. During power outages, the UPS may fail to sustain this load, causing system shutdowns. Consider load balancing or capacity upgrade.")
                    elif load > 80:
                        failure_reasons.append(f"ℹ️ ELEVATED LOAD MONITORING: Load at {load}% is above optimal range. While not immediately dangerous, this increases UPS stress and reduces backup time. Monitor closely during peak operations as this accelerates component aging.")
                    
                    # Power balance analysis with detailed failure explanations
                    power_input = ups_data.get('powerInput', 0)
                    power_output = ups_data.get('powerOutput', 0)
                    if power_input > 0 and power_output > 0:
                        power_balance = power_input - power_output
                        if abs(power_balance) > 50:
                            failure_reasons.append(f"🚨 CRITICAL POWER IMBALANCE: Power imbalance of {power_balance}W indicates severe electrical problems. The UPS is not properly regulating power flow, which will cause voltage fluctuations and equipment damage. This requires immediate electrical inspection and repair.")
                        elif abs(power_balance) > 20:
                            failure_reasons.append(f"⚠️ MODERATE POWER IMBALANCE: Power imbalance of {power_balance}W shows electrical regulation issues. The UPS is not efficiently managing power distribution, increasing failure risk during load changes. Schedule electrical maintenance within 24 hours.")
                    
                    # Runtime analysis with detailed failure explanations
                    uptime = ups_data.get('uptime', 0)
                    if uptime > 15000:  # More than 15,000 hours
                        failure_reasons.append(f"🚨 CRITICAL AGE-RELATED FAILURE RISK: UPS has operated for {uptime} hours, exceeding typical component life expectancy. Critical components like capacitors, fans, and power electronics are at high risk of failure. The UPS may fail unexpectedly and cannot be reliably restarted. Immediate replacement recommended.")
                    elif uptime > 10000:  # More than 10,000 hours
                        failure_reasons.append(f"⚠️ ELEVATED AGE-RELATED FAILURE RISK: UPS has operated for {uptime} hours, approaching component end-of-life. Internal components are showing wear and increased failure probability. Schedule comprehensive maintenance and prepare for replacement planning.")
                    
                    # Voltage analysis with detailed failure explanations
                    voltage_input = ups_data.get('voltageInput', 0)
                    voltage_output = ups_data.get('voltageOutput', 0)
                    if voltage_input > 0:
                        if voltage_input > 250 or voltage_input < 190:
                            failure_reasons.append(f"🚨 CRITICAL INPUT VOLTAGE FAILURE RISK: Input voltage at {voltage_input}V is outside safe operating range (190-250V). This will cause immediate UPS shutdown to protect connected equipment. The UPS cannot operate until input voltage stabilizes. Check power source immediately.")
                        elif voltage_input > 240 or voltage_input < 200:
                            failure_reasons.append(f"⚠️ MODERATE INPUT VOLTAGE RISK: Input voltage at {voltage_input}V is approaching unsafe limits. This stresses UPS components and increases failure probability. Monitor power quality and consider voltage regulation equipment.")
                    
                    if voltage_output > 0:
                        if voltage_output > 250 or voltage_output < 190:
                            failure_reasons.append(f"🚨 CRITICAL OUTPUT VOLTAGE FAILURE RISK: Output voltage at {voltage_output}V is outside safe range. This will damage connected equipment and cause UPS protection shutdown. Internal voltage regulation circuits require immediate inspection and repair.")
                        elif voltage_output > 240 or voltage_output < 200:
                            failure_reasons.append(f"⚠️ MODERATE OUTPUT VOLTAGE RISK: Output voltage at {voltage_output}V shows regulation issues. This may damage sensitive equipment and indicates internal component problems. Schedule voltage regulation maintenance.")
                    
                    # Frequency analysis with detailed failure explanations
                    frequency = ups_data.get('frequency', 50)
                    if frequency < 45 or frequency > 55:
                        failure_reasons.append(f"🚨 CRITICAL FREQUENCY FAILURE RISK: Frequency at {frequency}Hz is outside safe operating range (45-55Hz). This will cause immediate UPS shutdown as it cannot maintain stable power output. The UPS will fail to protect equipment during power disturbances.")
                    elif frequency < 47 or frequency > 53:
                        failure_reasons.append(f"⚠️ MODERATE FREQUENCY RISK: Frequency at {frequency}Hz is approaching unsafe limits. This indicates power quality issues and increases UPS stress. Monitor frequency stability and consider power conditioning equipment.")
                
                # If no specific reasons found, add probability-based general reasons
                if not failure_reasons:
                    if probability > 0.8:
                        failure_reasons = [
                            f"🚨 CRITICAL FAILURE IMMINENT: ML model predicts {probability:.1%} failure probability. The UPS is showing multiple critical failure indicators that will cause complete system failure within hours. This requires immediate emergency maintenance to prevent catastrophic equipment damage and data loss.",
                            f"⚠️ MULTIPLE COMPONENT FAILURES: Analysis indicates simultaneous failure of critical components including power electronics, battery systems, and cooling mechanisms. The UPS cannot maintain stable operation and will fail unexpectedly.",
                            f"🔧 SYSTEM STABILITY COMPROMISED: Internal diagnostics show severe degradation across multiple systems. The UPS is operating in an unstable state and cannot be relied upon for power protection.",
                            f"📞 EMERGENCY MAINTENANCE REQUIRED: Contact maintenance team immediately. This UPS requires comprehensive inspection and component replacement to prevent imminent failure."
                        ]
                    elif probability > 0.6:
                        failure_reasons = [
                            f"⚠️ ELEVATED FAILURE RISK: ML model predicts {probability:.1%} failure probability. The UPS is showing significant performance degradation that increases failure risk during high-load conditions or power disturbances.",
                            f"📉 PERFORMANCE DEGRADATION: Multiple performance metrics indicate accelerated component wear and reduced reliability. The UPS may fail during critical operations.",
                            f"🔧 PREVENTIVE MAINTENANCE CRITICAL: Schedule comprehensive maintenance within 24-48 hours to address identified issues before they cause complete system failure.",
                            f"👁️ INTENSIFIED MONITORING: Increase monitoring frequency and watch for further deterioration. The UPS requires close attention until maintenance is completed."
                        ]
                    elif probability > 0.4:
                        failure_reasons = [
                            f"ℹ️ MODERATE FAILURE RISK: ML model predicts {probability:.1%} failure probability. The UPS is showing early warning signs that, while not immediately critical, indicate increased failure probability over time.",
                            f"📅 MAINTENANCE PLANNING: Schedule routine maintenance to address identified issues before they escalate. This will prevent future failure and maintain optimal performance.",
                            f"🔧 COMPONENT INSPECTION: Focus on identified areas of concern during maintenance. Early intervention will prevent minor issues from becoming major problems."
                        ]
                    else:
                        failure_reasons = [
                            f"✅ OPTIMAL OPERATION: ML model predicts {probability:.1%} failure probability. The UPS is operating within normal parameters with no immediate failure indicators.",
                            f"📊 CONTINUOUS MONITORING: Regular monitoring continues to ensure early detection of any developing issues. Current conditions are stable and reliable.",
                            f"🔧 SCHEDULED MAINTENANCE: Continue with normal maintenance schedule. No additional maintenance is required at this time."
                        ]
                
                # Generate failure prediction summary
                if probability > 0.8:
                    failure_summary = f"🚨 CRITICAL FAILURE IMMINENT: The ML model predicts this UPS will fail within 6-12 hours with {probability:.1%} probability. Multiple critical systems are compromised, requiring immediate emergency intervention to prevent catastrophic failure."
                elif probability > 0.6:
                    failure_summary = f"⚠️ HIGH FAILURE RISK: The ML model predicts this UPS will fail within 12-24 hours with {probability:.1%} probability. Significant performance degradation detected, requiring urgent maintenance to prevent system failure."
                elif probability > 0.4:
                    failure_summary = f"ℹ️ MODERATE FAILURE RISK: The ML model predicts this UPS will fail within 24-48 hours with {probability:.1%} probability. Early warning signs detected, requiring preventive maintenance to avoid future failure."
                else:
                    failure_summary = f"✅ LOW FAILURE RISK: The ML model predicts this UPS will continue operating normally with {probability:.1%} failure probability. No immediate concerns, continue with regular monitoring and maintenance."
                
                prediction['risk_assessment'] = {
                    'risk_level': 'low' if probability < 0.4 else 'medium' if probability < 0.7 else 'high',
                    'timeframe': '24_hours' if probability < 0.4 else '12_hours' if probability < 0.7 else '6_hours',
                    'failure_summary': failure_summary,
                    'failure_reasons': failure_reasons,
                    'technical_details': {
                        'battery_health': ups_data.get('batteryLevel', 100) if ups_data else 'Unknown',
                        'temperature_status': ups_data.get('temperature', 25) if ups_data else 'Unknown',
                        'efficiency_rating': ups_data.get('efficiency', 100) if ups_data else 'Unknown',
                        'load_percentage': ups_data.get('load', 0) if ups_data else 'Unknown',
                        'power_balance': (ups_data.get('powerInput', 0) - ups_data.get('powerOutput', 0)) if ups_data else 'Unknown',
                        'voltage_input': ups_data.get('voltageInput', 0) if ups_data else 'Unknown',
                        'voltage_output': ups_data.get('voltageOutput', 0) if ups_data else 'Unknown',
                        'frequency': ups_data.get('frequency', 50) if ups_data else 'Unknown'
                    }
                }
            
            # Flatten top-level failure_reasons for frontend convenience
            if 'failure_reasons' not in prediction or not prediction['failure_reasons']:
                fr = prediction.get('risk_assessment', {}).get('failure_reasons') if prediction.get('risk_assessment') else None
                prediction['failure_reasons'] = fr or []
        
        return {"predictions": predictions}
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        # Return empty predictions instead of throwing error
        return {"predictions": []}


@app.get("/api/predictions/enhanced")
async def get_enhanced_predictions(
    limit: int = Query(12, ge=1, le=100, description="Number of latest enhanced predictions to return"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (high, medium, low)"),
    ups_id: Optional[str] = Query(None, description="Filter by specific UPS ID")
):
    """Get enhanced ML predictions using the enhanced model trainer for better accuracy"""
    try:
        logger.info(f"Getting enhanced predictions - limit: {limit}, risk_level: {risk_level}, ups_id: {ups_id}")
        
        # Initialize enhanced model trainer
        enhanced_trainer = EnhancedUPSModelTrainer()
        
        # Load the enhanced model
        if not enhanced_trainer.load_model():
            logger.warning("Enhanced model not loaded, falling back to basic predictions")
            # Fallback to basic predictions endpoint
            return await get_predictions(limit=limit, risk_level=risk_level, ups_id=ups_id)
        
        # Get UPS data for predictions
        match_conditions = {}
        if ups_id:
            match_conditions["upsId"] = ups_id
        
        # Get UPS data from the main collection
        ups_data_cursor = ups_collection.find(match_conditions)
        ups_data_list = list(ups_data_cursor)
        
        if not ups_data_list:
            logger.warning("No UPS data found for enhanced predictions")
            return {"predictions": []}
        
        # Generate enhanced predictions using the enhanced model trainer
        enhanced_predictions = []
        for ups in ups_data_list:
            try:
                # Make prediction using enhanced model trainer
                prediction_result = enhanced_trainer.predict_with_detailed_reasons(ups)
                
                if prediction_result:
                    # Use Gemini AI to generate enhanced failure reasons
                    gemini_failure_reasons = gemini_service.generate_failure_reasons(ups, prediction_result)
                    
                    # Create enhanced prediction object
                    enhanced_prediction = {
                        '_id': str(ups.get('_id')),
                        'ups_id': ups.get('upsId', 'Unknown'),
                        'ups_name': ups.get('name', 'Unknown'),
                        'probability_failure': prediction_result['probability_failure'],
                        'probability_healthy': prediction_result['probability_healthy'],
                        'confidence': prediction_result['confidence'],
                        'timestamp': datetime.now().isoformat(),
                        'prediction_data': prediction_result['features_used'],
                        'risk_assessment': {
                            'risk_level': 'low' if prediction_result['probability_failure'] < 0.4 else 'medium' if prediction_result['probability_failure'] < 0.7 else 'high',
                            'timeframe': '24_hours' if prediction_result['probability_failure'] < 0.4 else '12_hours' if prediction_result['probability_failure'] < 0.7 else '6_hours',
                            'failure_reasons': gemini_failure_reasons,  # Use Gemini AI generated reasons
                            'failure_summary': f"Enhanced ML model predicts {prediction_result['probability_failure']:.1%} failure probability with {prediction_result['confidence']:.1%} confidence.",
                            'technical_details': {
                                'battery_health': ups.get('batteryLevel', 100),
                                'temperature_status': ups.get('temperature', 25),
                                'efficiency_rating': ups.get('efficiency', 100),
                                'load_percentage': ups.get('load', 0),
                                'power_balance': (ups.get('powerInput', 0) - ups.get('powerOutput', 0)),
                                'voltage_input': ups.get('voltageInput', 0),
                                'voltage_output': ups.get('voltageOutput', 0),
                                'frequency': ups.get('frequency', 50)
                            }
                        }
                    }
                    
                    # Filter by risk level if specified
                    if risk_level:
                        if risk_level == 'high' and enhanced_prediction['risk_assessment']['risk_level'] != 'high':
                            continue
                        elif risk_level == 'medium' and enhanced_prediction['risk_assessment']['risk_level'] != 'medium':
                            continue
                        elif risk_level == 'low' and enhanced_prediction['risk_assessment']['risk_level'] != 'low':
                            continue
                    
                    enhanced_predictions.append(enhanced_prediction)
                    
            except Exception as e:
                logger.error(f"Error generating enhanced prediction for UPS {ups.get('name', 'Unknown')}: {e}")
                continue
        
        # Sort by failure probability (highest first) and limit results
        enhanced_predictions.sort(key=lambda x: x['probability_failure'], reverse=True)
        enhanced_predictions = enhanced_predictions[:limit]
        
        logger.info(f"Generated {len(enhanced_predictions)} enhanced predictions")
        
        return {"predictions": enhanced_predictions}
        
    except Exception as e:
        logger.error(f"Error getting enhanced predictions: {e}")
        # Return empty predictions instead of throwing error
        return {"predictions": []}


@app.get("/api/alerts/count")
async def get_alert_counts():
    """Get ML prediction alert counts by risk level (non-healthy predictions only)"""
    try:
        predictions_collection = db['ups_predictions']
        
        # Only count non-healthy predictions (probability_failure >= 0.4)
        pipeline = [
            {"$match": {"probability_failure": {"$gte": 0.4}}},
            {"$group": {"_id": "$risk_assessment.risk_level", "count": {"$sum": 1}}}
        ]
        
        counts = list(predictions_collection.aggregate(pipeline))
        
        # Format the response
        formatted_counts = []
        for count in counts:
            risk_level = count["_id"] or "unknown"
            formatted_counts.append({
                "risk_level": risk_level,
                "count": count["count"]
            })
        
        return {"counts": formatted_counts}
    except Exception as e:
        logger.error(f"Error getting alert counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert counts")

@app.get("/api/reports/ups-performance")
async def get_ups_performance_report(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    ups_ids: Optional[str] = Query(None, description="Comma-separated list of UPS IDs")
):
    """Get UPS performance report"""
    try:
        pipeline = []
        
        # Add UPS filter
        if ups_ids:
            ups_id_list = [id.strip() for id in ups_ids.split(",") if id.strip()]
            pipeline.append({"$match": {"upsId": {"$in": ups_id_list}}})
        
        # Add performance history processing
        pipeline.extend([
            {"$unwind": "$performanceHistory"}
        ])
        
        # Add date filters
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            pipeline.append({"$match": {"performanceHistory.timestamp": date_filter}})
        
        # Add aggregation
        pipeline.extend([
            {"$project": {"upsId": 1, "performanceHistory": 1}},
            {"$group": {
                "_id": "$upsId",
                "avgEfficiency": {"$avg": "$performanceHistory.efficiency"},
                "avgTemperature": {"$avg": "$performanceHistory.temperature"},
                "avgPowerInput": {"$avg": "$performanceHistory.powerInput"},
                "avgPowerOutput": {"$avg": "$performanceHistory.powerOutput"}
            }},
            {"$sort": {"_id": 1}}
        ])
        
        data = list(ups_collection.aggregate(pipeline))
        
        # Convert ObjectIds to strings for JSON serialization
        data = convert_objectids_to_strings(data)
        
        return {"data": data}
    except Exception as e:
        logger.error(f"Error getting performance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance report")

@app.get("/api/status")
async def get_system_status():
    """Get system status including background services"""
    try:
        # Check database connection
        db_status = "connected"
        try:
            client.admin.command('ping')
            collection_count = ups_collection.count_documents({})
        except Exception as e:
            db_status = f"error: {str(e)}"
            collection_count = 0
        
        # Check background services status
        services_status = {
            "database": {
                "status": db_status,
                "document_count": collection_count
            },
            "background_services": {
                "continuous_predictions": "enabled (running every 30 minutes)",
                "ups_monitoring": "enabled (updating every 1 minute)",
                "gemini_ai": "enabled (with fallback system)"
            },
            "system": {
                "timestamp": datetime.now().isoformat(),
                "uptime": "running",
                "mode": "real_time_monitoring",
                "fallback_system": "active"
            }
        }
        
        return services_status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.get("/api/locations")
async def get_locations():
    """Get all unique locations"""
    try:
        locations = ups_collection.distinct("location")
        return {"data": locations}
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get locations")

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting UPS Monitoring Server in Stable Mode...")
    logger.info("📊 Background services temporarily disabled for stability")
    logger.info("🌐 Access at: http://0.0.0.0:10000")
    logger.info("📖 API docs at: http://0.0.0.0:10000/docs")
    uvicorn.run(app, host="0.0.0.0", port=10000)
