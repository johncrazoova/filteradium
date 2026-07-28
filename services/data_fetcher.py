"""
Data Fetcher - Fetch all TSETMC data and store in database
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger

from core.tsetmc_client import TSETMCClient
from models.database import (
    SessionLocal, Stock, PriceHistory, ShareholderSnapshot,
    ClientTypeHistory, OrderBookSnapshot, MarketOverview, UpdateLog,
    init_db
)


class DataFetcher:
    """Fetch and store all TSETMC data"""
    
    def __init__(self, proxy: Optional[str] = None):
        self.client = TSETMCClient(proxy=proxy)
        self.db = SessionLocal()
    
    def close(self):
        self.db.close()
    
    # ========== Parse Helpers ==========
    
    def _parse_stock(self, raw: Dict) -> Dict:
        """Parse stock data from API response"""
        return {
            "ins_code": raw.get("insCode"),
            "symbol": raw.get("lVal18AFC", ""),
            "name": raw.get("lVal18", ""),
            "close": raw.get("pClosing", 0),
            "last": raw.get("pDrCotVal", 0),
            "first": raw.get("priceFirst", 0),
            "yesterday": raw.get("priceYesterday", 0),
            "high": raw.get("priceMax", 0),
            "low": raw.get("priceMin", 0),
            "volume": raw.get("qTotTran5J", 0),
            "value": raw.get("qTotCap", 0),
            "upper_limit": raw.get("pMax", 0),
            "lower_limit": raw.get("pMin", 0),
            "sector": raw.get("cSecVal", ""),
        }
    
    def _parse_price_history(self, raw: Dict) -> List[Dict]:
        """Parse price history"""
        history = []
        if "closingPriceHistory" in raw:
            for item in raw["closingPriceHistory"]:
                history.append({
                    "date": datetime.strptime(str(item.get("dEven", "")), "%Y%m%d") if item.get("dEven") else None,
                    "open": item.get("priceFirst", 0),
                    "high": item.get("priceMax", 0),
                    "low": item.get("priceMin", 0),
                    "close": item.get("pClosing", 0),
                    "last": item.get("pDrCotVal", 0),
                    "volume": item.get("qTotTran5J", 0),
                    "value": item.get("qTotCap", 0),
                    "change": item.get("priceChange", 0),
                })
        return history
    
    def _parse_client_type(self, raw: Dict) -> Dict:
        """Parse client type data"""
        return {
            "individual_buy_count": raw.get("buy_I_Count", 0),
            "individual_sell_count": raw.get("sell_I_Count", 0),
            "individual_buy_volume": raw.get("buy_I_Volume", 0),
            "individual_sell_volume": raw.get("sell_I_Volume", 0),
            "corporate_buy_count": raw.get("buy_N_Count", 0),
            "corporate_sell_count": raw.get("sell_N_Count", 0),
            "corporate_buy_volume": raw.get("buy_N_Volume", 0),
            "corporate_sell_volume": raw.get("sell_N_Volume", 0),
        }
    
    # ========== Fetch Methods ==========
    
    async def fetch_all_stocks(self) -> int:
        """Fetch all stocks and store in database"""
        logger.info("Fetching all stocks...")
        
        data = await self.client.get_market_watch()
        if not data or "closingPriceAll" not in data:
            logger.error("Failed to fetch market data")
            return 0
        
        stocks = data["closingPriceAll"]
        count = 0
        
        for raw in stocks:
            try:
                parsed = self._parse_stock(raw)
                if not parsed["ins_code"]:
                    continue
                
                # Upsert stock
                stock = self.db.query(Stock).filter(Stock.ins_code == parsed["ins_code"]).first()
                if stock:
                    stock.symbol = parsed["symbol"]
                    stock.name = parsed["name"]
                    stock.close_price = parsed["close"]
                    stock.last_price = parsed["last"]
                    stock.first_price = parsed["first"]
                    stock.yesterday_price = parsed["yesterday"]
                    stock.high_price = parsed["high"]
                    stock.low_price = parsed["low"]
                    stock.volume = parsed["volume"]
                    stock.value = parsed["value"]
                    stock.upper_limit = parsed["upper_limit"]
                    stock.lower_limit = parsed["lower_limit"]
                    stock.sector = parsed["sector"]
                    stock.updated_at = datetime.utcnow()
                else:
                    stock = Stock(
                        ins_code=parsed["ins_code"],
                        symbol=parsed["symbol"],
                        name=parsed["name"],
                        close_price=parsed["close"],
                        last_price=parsed["last"],
                        first_price=parsed["first"],
                        yesterday_price=parsed["yesterday"],
                        high_price=parsed["high"],
                        low_price=parsed["low"],
                        volume=parsed["volume"],
                        value=parsed["value"],
                        upper_limit=parsed["upper_limit"],
                        lower_limit=parsed["lower_limit"],
                        sector=parsed["sector"],
                    )
                    self.db.add(stock)
                
                count += 1
                
            except Exception as e:
                logger.error(f"Error parsing stock: {e}")
        
        self.db.commit()
        logger.info(f"Fetched {count} stocks")
        return count
    
    async def fetch_stock_details(self, ins_code: int) -> bool:
        """Fetch detailed data for a single stock"""
        try:
            # Get all data
            instrument = await self.client.get_instrument_info(ins_code)
            price_history = await self.client.get_closing_price_history(ins_code)
            client_type = await self.client.get_client_type(ins_code, 0)
            shareholders = await self.client.get_shareholders(ins_code)
            best_limits = await self.client.get_best_limits(ins_code)
            
            # Update stock info
            if instrument and "instrumentInfo" in instrument:
                info = instrument["instrumentInfo"]
                stock = self.db.query(Stock).filter(Stock.ins_code == ins_code).first()
                if stock:
                    stock.eps = info.get("epsValue")
                    stock.pe = info.get("pe")
                    stock.base_volume = info.get("baseVol")
                    stock.capital = info.get("zTitad")
                    stock.sector_code = info.get("cSecValCode")
                    self.db.commit()
            
            # Store price history
            if price_history:
                history = self._parse_price_history(price_history)
                for h in history:
                    if not h["date"]:
                        continue
                    existing = self.db.query(PriceHistory).filter(
                        PriceHistory.ins_code == ins_code,
                        PriceHistory.date == h["date"]
                    ).first()
                    if not existing:
                        self.db.add(PriceHistory(
                            ins_code=ins_code,
                            **h
                        ))
                self.db.commit()
            
            # Store client type
            if client_type:
                ct = self._parse_client_type(client_type)
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                existing = self.db.query(ClientTypeHistory).filter(
                    ClientTypeHistory.ins_code == ins_code,
                    ClientTypeHistory.date == today
                ).first()
                if not existing:
                    self.db.add(ClientTypeHistory(
                        ins_code=ins_code,
                        date=today,
                        **ct
                    ))
                    self.db.commit()
            
            # Store shareholders
            if shareholders:
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                existing = self.db.query(ShareholderSnapshot).filter(
                    ShareholderSnapshot.ins_code == ins_code,
                    ShareholderSnapshot.date == today
                ).first()
                if not existing:
                    self.db.add(ShareholderSnapshot(
                        ins_code=ins_code,
                        date=today,
                        data=shareholders
                    ))
                    self.db.commit()
            
            # Store order book
            if best_limits:
                self.db.add(OrderBookSnapshot(
                    ins_code=ins_code,
                    timestamp=datetime.utcnow(),
                    data=best_limits
                ))
                self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching details for {ins_code}: {e}")
            return False
    
    async def fetch_market_overview(self) -> bool:
        """Fetch market overview"""
        try:
            data = await self.client.get_market_overview()
            if data:
                self.db.add(MarketOverview(
                    timestamp=datetime.utcnow(),
                    data=data
                ))
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return False
    
    # ========== Update Methods ==========
    
    async def full_update(self) -> Dict:
        """Full update - fetch everything"""
        logger.info("Starting full update...")
        start = datetime.utcnow()
        
        # 1. Fetch all stocks
        stock_count = await self.fetch_all_stocks()
        
        # 2. Fetch details for each stock (with rate limiting)
        stocks = self.db.query(Stock).all()
        details_count = 0
        for i, stock in enumerate(stocks):
            logger.info(f"Fetching details {i+1}/{len(stocks)}: {stock.symbol}")
            success = await self.fetch_stock_details(stock.ins_code)
            if success:
                details_count += 1
            
            # Rate limit: 100ms between requests
            await asyncio.sleep(0.1)
        
        # 3. Fetch market overview
        await self.fetch_market_overview()
        
        # Log update
        duration = (datetime.utcnow() - start).total_seconds()
        self.db.add(UpdateLog(
            update_type="full",
            stocks_updated=details_count,
            status="success",
            error_message=f"Duration: {duration:.1f}s"
        ))
        self.db.commit()
        
        logger.info(f"Full update completed: {stock_count} stocks, {details_count} details, {duration:.1f}s")
        return {"stocks": stock_count, "details": details_count, "duration": duration}
    
    async def daily_update(self) -> Dict:
        """Daily update - fetch current prices only"""
        logger.info("Starting daily update...")
        start = datetime.utcnow()
        
        stock_count = await self.fetch_all_stocks()
        
        duration = (datetime.utcnow() - start).total_seconds()
        self.db.add(UpdateLog(
            update_type="daily",
            stocks_updated=stock_count,
            status="success",
            error_message=f"Duration: {duration:.1f}s"
        ))
        self.db.commit()
        
        logger.info(f"Daily update completed: {stock_count} stocks, {duration:.1f}s")
        return {"stocks": stock_count, "duration": duration}
    
    async def manual_update(self, ins_codes: List[int] = None) -> Dict:
        """Manual update - fetch specific stocks or all"""
        logger.info("Starting manual update...")
        start = datetime.utcnow()
        
        if ins_codes:
            count = 0
            for code in ins_codes:
                success = await self.fetch_stock_details(code)
                if success:
                    count += 1
                await asyncio.sleep(0.1)
            result = {"stocks": count}
        else:
            result = await self.full_update()
        
        duration = (datetime.utcnow() - start).total_seconds()
        self.db.add(UpdateLog(
            update_type="manual",
            stocks_updated=result.get("stocks", 0),
            status="success"
        ))
        self.db.commit()
        
        return result
