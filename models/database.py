"""
Database Models - SQLAlchemy models for TSETMC data
"""
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, JSON, Boolean,
    ForeignKey, Index, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()


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
    
    # Fundamental
    eps = Column(Float)
    pe = Column(Float)
    base_volume = Column(Float)
    capital = Column(Float)
    
    # Latest price
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
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="stock")
    client_type_history = relationship("ClientTypeHistory", back_populates="stock")
    shareholder_snapshots = relationship("ShareholderSnapshot", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock {self.symbol}: {self.last_price}>"


class PriceHistory(Base):
    """Historical daily price data"""
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
    
    stock = relationship("Stock", back_populates="price_history")
    
    __table_args__ = (
        Index("ix_price_stock_date", "ins_code", "date", unique=True),
    )


class ShareholderSnapshot(Base):
    """Shareholder snapshot"""
    __tablename__ = "shareholder_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    data = Column(JSON)
    
    stock = relationship("Stock", back_populates="shareholder_snapshots")
    
    __table_args__ = (
        Index("ix_sh_stock_date", "ins_code", "date", unique=True),
    )


class ClientTypeHistory(Base):
    """Client type history (حقیقی/حقوقی)"""
    __tablename__ = "client_type_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, ForeignKey("stocks.ins_code"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    
    individual_buy_count = Column(Integer)
    individual_sell_count = Column(Integer)
    individual_buy_volume = Column(Float)
    individual_sell_volume = Column(Float)
    
    corporate_buy_count = Column(Integer)
    corporate_sell_count = Column(Integer)
    corporate_buy_volume = Column(Float)
    corporate_sell_volume = Column(Float)
    
    stock = relationship("Stock", back_populates="client_type_history")
    
    __table_args__ = (
        Index("ix_ct_stock_date", "ins_code", "date", unique=True),
    )


class OrderBookSnapshot(Base):
    """Order book snapshot"""
    __tablename__ = "order_book_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    data = Column(JSON)
    total_demand = Column(Float)
    total_supply = Column(Float)


class MarketOverview(Base):
    """Market overview snapshot"""
    __tablename__ = "market_overview"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    data = Column(JSON)


class UpdateLog(Base):
    """Update log"""
    __tablename__ = "update_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    update_type = Column(String(20))  # full, daily, manual
    stocks_updated = Column(Integer)
    status = Column(String(20))  # success, failed
    error_message = Column(Text)


# Database setup
from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./data/filteradium.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
