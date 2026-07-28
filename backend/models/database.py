"""
فیلترادیوم - Database Models
SQLAlchemy models for data storage
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """Stock information"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, unique=True, index=True)
    symbol = Column(String(20), index=True)
    name = Column(String(100))
    sector = Column(String(100))
    market_type = Column(Integer)
    
    # Latest price data
    last_price = Column(Float)
    close_price = Column(Float)
    first_price = Column(Float)
    yesterday_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Float)
    value = Column(Float)
    
    # Score data
    total_score = Column(Float)
    signal = Column(String(20))
    technical_score = Column(Float)
    fundamental_score = Column(Float)
    moneyflow_score = Column(Float)
    risk_score = Column(Float)
    momentum_score = Column(Float)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class PriceHistory(Base):
    """Price history"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    value = Column(Float)
    
    class Meta:
        unique_together = ("ins_code", "date")


class ClientTypeHistory(Base):
    """Client type history"""
    __tablename__ = "client_type_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    
    individual_buy_count = Column(Integer)
    individual_sell_count = Column(Integer)
    individual_buy_volume = Column(Float)
    individual_sell_volume = Column(Float)
    corporate_buy_count = Column(Integer)
    corporate_sell_count = Column(Integer)
    corporate_buy_volume = Column(Float)
    corporate_sell_volume = Column(Float)


class ScoreHistory(Base):
    """Score history"""
    __tablename__ = "score_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    
    total_score = Column(Float)
    signal = Column(String(20))
    technical = Column(Float)
    fundamental = Column(Float)
    moneyflow = Column(Float)
    risk = Column(Float)
    momentum = Column(Float)
    regime = Column(String(20))


class UserFilter(Base):
    """User saved filters"""
    __tablename__ = "user_filters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True)
    name = Column(String(100))
    conditions = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    """Price/Score alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True)
    ins_code = Column(Integer, index=True)
    
    alert_type = Column(String(20))  # price, score, signal
    condition = Column(String(10))  # >, <, ==
    threshold = Column(Float)
    
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
DATABASE_URL = "sqlite:///./data/filteradium.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
