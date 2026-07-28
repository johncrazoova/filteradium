"""
فیلترادیوم - FastAPI Server (Complete)
Main API server with all features
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime
import asyncio
from loguru import logger

from backend.api.tsetmc_complete import TSETMCClient, TSETMCDataParser
from backend.api.user_panel import setup_user_routes
from backend.core.scoring import ScoringEngine, Signal, Regime
from backend.core.indicators import TechnicalIndicators
from backend.core.backtest import BacktestEngine, StrategyType, StrategyLibrary
from backend.models.database import (
    Stock, PriceHistory, Shareholder, ClientTypeHistory,
    ScoreHistory, init_db, SessionLocal
)


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


class BacktestRequest(BaseModel):
    ins_code: int
    strategy: str
    params: Optional[Dict] = None
    days: Optional[int] = 365


# Initialize FastAPI app
app = FastAPI(
    title="فیلترادیوم API",
    description="پلتفرم فیلترنویسی هوشمند بورس ایران",
    version="2.0.0"
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
backtest_engine = BacktestEngine()

# Setup user routes
setup_user_routes(app)

# Initialize database
init_db()


# ============================================================
# Root & Health
# ============================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "فیلترادیوم API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "market": "/api/market",
            "stock": "/api/stock/{ins_code}",
            "score": "/api/stock/{ins_code}/score",
            "filter": "/api/filter",
            "search": "/api/search",
            "backtest": "/api/backtest",
            "indicators": "/api/stock/{ins_code}/indicators",
            "auth": "/api/auth/*",
            "filters": "/api/filters",
            "alerts": "/api/alerts"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    db = SessionLocal()
    stock_count = db.query(Stock).count()
    db.close()
    
    return {
        "status": "healthy",
        "database": "connected",
        "stocks": stock_count,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================
# Market Data Endpoints
# ============================================================

@app.get("/api/market")
async def get_market_watch(
    market_id: int = Query(1, description="Market ID"),
    market_type: int = Query(0, description="Market type"),
    limit: int = Query(100, description="Limit results")
):
    """Get market watch data"""
    try:
        # Try database first
        db = SessionLocal()
        stocks = db.query(Stock).limit(limit).all()
        db.close()
        
        if stocks:
            return {
                "count": len(stocks),
                "stocks": [
                    {
                        "ins_code": s.ins_code,
                        "symbol": s.symbol,
                        "name": s.name,
                        "last_price": s.last_price,
                        "close_price": s.close_price,
                        "change_pct": ((s.last_price - s.yesterday_price) / s.yesterday_price * 100) if s.yesterday_price else 0,
                        "volume": s.volume,
                        "value": s.value,
                        "sector": s.sector,
                        "score": s.total_score,
                        "signal": s.signal
                    }
                    for s in stocks
                ]
            }
        
        # Fallback to API
        data = await tsetmc_client.get_market_watch(market_id, market_type)
        if not data:
            raise HTTPException(status_code=404, detail="Market data not found")
        
        stocks_data = []
        if "closingPriceAll" in data:
            for raw_stock in data["closingPriceAll"][:limit]:
                parsed = data_parser.parse_stock(raw_stock)
                if parsed:
                    stocks_data.append(parsed)
        
        return {"count": len(stocks_data), "stocks": stocks_data}
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ins_code}")
async def get_stock(ins_code: int):
    """Get stock details"""
    try:
        # Try database first
        db = SessionLocal()
        stock = db.query(Stock).filter(Stock.ins_code == ins_code).first()
        
        if stock:
            # Get shareholders
            shareholders = db.query(Shareholder).filter(
                Shareholder.ins_code == ins_code
            ).order_by(Shareholder.percentage.desc()).limit(10).all()
            
            # Get recent price history
            price_history = db.query(PriceHistory).filter(
                PriceHistory.ins_code == ins_code
            ).order_by(PriceHistory.date.desc()).limit(30).all()
            
            # Get client type
            client_type = db.query(ClientTypeHistory).filter(
                ClientTypeHistory.ins_code == ins_code
            ).order_by(ClientTypeHistory.date.desc()).first()
            
            db.close()
            
            return {
                "ins_code": stock.ins_code,
                "symbol": stock.symbol,
                "name": stock.name,
                "sector": stock.sector,
                "last_price": stock.last_price,
                "close_price": stock.close_price,
                "first_price": stock.first_price,
                "yesterday_price": stock.yesterday_price,
                "high_price": stock.high_price,
                "low_price": stock.low_price,
                "volume": stock.volume,
                "value": stock.value,
                "upper_limit": stock.upper_limit,
                "lower_limit": stock.lower_limit,
                "eps": stock.eps,
                "pe": stock.pe,
                "shareholders": [
                    {
                        "name": sh.shareholder_name,
                        "shares": sh.shares,
                        "percentage": sh.percentage,
                        "change": sh.change
                    }
                    for sh in shareholders
                ],
                "price_history": [
                    {
                        "date": ph.date.isoformat() if ph.date else None,
                        "open": ph.open,
                        "high": ph.high,
                        "low": ph.low,
                        "close": ph.close,
                        "volume": ph.volume
                    }
                    for ph in price_history
                ],
                "client_type": {
                    "individual_buy": client_type.individual_buy_volume if client_type else 0,
                    "individual_sell": client_type.individual_sell_volume if client_type else 0,
                    "corporate_buy": client_type.corporate_buy_volume if client_type else 0,
                    "corporate_sell": client_type.corporate_sell_volume if client_type else 0,
                } if client_type else None,
                "score": {
                    "total": stock.total_score,
                    "signal": stock.signal,
                    "technical": stock.technical_score,
                    "moneyflow": stock.moneyflow_score,
                    "risk": stock.risk_score
                }
            }
        
        db.close()
        
        # Fallback to API
        data = await tsetmc_client.get_stock_data(ins_code)
        if not data:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ins_code}/score")
async def get_stock_score(ins_code: int):
    """Get stock score and analysis"""
    try:
        # Try database first
        db = SessionLocal()
        stock = db.query(Stock).filter(Stock.ins_code == ins_code).first()
        
        if stock and stock.total_score:
            db.close()
            return {
                "ins_code": ins_code,
                "symbol": stock.symbol,
                "name": stock.name,
                "price": stock.last_price,
                "change_pct": ((stock.last_price - stock.yesterday_price) / stock.yesterday_price * 100) if stock.yesterday_price else 0,
                "volume": stock.volume,
                "score": {
                    "total": stock.total_score,
                    "signal": stock.signal,
                    "technical": stock.technical_score,
                    "fundamental": stock.fundamental_score,
                    "moneyflow": stock.moneyflow_score,
                    "risk": stock.risk_score,
                    "momentum": stock.momentum_score,
                    "regime": stock.regime
                }
            }
        
        db.close()
        
        # Calculate from price history
        db = SessionLocal()
        history = db.query(PriceHistory).filter(
            PriceHistory.ins_code == ins_code
        ).order_by(PriceHistory.date.desc()).limit(100).all()
        db.close()
        
        if not history:
            raise HTTPException(status_code=404, detail="No price history found")
        
        closes = [h.close for h in history]
        highs = [h.high for h in history]
        lows = [h.low for h in history]
        volumes = [h.volume for h in history]
        
        # Calculate indicators
        ti = TechnicalIndicators(closes, highs, lows, volumes)
        result = scoring_engine.calculate_score(
            opens=closes,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )
        
        return {
            "ins_code": ins_code,
            "price": closes[0] if closes else 0,
            "score": {
                "total": result.total_score,
                "signal": result.signal.value,
                "technical": result.technical,
                "moneyflow": result.moneyflow,
                "risk": result.risk,
                "momentum": result.momentum,
                "regime": result.regime.value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ins_code}/indicators")
async def get_stock_indicators(ins_code: int):
    """Get all technical indicators for a stock"""
    try:
        db = SessionLocal()
        history = db.query(PriceHistory).filter(
            PriceHistory.ins_code == ins_code
        ).order_by(PriceHistory.date.desc()).limit(100).all()
        db.close()
        
        if not history:
            raise HTTPException(status_code=404, detail="No price history found")
        
        closes = [h.close for h in history]
        highs = [h.high for h in history]
        lows = [h.low for h in history]
        volumes = [h.volume for h in history]
        
        ti = TechnicalIndicators(closes, highs, lows, volumes)
        
        return {
            "ins_code": ins_code,
            "indicators": ti.all_indicators(),
            "signals": {
                "rsi": ti.rsi_signal().signal,
                "macd": ti.macd_signal().signal,
                "bollinger": ti.bollinger_signal().signal,
                "adx": ti.adx_signal().signal,
            },
            "scores": {
                "trend": ti.trend_score(),
                "momentum": ti.momentum_score()
            }
        }
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Filter Endpoints
# ============================================================

@app.post("/api/filter")
async def apply_filter(request: FilterRequest):
    """Apply filter to all stocks"""
    try:
        db = SessionLocal()
        query = db.query(Stock)
        
        # Apply conditions
        for condition in request.conditions:
            field = condition.field
            op = condition.operator
            value = condition.value
            
            if hasattr(Stock, field):
                if op == ">":
                    query = query.filter(getattr(Stock, field) > value)
                elif op == "<":
                    query = query.filter(getattr(Stock, field) < value)
                elif op == ">=":
                    query = query.filter(getattr(Stock, field) >= value)
                elif op == "<=":
                    query = query.filter(getattr(Stock, field) <= value)
                elif op == "==":
                    query = query.filter(getattr(Stock, field) == value)
        
        # Apply min score
        if request.min_score:
            query = query.filter(Stock.total_score >= request.min_score)
        
        # Get results
        results = query.order_by(Stock.total_score.desc()).limit(request.limit).all()
        db.close()
        
        return {
            "count": len(results),
            "results": [
                {
                    "ins_code": s.ins_code,
                    "symbol": s.symbol,
                    "name": s.name,
                    "last_price": s.last_price,
                    "change_pct": ((s.last_price - s.yesterday_price) / s.yesterday_price * 100) if s.yesterday_price else 0,
                    "volume": s.volume,
                    "score": s.total_score,
                    "signal": s.signal
                }
                for s in results
            ]
        }
    except Exception as e:
        logger.error(f"Error applying filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_stocks(q: str = Query(..., description="Search query")):
    """Search stocks by symbol or name"""
    try:
        db = SessionLocal()
        stocks = db.query(Stock).filter(
            (Stock.symbol.contains(q)) |
            (Stock.name.contains(q))
        ).limit(20).all()
        db.close()
        
        return {
            "count": len(stocks),
            "results": [
                {
                    "ins_code": s.ins_code,
                    "symbol": s.symbol,
                    "name": s.name,
                    "last_price": s.last_price,
                    "sector": s.sector
                }
                for s in stocks
            ]
        }
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/filters/presets")
async def get_preset_filters():
    """Get predefined filter presets"""
    return {
        "filters": [
            {
                "name": "مومنتوم قوی",
                "description": "سهم‌های با رشد پیوسته و حجم بالا",
                "conditions": [
                    {"field": "volume", "operator": ">", "value": 1000000},
                    {"field": "last_price", "operator": ">", "value": 0}
                ]
            },
            {
                "name": "ورود پول هوشمند",
                "description": "خرید سنگین حقوقی",
                "conditions": [
                    {"field": "volume", "operator": ">", "value": 2000000},
                    {"field": "total_score", "operator": ">", "value": 60}
                ]
            },
            {
                "name": "سهم‌های ارزان",
                "description": "pe پایین و eps بالا",
                "conditions": [
                    {"field": "pe", "operator": ">", "value": 0},
                    {"field": "pe", "operator": "<", "value": 10},
                    {"field": "eps", "operator": ">", "value": 0}
                ]
            },
            {
                "name": "سیگنال خرید",
                "description": "سهم‌های با سیگنال خرید قوی",
                "conditions": [
                    {"field": "total_score", "operator": ">", "value": 70}
                ]
            }
        ]
    }


# ============================================================
# Backtest Endpoints
# ============================================================

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest on a stock"""
    try:
        db = SessionLocal()
        history = db.query(PriceHistory).filter(
            PriceHistory.ins_code == request.ins_code
        ).order_by(PriceHistory.date.asc()).limit(request.days).all()
        db.close()
        
        if len(history) < 50:
            raise HTTPException(status_code=400, detail="Not enough price history")
        
        closes = [h.close for h in history]
        highs = [h.high for h in history]
        lows = [h.low for h in history]
        volumes = [h.volume for h in history]
        
        # Get strategy
        strategy_map = {
            "rsi": StrategyType.RSI_OVERSOLD,
            "macd": StrategyType.MACD_CROSS,
            "bollinger": StrategyType.BOLLINGER_BOUNCE,
            "ma_cross": StrategyType.MOVING_AVERAGE_CROSS,
            "momentum": StrategyType.MOMENTUM,
            "mean_reversion": StrategyType.MEAN_REVERSION,
        }
        
        strategy = strategy_map.get(request.strategy)
        if not strategy:
            raise HTTPException(status_code=400, detail="Invalid strategy")
        
        # Run backtest
        result = backtest_engine.run_backtest(
            closes, highs, lows, volumes, strategy, request.params
        )
        
        return {
            "strategy": result.strategy_name,
            "initial_capital": result.initial_capital,
            "final_capital": result.final_capital,
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "trades": [
                {
                    "entry_date": t.entry_date.isoformat(),
                    "exit_date": t.exit_date.isoformat() if t.exit_date else None,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "exit_reason": t.exit_reason
                }
                for t in result.trades
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies")
async def get_strategies():
    """Get available trading strategies"""
    return {
        "strategies": [
            StrategyLibrary.rsi_oversold(),
            StrategyLibrary.macd_cross(),
            StrategyLibrary.bollinger_bounce(),
            StrategyLibrary.ma_cross(),
            StrategyLibrary.momentum(),
            StrategyLibrary.mean_reversion(),
        ]
    }


# ============================================================
# Database Stats
# ============================================================

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    db = SessionLocal()
    
    stats = {
        "stocks": db.query(Stock).count(),
        "price_history": db.query(PriceHistory).count(),
        "shareholders": db.query(Shareholder).count(),
        "client_type": db.query(ClientTypeHistory).count(),
    }
    
    db.close()
    return stats


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
