#!/usr/bin/env python3
"""
فیلترادیوم - Run Script
Start the Filteradium server
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting فیلترادیوم server...")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🌐 Main: http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
