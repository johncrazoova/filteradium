"""
Filteradium - TSETMC Data Collector
Main entry point for data collection and scheduling
"""
import asyncio
import sys
from datetime import datetime
from loguru import logger

from models.database import init_db
from services.data_fetcher import DataFetcher
from services.scheduler import UpdateScheduler


# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("data/filteradium.log", rotation="10 MB", retention="7 days")


async def cmd_full():
    """Full update command"""
    init_db()
    fetcher = DataFetcher()
    try:
        result = await fetcher.full_update()
        print(f"\n✅ Full update completed:")
        print(f"   Stocks: {result['stocks']}")
        print(f"   Details: {result['details']}")
        print(f"   Duration: {result['duration']:.1f}s")
    finally:
        fetcher.close()


async def cmd_daily():
    """Daily update command"""
    init_db()
    fetcher = DataFetcher()
    try:
        result = await fetcher.daily_update()
        print(f"\n✅ Daily update completed:")
        print(f"   Stocks: {result['stocks']}")
        print(f"   Duration: {result['duration']:.1f}s")
    finally:
        fetcher.close()


async def cmd_stock(ins_code: int):
    """Fetch single stock"""
    init_db()
    fetcher = DataFetcher()
    try:
        success = await fetcher.fetch_stock_details(ins_code)
        if success:
            print(f"\n✅ Stock {ins_code} updated")
        else:
            print(f"\n❌ Failed to update stock {ins_code}")
    finally:
        fetcher.close()


async def cmd_scheduler():
    """Run scheduler"""
    init_db()
    scheduler = UpdateScheduler()
    scheduler.start()
    
    print("\n📅 Scheduler started!")
    print("   Daily update: 6:00 PM")
    print("   Full update: Saturday 2:00 AM")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("\n👋 Scheduler stopped")


def cmd_stats():
    """Show database stats"""
    init_db()
    from models.database import SessionLocal, Stock, PriceHistory, UpdateLog
    
    db = SessionLocal()
    try:
        stocks = db.query(Stock).count()
        prices = db.query(PriceHistory).count()
        updates = db.query(UpdateLog).count()
        
        last_update = db.query(UpdateLog).order_by(UpdateLog.id.desc()).first()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Stocks: {stocks}")
        print(f"   Price records: {prices}")
        print(f"   Updates: {updates}")
        if last_update:
            print(f"   Last update: {last_update.timestamp} ({last_update.update_type})")
    finally:
        db.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════╗
║         FILTERADIUM Data Collector          ║
╠══════════════════════════════════════════════╣
║ Commands:                                    ║
║   full     - Full update (all data)          ║
║   daily    - Daily update (prices only)      ║
║   stock N  - Fetch stock by insCode          ║
║   run      - Run scheduler (6 PM daily)      ║
║   stats    - Show database statistics        ║
╚══════════════════════════════════════════════╝
        """)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "full":
        asyncio.run(cmd_full())
    elif cmd == "daily":
        asyncio.run(cmd_daily())
    elif cmd == "stock" and len(sys.argv) > 2:
        asyncio.run(cmd_stock(int(sys.argv[2])))
    elif cmd == "run":
        asyncio.run(cmd_scheduler())
    elif cmd == "stats":
        cmd_stats()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
