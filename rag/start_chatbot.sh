#!/bin/bash

# RAG Chatbot Startup Script

echo "🚀 Khởi động RAG Chatbot..."
echo "================================"

# Cài đặt dependencies nếu cần
echo "📥 Cài đặt dependencies..."
pip install -r requirements.txt

# Kiểm tra file .env
if [ ! -f ".env" ]; then
    echo "📝 Tạo file .env từ env.example..."
    cp env.example .env
    echo "✅ File .env đã được tạo. Vui lòng chỉnh sửa cấu hình nếu cần."
fi

# Kiểm tra API key
echo "🔑 Kiểm tra Gemini API key..."
if [ -f ".env" ]; then
    source .env
    if [ -z "$GEMINI_API_KEY" ]; then
        echo "⚠️  GEMINI_API_KEY chưa được cấu hình trong .env"
    else
        echo "✅ Gemini API key đã được cấu hình"
    fi
fi

# Khởi động server
echo "🌐 Khởi động RAG Chatbot server..."
echo "📍 Server sẽ chạy tại: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "================================"

python run_chatbot.py