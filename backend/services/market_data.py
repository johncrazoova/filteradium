"""
فیلترادیوم - Complete Market Data Service
Fetches and stores data for ALL stocks from TSETMC

This service:
1. Fetches all stocks from market watch
2. Stores basic data for each stock
3. Fetches detailed data (shareholders, history, client type) for each
4. Builds a complete database
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy.orm import Session

from backend.api.tsetmc_complete import TSETMCClient, TSETMCDataParser
from backend.models.database import (
    Stock, PriceHistory, Shareholder, ShareholderSnapshot,
    ShareholderHistory, ClientTypeHistory, OrderBookSnapshot,
    init_db, SessionLocal
)


class MarketDataService:
    """
    Complete market data service
    
    Handles fetching and storing data for ALL stocks in the market.
    """
    
    def __init__(self, proxy: Optional[str] = None):
        """
        Initialize market data service
        
        Args:
            proxy: Optional proxy URL for Iranian IP
        """
        self.client = TSETMCClient(proxy=proxy)
        self.parser = TSETMCDataParser()
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    # ============================================================
    # Step 1: Fetch All Stocks Basic Data
    # ============================================================
    
    async def fetch_all_stocks_basic(self) -> List[Dict]:
        """
        Fetch basic data for all stocks from market watch
        
        Returns:
            List of all stocks with basic data
        """
        logger.info("Fetching all stocks from market watch...")
        
        all_stocks = []
        
        # Fetch from different markets
        for market_id in [1, 2, 3]:  # Main, Secondary, Third
            for market_type in [0, 1]:  # All, Active
                try:
                    data = await self.client.get_market_watch(market_id, market_type)
                    if data and "closingPriceAll" in data:
                        for raw_stock in data["closingPriceAll"]:
                            parsed = self.parser.parse_stock(raw_stock)
                            if parsed and parsed.get("ins_code"):
                                # Avoid duplicates
                                if not any(s["ins_code"] == parsed["ins_code"] for s in all_stocks):
                                    all_stocks.append(parsed)
                except Exception as e:
                    logger.error(f"Error fetching market {market_id}/{market_type}: {e}")
        
        logger.info(f"Found {len(all_stocks)} unique stocks")
        return all_stocks
    
    async def store_all_stocks_basic(self) -> int:
        """
        Fetch and store basic data for all stocks
        
        Returns:
            Number of stocks stored
        """
        stocks = await self.fetch_all_stocks_basic()
        count = 0
        
        for stock_data in stocks:
            try:
                self._upsert_stock(stock_data)
                count += 1
            except Exception as e:
                logger.error(f"Error storing stock {stock_data.get('symbol')}: {e}")
        
        self.db.commit()
        logger.info(f"Stored {count} stocks")
        return count
    
    def _upsert_stock(self, stock_data: Dict) -> Stock:
        """Insert or update stock"""
        ins_code = stock_data.get("ins_code")
        
        # Check if exists
        stock = self.db.query(Stock).filter(Stock.ins_code == ins_code).first()
        
        if stock:
            # Update existing
            stock.symbol = stock_data.get("symbol", stock.symbol)
            stock.name = stock_data.get("name", stock.name)
            stock.sector = stock_data.get("sector", stock.sector)
            stock.last_price = stock_data.get("last", stock.last_price)
            stock.close_price = stock_data.get("close", stock.close_price)
            stock.first_price = stock_data.get("first", stock.first_price)
            stock.yesterday_price = stock_data.get("yesterday", stock.yesterday_price)
            stock.high_price = stock_data.get("high", stock.high_price)
            stock.low_price = stock_data.get("low", stock.low_price)
            stock.volume = stock_data.get("volume", stock.volume)
            stock.value = stock_data.get("value", stock.value)
            stock.upper_limit = stock_data.get("upper_limit", stock.upper_limit)
            stock.lower_limit = stock_data.get("lower_limit", stock.lower_limit)
            stock.market_type = stock_data.get("market_type", stock.market_type)
            stock.updated_at = datetime.utcnow()
        else:
            # Create new
            stock = Stock(
                ins_code=ins_code,
                symbol=stock_data.get("symbol", ""),
                name=stock_data.get("name", ""),
                sector=stock_data.get("sector", ""),
                last_price=stock_data.get("last", 0),
                close_price=stock_data.get("close", 0),
                first_price=stock_data.get("first", 0),
                yesterday_price=stock_data.get("yesterday", 0),
                high_price=stock_data.get("high", 0),
                low_price=stock_data.get("low", 0),
                volume=stock_data.get("volume", 0),
                value=stock_data.get("value", 0),
                upper_limit=stock_data.get("upper_limit", 0),
                lower_limit=stock_data.get("lower_limit", 0),
                market_type=stock_data.get("market_type", 0),
            )
            self.db.add(stock)
        
        return stock
    
    # ============================================================
    # Step 2: Fetch Detailed Data for Single Stock
    # ============================================================
    
    async def fetch_stock_detailed(self, ins_code: int) -> Optional[Dict]:
        """
        Fetch detailed data for a single stock
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Complete stock data including shareholders, history, etc.
        """
        try:
            data = await self.client.get_stock_data(ins_code)
            return data
        except Exception as e:
            logger.error(f"Error fetching detailed data for {ins_code}: {e}")
            return None
    
    async def store_stock_detailed(self, ins_code: int) -> bool:
        """
        Fetch and store detailed data for a single stock
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Success status
        """
        data = await self.fetch_stock_detailed(ins_code)
        if not data:
            return False
        
        try:
            # Update stock info
            if data.get("instrument"):
                info = self.parser.parse_instrument_info(data["instrument"])
                stock = self.db.query(Stock).filter(Stock.ins_code == ins_code).first()
                if stock:
                    stock.eps = info.get("eps")
                    stock.pe = info.get("pe")
                    stock.base_volume = info.get("base_volume")
                    stock.capital = info.get("capital")
                    stock.sector = info.get("sector")
                    stock.sector_code = info.get("sector_code")
            
            # Store shareholders
            if data.get("shareholders"):
                shareholders = self.parser.parse_shareholders(data["shareholders"])
                self._store_shareholders(ins_code, shareholders)
            
            # Store shareholder history
            if data.get("shareholder_history"):
                history = self.parser.parse_shareholder_history(data["shareholder_history"])
                self._store_shareholder_history(ins_code, history)
            
            # Store client type
            if data.get("client_type_today"):
                ct = self.parser.parse_client_type(data["client_type_today"])
                self._store_client_type(ins_code, ct, is_daily=True)
            
            if data.get("client_type_total"):
                ct = self.parser.parse_client_type(data["client_type_total"])
                self._store_client_type(ins_code, ct, is_daily=False)
            
            # Store price history
            if data.get("price_history"):
                history = self.parser.parse_price_history(data["price_history"])
                self._store_price_history(ins_code, history)
            
            # Store order book
            if data.get("best_limits"):
                limits = self.parser.parse_best_limits(data["best_limits"])
                self._store_order_book(ins_code, limits)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing detailed data for {ins_code}: {e}")
            self.db.rollback()
            return False
    
    def _store_shareholders(self, ins_code: int, shareholders: List[Dict]):
        """Store shareholders data"""
        for sh in shareholders:
            existing = self.db.query(Shareholder).filter(
                Shareholder.ins_code == ins_code,
                Shareholder.shareholder_name == sh.get("name")
            ).first()
            
            if existing:
                existing.shares = sh.get("shares", existing.shares)
                existing.percentage = sh.get("percentage", existing.percentage)
                existing.change = sh.get("change", existing.change)
                existing.change_type = sh.get("change_type", existing.change_type)
                existing.updated_at = datetime.utcnow()
            else:
                new_sh = Shareholder(
                    ins_code=ins_code,
                    shareholder_name=sh.get("name", ""),
                    shares=sh.get("shares", 0),
                    percentage=sh.get("percentage", 0),
                    change=sh.get("change", 0),
                    change_type=sh.get("change_type", 0),
                    last_date=datetime.utcnow(),
                )
                self.db.add(new_sh)
    
    def _store_shareholder_history(self, ins_code: int, history: List[Dict]):
        """Store shareholder history"""
        for item in history:
            # Check if exists
            existing = self.db.query(ShareholderHistory).filter(
                ShareholderHistory.ins_code == ins_code,
                ShareholderHistory.date == item.get("date"),
                ShareholderHistory.shareholder_name == item.get("name")
            ).first()
            
            if not existing:
                new_record = ShareholderHistory(
                    ins_code=ins_code,
                    date=item.get("date"),
                    shareholder_name=item.get("name", ""),
                    shares=item.get("shares", 0),
                    percentage=item.get("percentage", 0),
                    change=item.get("change", 0),
                )
                self.db.add(new_record)
    
    def _store_client_type(self, ins_code: int, ct: Dict, is_daily: bool = True):
        """Store client type data"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        existing = self.db.query(ClientTypeHistory).filter(
            ClientTypeHistory.ins_code == ins_code,
            ClientTypeHistory.date == today
        ).first()
        
        # Calculate ratios
        buy_vol = ct.get("individual_buy_volume", 0) + ct.get("corporate_buy_volume", 0)
        sell_vol = ct.get("individual_sell_volume", 0) + ct.get("corporate_sell_volume", 0)
        buy_sell_ratio = buy_vol / sell_vol if sell_vol > 0 else 1
        net_buy = buy_vol - sell_vol
        
        if existing:
            if is_daily:
                existing.individual_buy_count = ct.get("individual_buy_count")
                existing.individual_sell_count = ct.get("individual_sell_count")
                existing.individual_buy_volume = ct.get("individual_buy_volume")
                existing.individual_sell_volume = ct.get("individual_sell_volume")
                existing.corporate_buy_count = ct.get("corporate_buy_count")
                existing.corporate_sell_count = ct.get("corporate_sell_count")
                existing.corporate_buy_volume = ct.get("corporate_buy_volume")
                existing.corporate_sell_volume = ct.get("corporate_sell_volume")
                existing.buy_sell_ratio = buy_sell_ratio
                existing.net_buy = net_buy
        else:
            new_ct = ClientTypeHistory(
                ins_code=ins_code,
                date=today,
                individual_buy_count=ct.get("individual_buy_count", 0),
                individual_sell_count=ct.get("individual_sell_count", 0),
                individual_buy_volume=ct.get("individual_buy_volume", 0),
                individual_sell_volume=ct.get("individual_sell_volume", 0),
                corporate_buy_count=ct.get("corporate_buy_count", 0),
                corporate_sell_count=ct.get("corporate_sell_count", 0),
                corporate_buy_volume=ct.get("corporate_buy_volume", 0),
                corporate_sell_volume=ct.get("corporate_sell_volume", 0),
                buy_sell_ratio=buy_sell_ratio,
                net_buy=net_buy,
            )
            self.db.add(new_ct)
    
    def _store_price_history(self, ins_code: int, history: List[Dict]):
        """Store price history"""
        for item in history:
            date_str = item.get("date")
            if date_str:
                try:
                    date = datetime.strptime(date_str, "%Y%m%d")
                except:
                    date = datetime.utcnow()
            else:
                date = datetime.utcnow()
            
            existing = self.db.query(PriceHistory).filter(
                PriceHistory.ins_code == ins_code,
                PriceHistory.date == date
            ).first()
            
            if not existing:
                new_ph = PriceHistory(
                    ins_code=ins_code,
                    date=date,
                    open=item.get("open", 0),
                    high=item.get("high", 0),
                    low=item.get("low", 0),
                    close=item.get("close", 0),
                    last=item.get("last", 0),
                    volume=item.get("volume", 0),
                    value=item.get("value", 0),
                    change=item.get("change", 0),
                    trade_count=item.get("count", 0),
                )
                self.db.add(new_ph)
    
    def _store_order_book(self, ins_code: int, limits: Dict):
        """Store order book snapshot"""
        today = datetime.utcnow()
        
        new_ob = OrderBookSnapshot(
            ins_code=ins_code,
            timestamp=today,
            data=limits,
            total_demand=sum(d.get("quantity", 0) for d in limits.get("demand", [])),
            total_supply=sum(d.get("quantity", 0) for d in limits.get("supply", [])),
            demand_supply_ratio=0,
        )
        
        if new_ob.total_supply > 0:
            new_ob.demand_supply_ratio = new_ob.total_demand / new_ob.total_supply
        
        self.db.add(new_ob)
    
    # ============================================================
    # Step 3: Batch Process All Stocks
    # ============================================================
    
    async def fetch_all_detailed(self, limit: int = 100, delay: float = 0.5) -> int:
        """
        Fetch detailed data for all stocks
        
        Args:
            limit: Maximum number of stocks to process
            delay: Delay between requests (to avoid rate limiting)
            
        Returns:
            Number of stocks processed
        """
        # Get all stocks from database
        stocks = self.db.query(Stock).limit(limit).all()
        logger.info(f"Processing {len(stocks)} stocks...")
        
        count = 0
        for i, stock in enumerate(stocks):
            logger.info(f"[{i+1}/{len(stocks)}] Processing {stock.symbol} ({stock.ins_code})")
            
            success = await self.store_stock_detailed(stock.ins_code)
            if success:
                count += 1
                logger.info(f"  ✅ Success")
            else:
                logger.warning(f"  ❌ Failed")
            
            # Rate limiting
            if delay > 0:
                await asyncio.sleep(delay)
        
        logger.info(f"Successfully processed {count}/{len(stocks)} stocks")
        return count
    
    # ============================================================
    # Step 4: Query Data
    # ============================================================
    
    def get_stock_by_ins_code(self, ins_code: int) -> Optional[Stock]:
        """Get stock by instrument code"""
        return self.db.query(Stock).filter(Stock.ins_code == ins_code).first()
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol"""
        return self.db.query(Stock).filter(Stock.symbol == symbol).first()
    
    def search_stocks(self, query: str) -> List[Stock]:
        """Search stocks by symbol or name"""
        return self.db.query(Stock).filter(
            (Stock.symbol.contains(query)) | 
            (Stock.name.contains(query))
        ).all()
    
    def get_all_stocks(self, limit: int = 1000) -> List[Stock]:
        """Get all stocks"""
        return self.db.query(Stock).limit(limit).all()
    
    def get_stock_shareholders(self, ins_code: int) -> List[Shareholder]:
        """Get shareholders for a stock"""
        return self.db.query(Shareholder).filter(
            Shareholder.ins_code == ins_code
        ).order_by(Shareholder.percentage.desc()).all()
    
    def get_stock_price_history(self, ins_code: int, days: int = 30) -> List[PriceHistory]:
        """Get price history for a stock"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.db.query(PriceHistory).filter(
            PriceHistory.ins_code == ins_code,
            PriceHistory.date >= cutoff
        ).order_by(PriceHistory.date.desc()).all()
    
    def get_stock_client_type(self, ins_code: int, days: int = 30) -> List[ClientTypeHistory]:
        """Get client type history for a stock"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.db.query(ClientTypeHistory).filter(
            ClientTypeHistory.ins_code == ins_code,
            ClientTypeHistory.date >= cutoff
        ).order_by(ClientTypeHistory.date.desc()).all()
    
    def get_market_summary(self) -> Dict:
        """Get market summary"""
        total_stocks = self.db.query(Stock).count()
        total_shareholders = self.db.query(Shareholder).count()
        total_price_history = self.db.query(PriceHistory).count()
        total_client_type = self.db.query(ClientTypeHistory).count()
        
        return {
            "total_stocks": total_stocks,
            "total_shareholders": total_shareholders,
            "total_price_history": total_price_history,
            "total_client_type": total_client_type,
        }


# ============================================================
# Standalone Runner
# ============================================================

async def main():
    """Main function to build complete database"""
    
    print("=" * 60)
    print("فیلترادیوم - Market Data Builder")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    # Create service
    service = MarketDataService()
    
    # Step 1: Fetch and store all stocks basic data
    print("\n📊 Step 1: Fetching all stocks...")
    count = await service.store_all_stocks_basic()
    print(f"✅ Stored {count} stocks")
    
    # Step 2: Fetch detailed data for first N stocks
    print("\n📊 Step 2: Fetching detailed data...")
    print("(This may take a while due to rate limiting)")
    
    detailed_count = await service.fetch_all_detailed(limit=50, delay=1.0)
    print(f"✅ Processed {detailed_count} stocks with detailed data")
    
    # Step 3: Show summary
    print("\n📊 Database Summary:")
    summary = service.get_market_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Database build complete!")


if __name__ == "__main__":
    asyncio.run(main())
