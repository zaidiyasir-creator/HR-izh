#!/usr/bin/env python3
"""
Script to populate Malaysia 2026 public holidays into the VANTAGE HR database.
Run once to add all holidays.
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Malaysia 2026 Public Holidays
MALAYSIA_2026_HOLIDAYS = [
    {"title": "New Year's Day", "date": "2026-01-01"},
    {"title": "Thaipusam", "date": "2026-02-01"},
    {"title": "Federal Territory Day", "date": "2026-02-01"},
    {"title": "Chinese New Year", "date": "2026-02-17"},
    {"title": "Chinese New Year (2nd Day)", "date": "2026-02-18"},
    {"title": "Nuzul Al-Quran", "date": "2026-04-17"},
    {"title": "Labour Day", "date": "2026-05-01"},
    {"title": "Wesak Day", "date": "2026-05-12"},
    {"title": "Hari Raya Aidilfitri", "date": "2026-05-17"},
    {"title": "Hari Raya Aidilfitri (2nd Day)", "date": "2026-05-18"},
    {"title": "Yang di-Pertuan Agong's Birthday", "date": "2026-06-01"},
    {"title": "Hari Raya Haji", "date": "2026-07-24"},
    {"title": "Awal Muharram (Islamic New Year)", "date": "2026-08-14"},
    {"title": "Malaysia Day", "date": "2026-09-16"},
    {"title": "Maulidur Rasul (Prophet's Birthday)", "date": "2026-10-23"},
    {"title": "Deepavali", "date": "2026-11-07"},
    {"title": "Christmas Day", "date": "2026-12-25"},
]

async def add_holidays():
    """Add Malaysia 2026 public holidays to the database."""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "vantage_hr")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Check existing holidays to avoid duplicates
    existing = await db.events.find({"event_type": "holiday"}, {"title": 1}).to_list(100)
    existing_titles = {e["title"] for e in existing}
    
    added_count = 0
    skipped_count = 0
    
    for holiday in MALAYSIA_2026_HOLIDAYS:
        if holiday["title"] in existing_titles:
            print(f"⏭️  Skipping (already exists): {holiday['title']}")
            skipped_count += 1
            continue
        
        event = {
            "id": str(uuid.uuid4()),
            "title": holiday["title"],
            "description": f"Malaysia Public Holiday - {holiday['title']}",
            "start_date": holiday["date"],
            "end_date": holiday["date"],
            "event_type": "holiday",
            "created_by": "system",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.events.insert_one(event)
        print(f"✅ Added: {holiday['title']} ({holiday['date']})")
        added_count += 1
    
    print(f"\n🎉 Done! Added {added_count} holidays, skipped {skipped_count} duplicates.")
    client.close()

if __name__ == "__main__":
    asyncio.run(add_holidays())
