#!/usr/bin/env python3
"""
Phishing Kit Classifier API Server
Run this script to start the FastAPI backend server.
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Phishing Kit Classifier API...")
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )