"""
فیلترادیوم - FastAPI Server
Main API server for the platform
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional, List, Dict
from pydantic import BaseModel
import asyncio
from loguru import logger

from backend.api.tsetmc_client import TSETMCClient, TSETMCDataParser
from backend.core.scoring import ScoringEngine, Signal, Regime


# Pydantic models
class StockScore(BaseModel):
    ins_code: int
    symbol: str
    name: str
    total_score: float
    signal: str
    confidence: float
    regime: str
    technical: float
    fundamental: float
    moneyflow: float
    risk: float
    momentum: float
    price: float
    change_pct: float
    volume: float


class FilterCondition(BaseModel):
    field: str
    operator: str
    value: float


class FilterRequest(BaseModel):
    conditions: List[FilterCondition]
    min_score: Optional[float] = 0
    limit: Optional[int] = 100


# Initialize FastAPI app
app = FastAPI(
    title="فیلترادیوم API",
    description="پلتفرم فیلترنویسی هوشمند بورس ایران",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
tsetmc_client = TSETMCClient()
data_parser = TSETMCDataParser()
scoring_engine = ScoringEngine()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "فیلترادیوم API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "market_watch": "/api/market",
            "stock_score": "/api/stock/{ins_code}/score",
            "filter": "/api/filter",
            "search": "/api/search"
        }
    }


@app.get("/api/market")
async def get_market_watch(
    market_id: int = Query(1, description="Market ID"),
    market_type: int = Query(0, description="Market type")
):
    """Get market watch data"""
    try:
        data = await tsetmc_client.get_market_watch(market_id, market_type)
        if not data:
            raise HTTPException(status_code=404, detail="Market data not found")
        
        stocks = []
        if "closingPriceAll" in data:
            for raw_stock in data["closingPriceAll"][:100]:  # Limit to 100
                parsed = data_parser.parse_stock(raw_stock)
                if parsed:
                    stocks.append(parsed)
        
        return {"count": len(stocks), "stocks": stocks}
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ins_code}/score")
async def get_stock_score(ins_code: int):
    """Get stock score and analysis"""
    try:
        # Get stock data
        stock_data = await tsetmc_client.get_stock_data(ins_code)
        
        if not stock_data or not stock_data.get("price"):
            raise HTTPException(status_code=404, detail="Stock data not found")
        
        # Parse price data
        price_data = stock_data["price"]
        if "closingPrice" in price_data:
            price_info = price_data["closingPrice"]
        else:
            price_info = price_data
        
        # Extract OHLCV
        closes = [price_info.get("pClosing", 0)]
        highs = [price_info.get("priceMax", 0)]
        lows = [price_info.get("priceMin", 0)]
        opens = [price_info.get("priceFirst", 0)]
        volumes = [price_info.get("qTotTran5J", 0)]
        
        # Add historical data if available
        if "closingPriceHistory" in price_data:
            for hist in price_data["closingPriceHistory"][:50]:
                closes.append(hist.get("pClosing", 0))
                highs.append(hist.get("priceMax", 0))
                lows.append(hist.get("priceMin", 0))
                opens.append(hist.get("priceFirst", 0))
                volumes.append(hist.get("qTotTran5J", 0))
        
        # Parse client type
        client_type = None
        if stock_data.get("client_type"):
            client_type = data_parser.parse_client_type(stock_data["client_type"])
        
        # Calculate score
        result = scoring_engine.calculate_score(
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            client_type=client_type
        )
        
        # Get instrument info
        instrument = stock_data.get("instrument", {})
        if instrument and "instrumentInfo" in instrument:
            inst_info = instrument["instrumentInfo"]
        else:
            inst_info = instrument
        
        return {
            "ins_code": ins_code,
            "symbol": inst_info.get("lVal18AFC", ""),
            "name": inst_info.get("lVal18", ""),
            "price": closes[0],
            "change_pct": ((closes[0] - (closes[1] if len(closes) > 1 else closes[0])) / 
                          (closes[1] if len(closes) > 1 else 1)) * 100,
            "volume": volumes[0],
            "score": {
                "total": result.total_score,
                "signal": result.signal.value,
                "confidence": result.confidence,
                "regime": result.regime.value,
                "technical": result.technical,
                "fundamental": result.fundamental,
                "moneyflow": result.moneyflow,
                "risk": result.risk,
                "momentum": result.momentum
            },
            "details": result.details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/filter")
async def apply_filter(request: FilterRequest):
    """Apply filter to all stocks"""
    try:
        # Get market data
        market_data = await tsetmc_client.get_market_watch()
        
        if not market_data or "closingPriceAll" not in market_data:
            raise HTTPException(status_code=404, detail="Market data not found")
        
        results = []
        
        for raw_stock in market_data["closingPriceAll"][:200]:  # Limit
            parsed = data_parser.parse_stock(raw_stock)
            if not parsed:
                continue
            
            # Apply filter conditions
            passes = True
            for condition in request.conditions:
                value = parsed.get(condition.field, 0)
                if condition.operator == ">":
                    if not (value > condition.value):
                        passes = False
                        break
                elif condition.operator == "<":
                    if not (value < condition.value):
                        passes = False
                        break
                elif condition.operator == ">=":
                    if not (value >= condition.value):
                        passes = False
                        break
                elif condition.operator == "<=":
                    if not (value <= condition.value):
                        passes = False
                        break
                elif condition.operator == "==":
                    if not (value == condition.value):
                        passes = False
                        break
            
            if passes:
                results.append(parsed)
        
        # Sort by volume
        results.sort(key=lambda x: x.get("volume", 0), reverse=True)
        
        return {
            "count": len(results[:request.limit]),
            "results": results[:request.limit]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_stocks(q: str = Query(..., description="Search query")):
    """Search stocks by symbol or name"""
    try:
        results = await tsetmc_client.search_instruments(q)
        if not results:
            return {"count": 0, "results": []}
        
        return {"count": len(results), "results": results}
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scores/batch")
async def get_batch_scores(ins_codes: str = Query(..., description="Comma-separated ins_codes")):
    """Get scores for multiple stocks"""
    try:
        codes = [int(c.strip()) for c in ins_codes.split(",")]
        results = []
        
        for code in codes[:50]:  # Limit
            try:
                score = await get_stock_score(code)
                results.append(score)
            except:
                continue
        
        # Sort by total score
        results.sort(key=lambda x: x.get("score", {}).get("total", 0), reverse=True)
        
        return {"count": len(results), "results": results}
    except Exception as e:
        logger.error(f"Error getting batch scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Predefined filters
@app.get("/api/filters/presets")
async def get_preset_filters():
    """Get predefined filter presets"""
    return {
        "filters": [
            {
                "name": "مومنتوم قوی",
                "description": "سهم‌های با رشد پیوسته و حجم بالا",
                "conditions": [
                    {"field": "change_pct", "operator": ">", "value": 2},
                    {"field": "volume", "operator": ">", "value": 1000000}
                ]
            },
            {
                "name": "ورود پول هوشمند",
                "description": "خرید سنگین حقوقی",
                "conditions": [
                    {"field": "volume", "operator": ">", "value": 2000000},
                    {"field": "change_pct", "operator": ">", "value": 0}
                ]
            },
            {
                "name": "شکست مقاومت",
                "description": "عبور از مقاومت با تایید حجم",
                "conditions": [
                    {"field": "volume", "operator": ">", "value": 3000000},
                    {"field": "change_pct", "operator": ">", "value": 1}
                ]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
