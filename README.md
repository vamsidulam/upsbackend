# UPS Monitoring Backend API (FastAPI)

## Setup

1. Create a `.env` file in `backend/` (copy from below):

```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=UPS_DATA_MONITORING
COLLECTION=upsdata
```

2. Install dependencies and run:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API runs at `http://localhost:8000`.

## API Documentation

- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Endpoints

### Health & Status
- `GET /api/health` - Health check

### Dashboard
- `GET /api/dashboard/stats` - Dashboard statistics

### UPS Management
- `GET /api/ups` - List UPS systems (query params: `status`, `location`, `search`, `limit`, `offset`)
- `GET /api/ups/{ups_id}` - Get UPS details
- `GET /api/ups/{ups_id}/events` - Get UPS events (query params: `event_type`, `start_date`, `end_date`, `limit`, `offset`)
- `GET /api/ups/{ups_id}/status` - Get UPS current status
- `GET /api/ups/status/bulk?ids=UPS-DC-001,UPS-DC-002` - Get bulk UPS status

### Alerts
- `GET /api/alerts` - Get alerts (query params: `severity`, `status`, `limit`, `offset`)
- `GET /api/alerts/count` - Get alert counts by status

### Reports
- `GET /api/reports/ups-performance` - Performance report (query params: `start_date`, `end_date`, `ups_ids`)

### Locations
- `GET /api/locations` - Get all unique locations

## Features

- **FastAPI** with automatic API documentation
- **MongoDB** integration with PyMongo
- **CORS** enabled for frontend integration
- **Query parameter validation** with automatic type conversion
- **Error handling** with proper HTTP status codes
- **Logging** for debugging and monitoring
- **Environment variable** configuration


