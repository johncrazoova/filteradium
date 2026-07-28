"""
فیلترادیوم - Database Models
SQLAlchemy models for all TSETMC data including shareholders and history
"""

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, JSON, Boolean, 
    ForeignKey, Index, Text, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()


class MarketType(enum.Enum):
    """Market type enum"""
    MAIN = 1
    SECONDARY = 2
    THIRD = 3
    OPTION = 4


class SignalType(enum.Enum):
    """Signal type enum"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


# ============================================================
# Instrument Models
# ============================================================

class Stock(Base):
    """Stock/Instrument information"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, unique=True, index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    name = Column(String(100))
    sector = Column(String(100))
    sector_code = Column(String(20))
    market_type = Column(Integer)
    
    # Fundamental data
    eps = Column(Float)
    pe = Column(Float)
    base_volume = Column(Float)
    capital = Column(Float)
    
    # Latest price data
    last_price = Column(Float)
    close_price = Column(Float)
    first_price = Column(Float)
    yesterday_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Float)
    value = Column(Float)
    upper_limit = Column(Float)
    lower_limit = Column(Float)
    
    # Score data
    total_score = Column(Float)
    signal = Column(String(20))
    technical_score = Column(Float)
    fundamental_score = Column(Float)
    moneyflow_score = Column(Float)
    risk_score = Column(Float)
    momentum_score = Column(Float)
    regime = Column(String(20))
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="stock")
    client_type_history = relationship("ClientTypeHistory", back_populates="stock")
    shareholder_snapshots = relationship("ShareholderSnapshot", back_populates="stock")
    score_history = relationship("ScoreHistory", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock {self.symbol}: {self.last_price}>"


# ============================================================
# Price History Models
# ============================================================

class PriceHistory(Base):
    """Historical daily price data (سابقه)"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    last = Column(Float)
    volume = Column(Float)
    value = Column(Float)
    change = Column(Float)
    change_pct = Column(Float)
    trade_count = Column(Integer)
    
    # Relationships
    stock = relationship("Stock", back_populates="price_history")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_price_history_stock_date", "ins_code", "date", unique=True),
    )
    
    def __repr__(self):
        return f"<PriceHistory {self.date}: {self.close}>"


# ============================================================
# Shareholder Models (سهام‌داران)
# ============================================================

class Shareholder(Base):
    """Shareholder information"""
    __tablename__ = "shareholders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    shareholder_name = Column(String(200), nullable=False)
    
    # Shareholding info
    shares = Column(Float)
    percentage = Column(Float)
    change = Column(Float)
    change_type = Column(Integer)  # 0=no change, 1=increase, -1=decrease
    
    # Metadata
    last_date = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", backref="shareholders")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_shareholder_stock_name", "ins_code", "shareholder_name", unique=True),
    )
    
    def __repr__(self):
        return f"<Shareholder {self.shareholder_name}: {self.percentage}%>"


class ShareholderSnapshot(Base):
    """Shareholder snapshot over time"""
    __tablename__ = "shareholder_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    
    # Snapshot data
    data = Column(JSON)  # Store full shareholder data as JSON
    
    # Relationships
    stock = relationship("Stock", back_populates="shareholder_snapshots")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_shareholder_snapshot_stock_date", "ins_code", "date", unique=True),
    )


class ShareholderHistory(Base):
    """Shareholder history (تاریخچه سهام‌داران)"""
    __tablename__ = "shareholder_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    shareholder_name = Column(String(200), nullable=False)
    
    # Historical data
    shares = Column(Float)
    percentage = Column(Float)
    change = Column(Float)
    
    # Unique constraint
    __table_args__ = (
        Index("ix_shareholder_history_stock_date_name", "ins_code", "date", "shareholder_name", unique=True),
    )


# ============================================================
# Client Type Models (حقیقی/حقوقی)
# ============================================================

class ClientTypeHistory(Base):
    """Client type history (تاریخچه حقیقی/حقوقی)"""
    __tablename__ = "client_type_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    
    # Individual (حقیقی)
    individual_buy_count = Column(Integer)
    individual_sell_count = Column(Integer)
    individual_buy_volume = Column(Float)
    individual_sell_volume = Column(Float)
    
    # Corporate (حقوقی)
    corporate_buy_count = Column(Integer)
    corporate_sell_count = Column(Integer)
    corporate_buy_volume = Column(Float)
    corporate_sell_volume = Column(Float)
    
    # Calculated fields
    buy_sell_ratio = Column(Float)
    net_buy = Column(Float)
    
    # Relationships
    stock = relationship("Stock", back_populates="client_type_history")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_client_type_history_stock_date", "ins_code", "date", unique=True),
    )


# ============================================================
# Order Book Models (بهترین عرضه/تقاضا)
# ============================================================

class OrderBookSnapshot(Base):
    """Order book snapshot"""
    __tablename__ = "order_book_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Order book data
    data = Column(JSON)  # Store full order book as JSON
    
    # Summary
    total_demand = Column(Float)
    total_supply = Column(Float)
    demand_supply_ratio = Column(Float)


# ============================================================
# Score Models
# ============================================================

class ScoreHistory(Base):
    """Score history over time"""
    __tablename__ = "score_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    
    # Scores
    total_score = Column(Float)
    signal = Column(String(20))
    technical = Column(Float)
    fundamental = Column(Float)
    moneyflow = Column(Float)
    risk = Column(Float)
    momentum = Column(Float)
    regime = Column(String(20))
    
    # Relationships
    stock = relationship("Stock", back_populates="score_history")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_score_history_stock_date", "ins_code", "date", unique=True),
    )


# ============================================================
# Indicator Models
# ============================================================

class IndicatorSnapshot(Base):
    """Indicator snapshot"""
    __tablename__ = "indicator_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Indicator values
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    adx = Column(Float)
    plus_di = Column(Float)
    minus_di = Column(Float)
    atr_14 = Column(Float)
    cci_20 = Column(Float)
    mfi_14 = Column(Float)
    stochastic_k = Column(Float)
    stochastic_d = Column(Float)
    obv = Column(Float)
    vwap = Column(Float)


# ============================================================
# User Models
# ============================================================

class User(Base):
    """User account"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(200))
    
    # Subscription
    subscription_type = Column(String(20), default="free")  # free, basic, pro, enterprise
    subscription_expires = Column(DateTime)
    
    # Settings
    telegram_id = Column(String(50))
    notifications_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserFilter(Base):
    """User saved filters"""
    __tablename__ = "user_filters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    conditions = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    """Price/Score alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True)
    
    # Alert conditions
    alert_type = Column(String(20))  # price, score, signal, volume
    condition = Column(String(10))  # >, <, ==, cross_above, cross_below
    threshold = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)
    triggered_value = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# Sector Models
# ============================================================

class Sector(Base):
    """Sector/Industry information"""
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_code = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    
    # Market data
    total_market_cap = Column(Float)
    total_volume = Column(Float)
    total_value = Column(Float)
    
    # Performance
    avg_change = Column(Float)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# Database Setup
# ============================================================

from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./data/filteradium.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database with all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
