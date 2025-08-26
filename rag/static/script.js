class RAGChatbot {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.status = document.getElementById('status');
        
        this.setupEventListeners();
        this.apiUrl = '/ask'; // API endpoint của RAG service
    }
    
    setupEventListeners() {
        // Gửi tin nhắn khi nhấn Enter
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Gửi tin nhắn khi nhấn nút gửi
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Focus vào input khi trang load
        this.messageInput.focus();
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Hiển thị tin nhắn của user
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        // Hiển thị loading
        this.showLoading();
        
        try {
            // Gọi API RAG
            const response = await this.callRAGAPI(message);
            this.hideLoading();
            
            // Hiển thị kết quả
            this.displayRAGResponse(response);
            
        } catch (error) {
            this.hideLoading();
            this.showError('Có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại.');
            console.error('Error:', error);
        }
    }
    
    async callRAGAPI(question) {
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    displayRAGResponse(response) {
        const { question, answer, context, confidence, llm_provider } = response;
        
        // Hiển thị câu trả lời từ LLM
        let responseText = `**🤖 Câu trả lời:**\n${answer}\n\n`;
        
        this.addMessage(responseText, 'bot');
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Xử lý text với markdown đơn giản
        const formattedText = this.formatText(text);
        contentDiv.innerHTML = formattedText;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll xuống tin nhắn mới nhất
        this.scrollToBottom();
    }
    
    formatText(text) {
        // Thay thế \n thành <br>
        let formatted = text.replace(/\n/g, '<br>');
        
        // Thay thế **text** thành <strong>text</strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Thay thế *text* thành <em>text</em>
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        return formatted;
    }
    
    showLoading() {
        this.status.innerHTML = '<span class="loading"></span>Đang xử lý câu hỏi...';
        this.sendButton.disabled = true;
        this.messageInput.disabled = true;
    }
    
    hideLoading() {
        this.status.textContent = '';
        this.sendButton.disabled = false;
        this.messageInput.disabled = false;
        this.messageInput.focus();
    }
    
    showError(message) {
        this.addMessage(`❌ ${message}`, 'bot');
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Khởi tạo chatbot khi trang load xong
document.addEventListener('DOMContentLoaded', () => {
    new RAGChatbot();
});
