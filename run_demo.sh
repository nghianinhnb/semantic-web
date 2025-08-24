#!/bin/bash

echo "🌍 Demo: Semantic Web + RAG + Chatbot"
echo "======================================"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 không được tìm thấy. Vui lòng cài đặt Python 3.8+"
    exit 1
fi

# Kiểm tra pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 không được tìm thấy. Vui lòng cài đặt pip"
    exit 1
fi

echo "✅ Python và pip đã sẵn sàng"

# Cài đặt dependencies
echo "📦 Đang cài đặt dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Lỗi khi cài đặt dependencies"
    exit 1
fi

echo "✅ Dependencies đã được cài đặt"

# Kiểm tra file .env
if [ ! -f ".env" ]; then
    echo "⚠️  File .env không tồn tại"
    echo "📝 Tạo file .env từ template..."
    cp env_example.txt .env
    echo "🔑 Vui lòng chỉnh sửa file .env và thêm OpenAI API Key của bạn"
    echo "💡 Sau đó chạy lại script này"
    exit 1
fi

# Kiểm tra API key
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OpenAI API Key chưa được thiết lập"
    echo "🔑 Vui lòng chỉnh sửa file .env và thêm OpenAI API Key hợp lệ"
    exit 1
fi

echo "✅ OpenAI API Key đã được thiết lập"

# Chọn chế độ chạy
echo ""
echo "🎯 Chọn chế độ chạy:"
echo "1. Demo đơn giản (Terminal)"
echo "2. Demo đầy đủ (Web Interface)"
echo "3. Thoát"
echo ""

read -p "Nhập lựa chọn (1-3): " choice

case $choice in
    1)
        echo "🚀 Chạy demo đơn giản..."
        python3 simple_demo.py
        ;;
    2)
        echo "🚀 Chạy demo đầy đủ với Streamlit..."
        echo "🌐 Mở trình duyệt tại: http://localhost:8501"
        streamlit run semantic_web_rag_chatbot.py
        ;;
    3)
        echo "👋 Tạm biệt!"
        exit 0
        ;;
    *)
        echo "❌ Lựa chọn không hợp lệ"
        exit 1
        ;;
esac
