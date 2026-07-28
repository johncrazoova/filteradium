"""
فیلترادیوم - TSETMC API Client
cliet for Tehran Stock Exchange data
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger


class TSETMCClient:
    """Client for TSETMC API"""
    
    BASE_URL = "https://cdn.tsetmc.com"
    OLD_URL = "https://old.tsetmc.com"
    
    # API Endpoints
    ENDPOINTS = {
        "instrument_info": "/api/Instrument/GetInstrumentInfo/{ins_code}",
        "closing_price": "/api/ClosingPrice/GetClosingPriceInfo/{ins_code}",
        "market_watch": "/api/ClosingPrice/GetMarketWatch/{market_id}/{type}",
        "best_limits": "/api/BestLimits/GetBestLimits/{ins_code}",
        "client_type": "/api/ClientType/GetClientType/{ins_code}/{day_or_total}",
        "instruments": "/api/Instrument/GetInstrumentSearch/{search}",
        "market_overview": "/api/ClosingPrice/GetMarketOverview",
    }
    
    def __init__(self, proxy: Optional[str] = None):
        """
        Initialize TSETMC Client
        
        Args:
            proxy: Optional proxy URL (needed for international IPs)
        """
        self.proxy = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://old.tsetmc.com/",
        }
        
    async def _request(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request"""
        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                headers=self.headers,
                timeout=30.0,
                verify=False
            ) as client:
                response = await client.get(endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    async def get_instrument_info(self, ins_code: int) -> Optional[Dict]:
        """Get instrument information"""
        endpoint = self.BASE_URL + self.ENDPOINTS["instrument_info"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_closing_price(self, ins_code: int) -> Optional[Dict]:
        """Get closing price information"""
        endpoint = self.BASE_URL + self.ENDPOINTS["closing_price"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_market_watch(self, market_id: int = 1, market_type: int = 0) -> Optional[Dict]:
        """
        Get market watch data
        
        Args:
            market_id: 1=Main Market, 2=Secondary Market
            market_type: 0=All, 1=Active, 2=Inactive
        """
        endpoint = self.BASE_URL + self.ENDPOINTS["market_watch"].format(
            market_id=market_id, 
            type=market_type
        )
        return await self._request(endpoint)
    
    async def get_best_limits(self, ins_code: int) -> Optional[Dict]:
        """Get best limits (order book)"""
        endpoint = self.BASE_URL + self.ENDPOINTS["best_limits"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_client_type(self, ins_code: int, day_or_total: int = 0) -> Optional[Dict]:
        """
        Get client type data
        
        Args:
            day_or_total: 0=Today, 1=Total
        """
        endpoint = self.BASE_URL + self.ENDPOINTS["client_type"].format(
            ins_code=ins_code,
            day_or_total=day_or_total
        )
        return await self._request(endpoint)
    
    async def search_instruments(self, search: str) -> Optional[List]:
        """Search instruments by symbol or name"""
        endpoint = self.BASE_URL + self.ENDPOINTS["instruments"].format(search=search)
        return await self._request(endpoint)
    
    async def get_market_overview(self) -> Optional[Dict]:
        """Get market overview"""
        endpoint = self.BASE_URL + self.ENDPOINTS["market_overview"]
        return await self._request(endpoint)
    
    async def get_stock_data(self, ins_code: int) -> Optional[Dict]:
        """
        Get comprehensive stock data
        
        Returns:
            Dictionary with all stock data
        """
        # Fetch all data concurrently
        info_task = self.get_instrument_info(ins_code)
        price_task = self.get_closing_price(ins_code)
        limits_task = self.get_best_limits(ins_code)
        client_task = self.get_client_type(ins_code)
        
        info, price, limits, client = await asyncio.gather(
            info_task, price_task, limits_task, client_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        info = info if not isinstance(info, Exception) else None
        price = price if not isinstance(price, Exception) else None
        limits = limits if not isinstance(limits, Exception) else None
        client = client if not isinstance(client, Exception) else None
        
        return {
            "instrument": info,
            "price": price,
            "limits": limits,
            "client_type": client
        }
    
    async def get_all_stocks(self) -> Optional[List]:
        """Get all stocks from market watch"""
        data = await self.get_market_watch()
        if data and "closingPriceAll" in data:
            return data["closingPriceAll"]
        return None


class TSETMCDataParser:
    """Parse TSETMC data into clean format"""
    
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
                              raw_data.get("priceYesterday", 1)) * 100,
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
