from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio

async def test():
    client = AsyncIOMotorClient("mongodb://root:example@localhost:27017/")
    db = client.webguard_db
    reports = db.reports
    
    report_id = "6aa8b62762f5bfb255c722ba"
    print("Testing report_id:", report_id)
    
    # query 1
    try:
        report1 = await reports.find_one({"_id": ObjectId(report_id)})
        print("Query 1 result:", bool(report1))
    except Exception as e:
        print("Query 1 Exception:", e)
        report1 = None
        
    # query 2
    report2 = await reports.find_one({"scan_id": report_id})
    print("Query 2 result:", bool(report2))

asyncio.run(test())
