// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the UPS monitoring database
db = db.getSiblingDB('UPS_DATA_MONITORING');

// Create collections if they don't exist
db.createCollection('upsdata');
db.createCollection('ups_predictions');
db.createCollection('alerts');

// Create indexes for better performance
db.upsdata.createIndex({ "timestamp": -1 });
db.upsdata.createIndex({ "ups_id": 1 });
db.upsdata.createIndex({ "status": 1 });

db.ups_predictions.createIndex({ "timestamp": -1 });
db.ups_predictions.createIndex({ "ups_id": 1 });
db.ups_predictions.createIndex({ "prediction_date": -1 });

db.alerts.createIndex({ "timestamp": -1 });
db.alerts.createIndex({ "ups_id": 1 });
db.alerts.createIndex({ "alert_type": 1 });

// Create a user for the application (optional, for additional security)
db.createUser({
  user: "ups_app",
  pwd: "ups_app_password",
  roles: [
    { role: "readWrite", db: "UPS_DATA_MONITORING" }
  ]
});

print("MongoDB initialization completed successfully!");
print("Database: UPS_DATA_MONITORING");
print("Collections created: upsdata, ups_predictions, alerts");
print("Indexes created for optimal performance");
