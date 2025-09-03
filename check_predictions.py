#!/usr/bin/env python3
"""Check latest predictions in database"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('atlas.env')

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('DB_NAME')]
predictions = db['ups_predictions']

# Get latest prediction
latest = list(predictions.find().sort('timestamp', -1).limit(1))

if latest:
    pred = latest[0]
    print('Latest prediction:')
    print(f'UPS: {pred.get("ups_name")}')
    print(f'Failure Probability: {pred.get("probability_failure"):.1%}')
    print(f'Risk Level: {pred.get("risk_assessment", {}).get("risk_level")}')
    print(f'Failure Reasons: {len(pred.get("risk_assessment", {}).get("failure_reasons", []))}')
    
    if pred.get("risk_assessment", {}).get("failure_reasons"):
        print('\nSample failure reason:')
        print(pred["risk_assessment"]["failure_reasons"][0][:200] + '...')
else:
    print('No predictions found')

client.close()
