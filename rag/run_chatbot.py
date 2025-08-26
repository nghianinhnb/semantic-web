#!/usr/bin/env python3
"""
Script để chạy RAG Chatbot server
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Cấu hình server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Khởi động RAG Chatbot server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Auto-reload: {reload}")
    print(f"🌐 Web UI: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print("=" * 50)
    
    # Chạy server
    uvicorn.run(
        "rag_service:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
