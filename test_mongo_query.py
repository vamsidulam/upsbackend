# #!/usr/bin/env python3
# """
# Test MongoDB query directly to debug the alerts endpoint
# """

# from pymongo import MongoClient
# from datetime import datetime

# def test_mongo_query():
#     """Test the MongoDB query that the alerts endpoint uses"""
#     try:
#         print("🔍 Testing MongoDB Query Directly...")
#         print("=" * 50)
        
#         # Connect to MongoDB
#         client = MongoClient('mongodb://localhost:27017')
#         db = client['UPS_DATA_MONITORING']
#         predictions_collection = db['ups_predictions']
        
#         print(f"📊 Total predictions in collection: {predictions_collection.count_documents({})}")
        
#         # Test the exact query from the alerts endpoint
#         match_conditions = {"probability_failure": {"$gte": 0.4}}
#         print(f"\n🔍 Match conditions: {match_conditions}")
        
#         # Test basic match
#         basic_match = list(predictions_collection.find(match_conditions))
#         print(f"📋 Basic match results: {len(basic_match)} documents")
        
#         if basic_match:
#             print(f"✅ First document probability_failure: {basic_match[0].get('probability_failure')}")
#             print(f"✅ First document risk_assessment: {basic_match[0].get('risk_assessment', {}).get('risk_level')}")
        
#         # Test with severity mapping (critical = high)
#         severity_match = {"probability_failure": {"$gte": 0.4}, "risk_assessment.risk_level": "high"}
#         print(f"\n🔍 Severity match (critical=high): {severity_match}")
        
#         severity_results = list(predictions_collection.find(severity_match))
#         print(f"📋 Severity match results: {len(severity_results)} documents")
        
#         # Test the full pipeline
#         print(f"\n🔍 Testing full aggregation pipeline...")
        
#         pipeline = [
#             {"$match": match_conditions},
#             {"$sort": {"timestamp": -1}},
#             {"$limit": 5}
#         ]
        
#         pipeline_results = list(predictions_collection.aggregate(pipeline))
#         print(f"📋 Pipeline results: {len(pipeline_results)} documents")
        
#         if pipeline_results:
#             print(f"✅ First pipeline result:")
#             print(f"   • ups_id: {pipeline_results[0].get('ups_id')}")
#             print(f"   • ups_name: {pipeline_results[0].get('ups_name')}")
#             print(f"   • probability_failure: {pipeline_results[0].get('probability_failure')}")
#             print(f"   • risk_level: {pipeline_results[0].get('risk_assessment', {}).get('risk_level')}")
#             print(f"   • failure_reasons count: {len(pipeline_results[0].get('risk_assessment', {}).get('failure_reasons', []))}")
        
#     except Exception as e:
#         print(f"❌ Error testing MongoDB query: {e}")
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     test_mongo_query()
