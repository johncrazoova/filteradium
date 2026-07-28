"""
TSETMC API Client - Complete client for all TSETMC endpoints
Requires Iranian IP for access
"""
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger


class TSETMCClient:
    """Complete TSETMC API Client"""
    
    CDN_URL = "https://cdn.tsetmc.com"
    
    ENDPOINTS = {
        # Instrument
        "instrument_info": "/api/Instrument/GetInstrumentInfo/{ins_code}",
        "instrument_search": "/api/Instrument/GetInstrumentSearch/{search}",
        
        # Price
        "closing_price": "/api/ClosingPrice/GetClosingPriceInfo/{ins_code}",
        "closing_price_all": "/api/ClosingPrice/GetClosingPriceAll",
        "market_watch": "/api/ClosingPrice/GetMarketWatch/{market_id}/{type}",
        "market_overview": "/api/ClosingPrice/GetMarketOverview",
        "closing_price_history": "/api/ClosingPrice/GetClosingPriceHistory/{ins_code}",
        "price_change": "/api/ClosingPrice/GetPriceChange/{ins_code}",
        
        # Order Book
        "best_limits": "/api/BestLimits/GetBestLimits/{ins_code}",
        "best_limits_detail": "/api/BestLimits/GetBestLimitsDetail/{ins_code}",
        
        # Client Type
        "client_type": "/api/ClientType/GetClientType/{ins_code}/{day_or_total}",
        "client_type_history": "/api/ClientType/GetClientTypeHistory/{ins_code}",
        
        # Shareholders
        "shareholders": "/api/Shareholder/GetInstrumentShareholders/{ins_code}",
        "shareholder_history": "/api/Shareholder/GetInstrumentShareholderHistory/{ins_code}",
        
        # Market State
        "market_state": "/api/MarketData/GetMarketState",
        "instrument_market": "/api/MarketData/GetInstrumentMarketState/{ins_code}",
        
        # Index
        "index_b1": "/api/Index/GetIndexB1",
        "index_b2": "/api/Index/GetIndexB2",
        
        # Sector
        "sectors": "/api/StaticData/GetStaticData",
        "sector_instruments": "/api/StaticData/GetStaticData/{sector_id}",
        
        # Message
        "messages": "/api/Message/GetMessage",
        "instrument_messages": "/api/Message/GetInstrumentMessage/{ins_code}",
    }
    
    def __init__(self, proxy: Optional[str] = None, timeout: float = 30.0):
        self.proxy = proxy
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8",
            "Referer": "https://old.tsetmc.com/",
            "Origin": "https://old.tsetmc.com",
        }
    
    async def _request(self, endpoint: str) -> Optional[Dict]:
        """Make HTTP request"""
        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                headers=self.headers,
                timeout=self.timeout,
                verify=False
            ) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Request failed: {endpoint} - {e}")
            return None
    
    # ========== Instrument ==========
    
    async def get_instrument_info(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_info"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def search_instruments(self, search: str) -> Optional[List]:
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_search"].format(search=search)
        return await self._request(endpoint)
    
    # ========== Price ==========
    
    async def get_closing_price(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["closing_price"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_closing_price_all(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["closing_price_all"]
        return await self._request(endpoint)
    
    async def get_market_watch(self, market_id: int = 1, market_type: int = 0) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["market_watch"].format(
            market_id=market_id, type=market_type
        )
        return await self._request(endpoint)
    
    async def get_market_overview(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["market_overview"]
        return await self._request(endpoint)
    
    async def get_closing_price_history(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["closing_price_history"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_price_change(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["price_change"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ========== Order Book ==========
    
    async def get_best_limits(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["best_limits"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_best_limits_detail(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["best_limits_detail"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ========== Client Type ==========
    
    async def get_client_type(self, ins_code: int, day_or_total: int = 0) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["client_type"].format(
            ins_code=ins_code, day_or_total=day_or_total
        )
        return await self._request(endpoint)
    
    async def get_client_type_history(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["client_type_history"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ========== Shareholders ==========
    
    async def get_shareholders(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["shareholders"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    async def get_shareholder_history(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["shareholder_history"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ========== Market State ==========
    
    async def get_market_state(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["market_state"]
        return await self._request(endpoint)
    
    async def get_instrument_market_state(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_market"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ========== Index ==========
    
    async def get_index_b1(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["index_b1"]
        return await self._request(endpoint)
    
    async def get_index_b2(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["index_b2"]
        return await self._request(endpoint)
    
    # ========== Sector ==========
    
    async def get_sectors(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["sectors"]
        return await self._request(endpoint)
    
    async def get_sector_instruments(self, sector_id: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["sector_instruments"].format(sector_id=sector_id)
        return await self._request(endpoint)
    
    # ========== Message ==========
    
    async def get_messages(self) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["messages"]
        return await self._request(endpoint)
    
    async def get_instrument_messages(self, ins_code: int) -> Optional[Dict]:
        endpoint = self.CDN_URL + self.ENDPOINTS["instrument_messages"].format(ins_code=ins_code)
        return await self._request(endpoint)
    
    # ========== Combined ==========
    
    async def get_all_stocks(self) -> Optional[List]:
        """Get all stocks from market"""
        data = await self.get_market_watch()
        if data and "closingPriceAll" in data:
            return data["closingPriceAll"]
        return None
    
    async def get_stock_full(self, ins_code: int) -> Optional[Dict]:
        """Get all data for a single stock"""
        tasks = [
            self.get_instrument_info(ins_code),
            self.get_closing_price(ins_code),
            self.get_best_limits(ins_code),
            self.get_client_type(ins_code, 0),
            self.get_client_type(ins_code, 1),
            self.get_shareholders(ins_code),
            self.get_closing_price_history(ins_code),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        keys = [
            "instrument", "price", "best_limits",
            "client_type_today", "client_type_total",
            "shareholders", "price_history"
        ]
        
        return {k: r if not isinstance(r, Exception) else None for k, r in zip(keys, results)}
