#!/usr/bin/env python3
import uvicorn

if __name__ == "__main__":
    print("Starting Phishing Kit Classifier API...")
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )