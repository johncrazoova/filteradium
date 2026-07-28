"""
فیلترادیوم - TSETMC Complete API Client
Complete client for all TSETMC data including shareholders and history

All known TSETMC API endpoints for:
- Instrument info
- Price data (current & historical)
- Shareholders (سهام‌داران)
- History (سابقه)
- Order book (بهترین عرضه/تقاضا)
- Client type (حقیقی/حقوقی)
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger
from datetime import datetime


class TSETMCClient:
    """
    Complete TSETMC API Client
    
    Supports all known endpoints for Tehran Stock Exchange data.
    Requires Iranian IP or proxy for access.
    """
    
    # Base URLs
    CDN_URL = "https://cdn.tsetmc.com"
    OLD_URL = "https://old.tsetmc.com"
    TSETMC_URL = "https://tsetmc.com"
    
    # ============================================================
    # API Endpoints
    # ============================================================
    
    ENDPOINTS = {
        # ===== Instrument APIs =====
        "instrument_info": "/api/Instrument/GetInstrumentInfo/{ins_code}",
        "instrument_search": "/api/Instrument/GetInstrumentSearch/{search}",
        "instruments": "/api/Instrument/GetInstrumentSearch/{search}",
        
        # ===== Price APIs =====
        "closing_price": "/api/ClosingPrice/GetClosingPriceInfo/{ins_code}",
        "closing_price_all": "/api/ClosingPrice/GetClosingPriceAll",
        "market_watch": "/api/ClosingPrice/GetMarketWatch/{market_id}/{type}",
        "market_overview": "/api/ClosingPrice/GetMarketOverview",
        
        # ===== Historical Price APIs =====
        "closing_price_history": "/api/ClosingPrice/GetClosingPriceHistory/{ins_code}",
        "price_changes": "/api/ClosingPrice/GetPriceChange/{ins_code}",
        
        # ===== Order Book APIs =====
        "best_limits": "/api/BestLimits/GetBestLimits/{ins_code}",
        "best_limits_detail": "/api/BestLimits/GetBestLimitsDetail/{ins_code}",
        
        # ===== Client Type APIs =====
        "client_type": "/api/ClientType/GetClientType/{ins_code}/{day_or_total}",
        "client_type_history": "/api/ClientType/GetClientTypeHistory/{ins_code}",
        
        # ===== Shareholder APIs (سهام‌داران) =====
        "shareholders": "/api/Shareholder/GetInstrumentShareholders/{ins_code}",
        "shareholder_history": "/api/Shareholder/GetInstrumentShareholderHistory/{ins_code}",
        
        # ===== Market State APIs =====
        "market_state": "/api/MarketData/GetMarketState",
        "instrument_market": "/api/MarketData/GetInstrumentMarketState/{ins_code}",
        
        # ===== Index APIs =====
        "index_b1": "/api/Index/GetIndexB1",
        "index_b2": "/api/Index/GetIndexB2",
        
        # ===== Sector APIs =====
        "sectors": "/api/StaticData/GetStaticData",
        "sector_instruments": "/api/StaticData/GetStaticData/{sector_id}",
        
        # ===== Message APIs =====
        "messages": "/api/Message/GetMessage",
        "instrument_messages": "/api/Message/GetInstrumentMessage/{ins_code}",
    }
    
    # Known ins_codes for popular stocks
    KNOWN_STOCKS = {
        "خساپا": 164825749812583985,
        "خودرو": 65883957528548870,
        "فولاد": 46348552314985160,
        "فملی": 62752822824611701,
        "شپنا": 35425587664162881,
        "شبندر": 20813285709680328,
        "کگل": 62755692645762881,
        "وبملت": 23456789012345678,
        "تاپیکو": 62879545926137980,
        "جم": 13068359010280975,
        "سایپا": 57631445418375704,
        "خپارس": 10457254982612816,
        "های وب": 53137489195258270,
        "پترول": 52556955283675688,
        "شتران": 60489893236680253,
    }
    
    def __init__(self, proxy: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize TSETMC Client
        
        Args:
            proxy: Optional proxy URL (required for international IPs)
            timeout: Request timeout in seconds
        """
        self.proxy = proxy
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://old.tsetmc.com/",
            "Origin": "https://old.tsetmc.com",
        }
    
    async def _request(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request"""
        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                headers=self.headers,
                timeout=self.timeout,
                verify=False
            ) as client:
                response = await client.get(endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.warning(f"Timeout: {endpoint}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code}: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {endpoint} - {e}")
            return None
    
    # ============================================================
    # Instrument APIs
    # ============================================================
    
    async def get_instrument_info(self, ins_code: int) -> Optional[Dict]:
        """
        Get instrument information
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Instrument info dictionary
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_info"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def search_instruments(self, search: str) -> Optional[List]:
        """
        Search instruments by symbol or name
        
        Args:
            search: Search query
            
        Returns:
            List of matching instruments
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_search"].format(search=search)
        return await self._request(endpoint)
    
    # ============================================================
    # Price APIs
    # ============================================================
    
    async def get_closing_price(self, ins_code: int) -> Optional[Dict]:
        """
        Get closing price information
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Price data dictionary
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["closing_price"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_market_watch(self, market_id: int = 1, market_type: int = 0) -> Optional[Dict]:
        """
        Get market watch data
        
        Args:
            market_id: 1=Main Market, 2=Secondary, 3=Third Market, 4=Option
            market_type: 0=All, 1=Active, 2=Inactive
            
        Returns:
            Market watch data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["market_watch"].format(
            market_id=market_id,
            type=market_type
        )
        return await self._request(endpoint)
    
    async def get_market_overview(self) -> Optional[Dict]:
        """Get market overview"""
        endpoint = self.CDN_URL + self.ENDPOINTS["market_overview"]
        return await self._request(endpoint)
    
    # ============================================================
    # Historical Price APIs
    # ============================================================
    
    async def get_closing_price_history(self, ins_code: int) -> Optional[Dict]:
        """
        Get historical closing prices
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Historical price data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["closing_price_history"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_price_changes(self, ins_code: int) -> Optional[Dict]:
        """
        Get price changes
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Price change data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["price_changes"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ============================================================
    # Order Book APIs
    # ============================================================
    
    async def get_best_limits(self, ins_code: int) -> Optional[Dict]:
        """
        Get best limits (order book snapshot)
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Best limits data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["best_limits"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_best_limits_detail(self, ins_code: int) -> Optional[Dict]:
        """
        Get detailed best limits
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Detailed best limits
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["best_limits_detail"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ============================================================
    # Client Type APIs
    # ============================================================
    
    async def get_client_type(self, ins_code: int, day_or_total: int = 0) -> Optional[Dict]:
        """
        Get client type data (حقیقی/حقوقی)
        
        Args:
            ins_code: Instrument code
            day_or_total: 0=Today, 1=Total
            
        Returns:
            Client type data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["client_type"].format(
            ins_code=ins_code,
            day_or_total=day_or_total
        )
        return await self._request(endpoint)
    
    async def get_client_type_history(self, ins_code: int) -> Optional[Dict]:
        """
        Get client type history
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Client type history data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["client_type_history"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ============================================================
    # Shareholder APIs (سهام‌داران)
    # ============================================================
    
    async def get_shareholders(self, ins_code: int) -> Optional[Dict]:
        """
        Get current shareholders (سهام‌داران)
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Shareholders data including:
            - Shareholder name
            - Number of shares
            - Percentage
            - Change (increase/decrease)
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["shareholders"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_shareholder_history(self, ins_code: int) -> Optional[Dict]:
        """
        Get shareholder history (تاریخچه سهام‌داران)
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Historical shareholders data
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["shareholder_history"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ============================================================
    # Market State APIs
    # ============================================================
    
    async def get_market_state(self) -> Optional[Dict]:
        """Get market state (وضعیت بازار)"""
        endpoint = self.CDN_URL + self.ENDPOINTS["market_state"]
        return await self._request(endpoint)
    
    async def get_instrument_market_state(self, ins_code: int) -> Optional[Dict]:
        """
        Get instrument market state
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Instrument market state
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_market"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ============================================================
    # Index APIs
    # ============================================================
    
    async def get_index_b1(self) -> Optional[Dict]:
        """Get Index B1"""
        endpoint = self.CDN_URL + self.ENDPOINTS["index_b1"]
        return await self._request(endpoint)
    
    async def get_index_b2(self) -> Optional[Dict]:
        """Get Index B2"""
        endpoint = self.CDN_URL + self.ENDPOINTS["index_b2"]
        return await self._request(endpoint)
    
    # ============================================================
    # Sector APIs
    # ============================================================
    
    async def get_sectors(self) -> Optional[Dict]:
        """Get all sectors (گروه‌های صنعت)"""
        endpoint = self.CDN_URL + self.ENDPOINTS["sectors"]
        return await self._request(endpoint)
    
    async def get_sector_instruments(self, sector_id: int) -> Optional[Dict]:
        """
        Get instruments in a sector
        
        Args:
            sector_id: Sector ID
            
        Returns:
            Instruments in the sector
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["sector_instruments"].format(sector_id=sector_id)
        return await self._request(endpoint)
    
    # ============================================================
    # Message APIs
    # ============================================================
    
    async def get_messages(self) -> Optional[Dict]:
        """Get market messages"""
        endpoint = self.CDN_URL + self.ENDPOINTS["messages"]
        return await self._request(endpoint)
    
    async def get_instrument_messages(self, ins_code: int) -> Optional[Dict]:
        """
        Get instrument messages
        
        Args:
            ins_code: Instrument code
            
        Returns:
            Instrument messages
        """
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_messages"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ============================================================
    # Combined Data APIs
    # ============================================================
    
    async def get_stock_data(self, ins_code: int) -> Optional[Dict]:
        """
        Get comprehensive stock data
        
        Args:
            ins_code: Instrument code
            
        Returns:
            All stock data including price, history, shareholders, client type
        """
        # Fetch all data concurrently
        tasks = [
            self.get_instrument_info(ins_code),
            self.get_closing_price(ins_code),
            self.get_best_limits(ins_code),
            self.get_client_type(ins_code, 0),
            self.get_client_type(ins_code, 1),
            self.get_shareholders(ins_code),
            self.get_shareholder_history(ins_code),
            self.get_closing_price_history(ins_code),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        data = {}
        keys = [
            "instrument", "price", "best_limits", 
            "client_type_today", "client_type_total",
            "shareholders", "shareholder_history", "price_history"
        ]
        
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {key}: {result}")
                data[key] = None
            else:
                data[key] = result
        
        return data
    
    async def get_all_stocks(self) -> Optional[List]:
        """
        Get all stocks from market watch
        
        Returns:
            List of all stocks
        """
        data = await self.get_market_watch()
        if data and "closingPriceAll" in data:
            return data["closingPriceAll"]
        return None


class TSETMCDataParser:
    """
    Parse TSETMC data into clean, structured format
    
    Converts raw API responses into clean dictionaries
    ready for database storage and analysis.
    """
    
    @staticmethod
    def parse_stock(raw_data: Dict) -> Dict:
        """Parse raw stock data into clean format"""
        try:
            return {
                "ins_code": raw_data.get("insCode"),
                "symbol": raw_data.get("lVal18AFC", ""),
                "name": raw_data.get("lVal18", ""),
                "close": raw_data.get("pClosing", 0),
                "last": raw_data.get("pDrCotVal", 0),
                "first": raw_data.get("priceFirst", 0),
                "yesterday": raw_data.get("priceYesterday", 0),
                "high": raw_data.get("priceMax", 0),
                "low": raw_data.get("priceMin", 0),
                "volume": raw_data.get("qTotTran5J", 0),
                "value": raw_data.get("qTotCap", 0),
                "change": raw_data.get("pDrCotVal", 0) - raw_data.get("priceYesterday", 0),
                "change_pct": ((raw_data.get("pDrCotVal", 0) - raw_data.get("priceYesterday", 0)) / 
                              max(raw_data.get("priceYesterday", 1), 1)) * 100,
                "count": raw_data.get("zTitad", 0),
                "upper_limit": raw_data.get("pMax", 0),
                "lower_limit": raw_data.get("pMin", 0),
                "market_type": raw_data.get("flow", 0),
                "sector": raw_data.get("cSecVal", ""),
            }
        except Exception as e:
            logger.error(f"Error parsing stock data: {e}")
            return {}
    
    @staticmethod
    def parse_client_type(raw_data: Dict) -> Dict:
        """Parse client type data"""
        try:
            return {
                "individual_buy_count": raw_data.get("buy_I_Count", 0),
                "individual_sell_count": raw_data.get("sell_I_Count", 0),
                "individual_buy_volume": raw_data.get("buy_I_Volume", 0),
                "individual_sell_volume": raw_data.get("sell_I_Volume", 0),
                "corporate_buy_count": raw_data.get("buy_N_Count", 0),
                "corporate_sell_count": raw_data.get("sell_N_Count", 0),
                "corporate_buy_volume": raw_data.get("buy_N_Volume", 0),
                "corporate_sell_volume": raw_data.get("sell_N_Volume", 0),
            }
        except Exception as e:
            logger.error(f"Error parsing client type: {e}")
            return {}
    
    @staticmethod
    def parse_shareholders(raw_data: Dict) -> List[Dict]:
        """
        Parse shareholders data (سهام‌داران)
        
        Returns list of shareholders with:
        - name: Shareholder name
        - shares: Number of shares
        - percentage: Ownership percentage
        - change: Change in shares
        - change_pct: Change percentage
        """
        try:
            shareholders = []
            
            if "shareShareholder" in raw_data:
                for sh in raw_data["shareShareholder"]:
                    shareholders.append({
                        "name": sh.get("shareHolderName", ""),
                        "shares": sh.get("shares", 0),
                        "percentage": sh.get("perOfShares", 0),
                        "change": sh.get("change", 0),
                        "change_type": sh.get("changeType", 0),  # 0=no change, 1=increase, -1=decrease
                        "ins_code": sh.get("insCode", 0),
                    })
            
            return shareholders
        except Exception as e:
            logger.error(f"Error parsing shareholders: {e}")
            return []
    
    @staticmethod
    def parse_shareholder_history(raw_data: Dict) -> List[Dict]:
        """
        Parse shareholder history
        
        Returns historical shareholder data
        """
        try:
            history = []
            
            if "shareShareholder" in raw_data:
                for sh in raw_data["shareShareholder"]:
                    history.append({
                        "date": sh.get("dEven", ""),
                        "name": sh.get("shareHolderName", ""),
                        "shares": sh.get("shares", 0),
                        "percentage": sh.get("perOfShares", 0),
                        "change": sh.get("change", 0),
                        "ins_code": sh.get("insCode", 0),
                    })
            
            return history
        except Exception as e:
            logger.error(f"Error parsing shareholder history: {e}")
            return []
    
    @staticmethod
    def parse_price_history(raw_data: Dict) -> List[Dict]:
        """
        Parse historical price data (سابقه)
        
        Returns list of daily OHLCV data
        """
        try:
            history = []
            
            if "closingPriceHistory" in raw_data:
                for item in raw_data["closingPriceHistory"]:
                    history.append({
                        "date": item.get("dEven", ""),
                        "open": item.get("priceFirst", 0),
                        "high": item.get("priceMax", 0),
                        "low": item.get("priceMin", 0),
                        "close": item.get("pClosing", 0),
                        "last": item.get("pDrCotVal", 0),
                        "volume": item.get("qTotTran5J", 0),
                        "value": item.get("qTotCap", 0),
                        "change": item.get("priceChange", 0),
                        "change_pct": item.get("priceMin", 0),
                        "count": item.get("zTitad", 0),
                    })
            
            return history
        except Exception as e:
            logger.error(f"Error parsing price history: {e}")
            return []
    
    @staticmethod
    def parse_best_limits(raw_data: Dict) -> Dict:
        """
        Parse order book (بهترین عرضه/تقاضا)
        
        Returns structured order book data
        """
        try:
            limits = {
                "demand": [],  # Buy orders
                "supply": [],  # Sell orders
            }
            
            if "bestLimits" in raw_data:
                for item in raw_data["bestLimits"]:
                    row = {
                        "count": item.get("number", 0),
                        "quantity": item.get("qTitTran", 0),
                        "price": item.get("pMeDem", 0) if "pMeDem" in item else item.get("pMeOf", 0),
                    }
                    
                    if "pMeDem" in item:
                        limits["demand"].append(row)
                    elif "pMeOf" in item:
                        limits["supply"].append(row)
            
            return limits
        except Exception as e:
            logger.error(f"Error parsing best limits: {e}")
            return {"demand": [], "supply": []}
    
    @staticmethod
    def parse_instrument_info(raw_data: Dict) -> Dict:
        """
        Parse instrument information
        
        Returns comprehensive instrument data
        """
        try:
            info = raw_data.get("instrumentInfo", {})
            
            return {
                "ins_code": info.get("insCode", 0),
                "symbol": info.get("lVal18AFC", ""),
                "name": info.get("lVal18", ""),
                "sector": info.get("cSecVal", ""),
                "sector_code": info.get("cSecValCode", ""),
                "market": info.get("flow", 0),
                "eps": info.get("epsValue", 0),
                "pe": info.get("pe", 0),
                "base_volume": info.get("baseVol", 0),
                "last_date": info.get("lastDate", ""),
                "status": info.get("cIsin", ""),
                "capital": info.get("zTitad", 0),
            }
        except Exception as e:
            logger.error(f"Error parsing instrument info: {e}")
            return {}


# ============================================================
# Example Usage
# ============================================================

async def main():
    """Example usage of TSETMC client"""
    
    client = TSETMCClient()
    
    # Get stock data for خساپا
    ins_code = 164825749812583985
    
    print("Fetching data for خساپا...")
    data = await client.get_stock_data(ins_code)
    
    if data:
        # Parse data
        parser = TSETMCDataParser()
        
        if data.get("instrument"):
            info = parser.parse_instrument_info(data["instrument"])
            print(f"\n=== Instrument Info ===")
            print(f"Symbol: {info.get('symbol')}")
            print(f"Name: {info.get('name')}")
            print(f"Sector: {info.get('sector')}")
            print(f"EPS: {info.get('eps')}")
            print(f"PE: {info.get('pe')}")
        
        if data.get("shareholders"):
            shareholders = parser.parse_shareholders(data["shareholders"])
            print(f"\n=== Shareholders ({len(shareholders)}) ===")
            for sh in shareholders[:5]:
                print(f"{sh['name']}: {sh['percentage']:.2f}%")
        
        if data.get("price_history"):
            history = parser.parse_price_history(data["price_history"])
            print(f"\n=== Price History ({len(history)} days) ===")
            for h in history[:3]:
                print(f"{h['date']}: Close={h['close']}, Vol={h['volume']}")
        
        if data.get("client_type_today"):
            ct = parser.parse_client_type(data["client_type_today"])
            print(f"\n=== Client Type (Today) ===")
            print(f"Individual Buy: {ct['individual_buy_volume']}")
            print(f"Corporate Buy: {ct['corporate_buy_volume']}")


if __name__ == "__main__":
    asyncio.run(main())
