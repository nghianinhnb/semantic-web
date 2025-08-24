# 🌍 Demo: Semantic Web + RAG + Chatbot

Demo này kết hợp Semantic Web, RAG (Retrieval-Augmented Generation) và Chatbot để tạo một hệ thống thông minh trả lời câu hỏi về thông tin thành phố.

## 🚀 Tính năng

- **Semantic Web**: Query DBpedia để lấy thông tin thành phố qua SPARQL
- **RAG**: Tạo vector database từ dữ liệu semantic web
- **Chatbot**: Sử dụng ChatGPT API để trả lời câu hỏi thông minh
- **Web Interface**: Giao diện Streamlit đẹp mắt và dễ sử dụng

## 📋 Yêu cầu

- Python 3.8+
- OpenAI API Key
- Kết nối internet để truy cập DBpedia

## 🛠️ Cài đặt

1. **Clone repository**:
```bash
git clone <repository-url>
cd semantic_web
```

2. **Cài đặt dependencies**:
```bash
pip install -r requirements.txt
```

3. **Thiết lập API Key**:
```bash
# Tạo file .env
cp env_example.txt .env
# Chỉnh sửa file .env và thêm OpenAI API Key của bạn
```

4. **Chạy demo**:
```bash
streamlit run semantic_web_rag_chatbot.py
```

## 🎯 Cách sử dụng

1. **Load dữ liệu**: Nhấn nút "Load dữ liệu từ DBpedia" trong sidebar
2. **Chat**: Đặt câu hỏi về thông tin thành phố trong chat interface
3. **Xem thống kê**: Kiểm tra biểu đồ và thống kê trong sidebar
4. **Gợi ý**: Sử dụng các câu hỏi gợi ý có sẵn

## 🔍 Ví dụ câu hỏi

- "Thành phố nào có dân số lớn nhất?"
- "Kể cho tôi về thành phố London"
- "Những thành phố nào thuộc về Đức?"
- "Thành phố nào có diện tích lớn nhất?"

## 🏗️ Kiến trúc

### 1. DBpediaSemanticWeb
- Query DBpedia qua SPARQL endpoint
- Lấy thông tin thành phố: tên, quốc gia, dân số, mô tả, diện tích
- Hỗ trợ query chi tiết cho từng thành phố

### 2. RAGSystem
- Tạo embeddings từ dữ liệu semantic web
- Xây dựng vector store với Chroma
- Retrieval-Augmented Generation với ChatGPT

### 3. SemanticWebRAGChatbot
- Kết hợp tất cả components
- Giao diện Streamlit
- Chat history và thống kê

## 📊 Dữ liệu

Demo sử dụng DBpedia - một knowledge base lớn được trích xuất từ Wikipedia. Dữ liệu bao gồm:
- Thông tin thành phố từ khắp thế giới
- Mô tả chi tiết bằng tiếng Anh
- Thông tin dân số, diện tích, múi giờ

## 🔧 Tùy chỉnh

Bạn có thể tùy chỉnh demo bằng cách:
- Thay đổi SPARQL query để lấy dữ liệu khác
- Điều chỉnh prompt template
- Thêm các loại dữ liệu semantic web khác
- Tùy chỉnh giao diện Streamlit

## 📝 Lưu ý

- Cần có OpenAI API Key hợp lệ
- Kết nối internet ổn định để truy cập DBpedia
- Lần đầu load dữ liệu có thể mất vài phút
