"""
فیلترادیوم - User Panel API
User authentication, profiles, and saved filters
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import hashlib
import secrets
from loguru import logger

from backend.models.database import (
    User, UserFilter, Alert, Stock,
    init_db, SessionLocal, get_db
)


# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    subscription_type: str
    created_at: datetime


class FilterCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    conditions: List[Dict]


class FilterResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    conditions: Dict
    is_active: bool
    created_at: datetime


class AlertCreate(BaseModel):
    ins_code: int
    alert_type: str
    condition: str
    threshold: float


class AlertResponse(BaseModel):
    id: int
    ins_code: int
    alert_type: str
    condition: str
    threshold: float
    is_active: bool
    is_triggered: bool
    triggered_at: Optional[datetime]


# Security
security = HTTPBearer()
SECRET_KEY = "filteradium-secret-key-change-in-production"


def hash_password(password: str) -> str:
    """Hash password"""
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def create_token(user_id: int) -> str:
    """Create auth token"""
    # Simple token - in production use JWT
    return f"{user_id}:{secrets.token_hex(32)}"


def verify_token(token: str) -> Optional[int]:
    """Verify token and return user_id"""
    try:
        user_id = int(token.split(":")[0])
        return user_id
    except:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# ============================================================
# User Routes
# ============================================================

def setup_user_routes(app: FastAPI):
    """Setup user panel routes"""
    
    @app.post("/api/auth/register")
    async def register(user: UserCreate):
        """Register new user"""
        db = SessionLocal()
        
        # Check if username exists
        existing = db.query(User).filter(User.username == user.username).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email exists
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create user
        new_user = User(
            username=user.username,
            email=user.email,
            password_hash=hash_password(user.password),
            subscription_type="free"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()
        
        # Generate token
        token = create_token(new_user.id)
        
        return {
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "subscription_type": new_user.subscription_type
            }
        }
    
    @app.post("/api/auth/login")
    async def login(user: UserLogin):
        """Login user"""
        db = SessionLocal()
        
        db_user = db.query(User).filter(User.username == user.username).first()
        db.close()
        
        if not db_user or db_user.password_hash != hash_password(user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_token(db_user.id)
        
        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "subscription_type": db_user.subscription_type
            }
        }
    
    @app.get("/api/auth/me")
    async def get_me(user: User = Depends(get_current_user)):
        """Get current user info"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "subscription_type": user.subscription_type,
            "created_at": user.created_at
        }
    
    # ============================================================
    # Saved Filters
    # ============================================================
    
    @app.get("/api/filters")
    async def get_my_filters(user: User = Depends(get_current_user)):
        """Get user's saved filters"""
        db = SessionLocal()
        filters = db.query(UserFilter).filter(UserFilter.user_id == user.id).all()
        db.close()
        
        return {
            "filters": [
                {
                    "id": f.id,
                    "name": f.name,
                    "description": f.description,
                    "conditions": f.conditions,
                    "is_active": f.is_active,
                    "created_at": f.created_at
                }
                for f in filters
            ]
        }
    
    @app.post("/api/filters")
    async def create_filter(filter: FilterCreate, user: User = Depends(get_current_user)):
        """Create new filter"""
        db = SessionLocal()
        
        new_filter = UserFilter(
            user_id=user.id,
            name=filter.name,
            description=filter.description,
            conditions=filter.conditions,
            is_active=True
        )
        db.add(new_filter)
        db.commit()
        db.refresh(new_filter)
        db.close()
        
        return {
            "message": "Filter created",
            "filter": {
                "id": new_filter.id,
                "name": new_filter.name,
                "conditions": new_filter.conditions
            }
        }
    
    @app.put("/api/filters/{filter_id}")
    async def update_filter(filter_id: int, filter: FilterCreate, user: User = Depends(get_current_user)):
        """Update filter"""
        db = SessionLocal()
        
        db_filter = db.query(UserFilter).filter(
            UserFilter.id == filter_id,
            UserFilter.user_id == user.id
        ).first()
        
        if not db_filter:
            db.close()
            raise HTTPException(status_code=404, detail="Filter not found")
        
        db_filter.name = filter.name
        db_filter.description = filter.description
        db_filter.conditions = filter.conditions
        db.commit()
        db.close()
        
        return {"message": "Filter updated"}
    
    @app.delete("/api/filters/{filter_id}")
    async def delete_filter(filter_id: int, user: User = Depends(get_current_user)):
        """Delete filter"""
        db = SessionLocal()
        
        db_filter = db.query(UserFilter).filter(
            UserFilter.id == filter_id,
            UserFilter.user_id == user.id
        ).first()
        
        if not db_filter:
            db.close()
            raise HTTPException(status_code=404, detail="Filter not found")
        
        db.delete(db_filter)
        db.commit()
        db.close()
        
        return {"message": "Filter deleted"}
    
    # ============================================================
    # Alerts
    # ============================================================
    
    @app.get("/api/alerts")
    async def get_my_alerts(user: User = Depends(get_current_user)):
        """Get user's alerts"""
        db = SessionLocal()
        alerts = db.query(Alert).filter(Alert.user_id == user.id).all()
        db.close()
        
        return {
            "alerts": [
                {
                    "id": a.id,
                    "ins_code": a.ins_code,
                    "alert_type": a.alert_type,
                    "condition": a.condition,
                    "threshold": a.threshold,
                    "is_active": a.is_active,
                    "is_triggered": a.is_triggered,
                    "triggered_at": a.triggered_at
                }
                for a in alerts
            ]
        }
    
    @app.post("/api/alerts")
    async def create_alert(alert: AlertCreate, user: User = Depends(get_current_user)):
        """Create new alert"""
        db = SessionLocal()
        
        new_alert = Alert(
            user_id=user.id,
            ins_code=alert.ins_code,
            alert_type=alert.alert_type,
            condition=alert.condition,
            threshold=alert.threshold,
            is_active=True
        )
        db.add(new_alert)
        db.commit()
        db.close()
        
        return {"message": "Alert created"}
    
    @app.delete("/api/alerts/{alert_id}")
    async def delete_alert(alert_id: int, user: User = Depends(get_current_user)):
        """Delete alert"""
        db = SessionLocal()
        
        db_alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user.id
        ).first()
        
        if not db_alert:
            db.close()
            raise HTTPException(status_code=404, detail="Alert not found")
        
        db.delete(db_alert)
        db.commit()
        db.close()
        
        return {"message": "Alert deleted"}
    
    # ============================================================
    # Portfolio
    # ============================================================
    
    @app.get("/api/portfolio")
    async def get_portfolio(user: User = Depends(get_current_user)):
        """Get user's portfolio (watchlist)"""
        db = SessionLocal()
        
        # Get user's active filters
        filters = db.query(UserFilter).filter(
            UserFilter.user_id == user.id,
            UserFilter.is_active == True
        ).all()
        
        # Get stocks that match filters
        portfolio = []
        for f in filters:
            conditions = f.conditions
            # Apply filter conditions
            query = db.query(Stock)
            for cond in conditions:
                field = cond.get("field")
                op = cond.get("operator")
                value = cond.get("value")
                
                if field and op and value is not None:
                    if op == ">":
                        query = query.filter(getattr(Stock, field) > value)
                    elif op == "<":
                        query = query.filter(getattr(Stock, field) < value)
                    elif op == ">=":
                        query = query.filter(getattr(Stock, field) >= value)
                    elif op == "<=":
                        query = query.filter(getattr(Stock, field) <= value)
            
            stocks = query.limit(20).all()
            for s in stocks:
                if not any(p["ins_code"] == s.ins_code for p in portfolio):
                    portfolio.append({
                        "ins_code": s.ins_code,
                        "symbol": s.symbol,
                        "name": s.name,
                        "last_price": s.last_price,
                        "change_pct": ((s.last_price - s.yesterday_price) / s.yesterday_price * 100) if s.yesterday_price else 0,
                        "volume": s.volume,
                        "filter_name": f.name
                    })
        
        db.close()
        
        return {"portfolio": portfolio}
