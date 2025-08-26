#!/usr/bin/env python3
import os
from typing import List, Tuple

import faiss
import requests
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


FUSEKI_URL = os.environ.get("FUSEKI_URL", "http://localhost:3030/vn")
QUERY_URL = f"{FUSEKI_URL}/query"

# LLM API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


class QueryRequest(BaseModel):
    question: str


class LLMResponse(BaseModel):
    answer: str
    context_used: List[str]
    confidence: float


def query_triples_for_context() -> List[str]:
    sparql = """
    PREFIX ex: <http://example.org/vn/ontology#>

    SELECT ?new_province ?new_label ?old_province ?old_label WHERE {
    ?new_province ex:formedBy ?old_province .
    ?new_province ex:canonicalLabel ?new_label .
    ?old_province ex:canonicalLabel ?old_label .
    }
    ORDER BY ?new_label ?old_label
    """
    r = requests.get(
        QUERY_URL,
        params={"query": sparql, "format": "application/sparql-results+json"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()["results"]["bindings"]
    docs: List[str] = []
    for b in data:
        docs.append(str(b))
    return docs


class RAGIndex:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.corpus: List[str] = []

    def build(self) -> None:
        self.corpus = query_triples_for_context()
        if not self.corpus:
            self.index = None
            return
        emb = self.model.encode(
            self.corpus, convert_to_numpy=True, show_progress_bar=False
        )
        d = emb.shape[1]
        self.index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(emb)
        self.index.add(emb)

    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        if not self.index:
            return []
        q = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q)
        scores, idx = self.index.search(q, k)
        results: List[Tuple[str, float]] = []
        for i, s in zip(idx[0], scores[0]):
            if i >= 0 and i < len(self.corpus):
                results.append((self.corpus[i], float(s)))
        return results


class LLMService:
    """Service để gọi Gemini API"""

    def __init__(self):
        self.gemini_api_key = GEMINI_API_KEY

    def generate_answer(self, question: str, context: List[Tuple[str, float]]) -> str:
        """Tạo câu trả lời từ context sử dụng Gemini API"""

        if not context:
            return "Xin lỗi, tôi không tìm thấy thông tin liên quan để trả lời câu hỏi của bạn."

        # Chuẩn bị context
        context_text = self._prepare_context(context)

        return self._call_gemini(question, context_text)

    def _prepare_context(self, context: List[Tuple[str, float]]) -> str:
        return context

    def _call_gemini(self, question: str, context: str) -> str:
        """Gọi Google Gemini API"""
        if not self.gemini_api_key:
            return self._fallback_response(question, context)

        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/"
                "models/gemini-2.0-flash:generateContent"
            )

            prompt = f"""Dựa trên dữ liệu SPARQL sau về các tỉnh thành Việt Nam, hãy trả lời câu hỏi bằng tiếng Việt:

Dữ liệu (format: new_province: URI tỉnh sau sát nhập, new_label: tên tỉnh sau sát nhập, old_province: URI tỉnh trước sát nhập, old_label: tên tỉnh trước sát nhập):
{context}

Câu hỏi: {question}

Hãy phân tích dữ liệu và trả lời chính xác, đưa ra các uri liên quan nếu có:"""

            print(prompt)

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }

            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.gemini_api_key
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            result = response.json()

            if response.status_code == 200:
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text = candidate["content"]["parts"][0]["text"]
                        print(f"Extracted text: {text}")
                        return text
                    else:
                        print(f"Candidate structure: {candidate}")
                else:
                    print("No candidates found in response")

            return self._fallback_response(question, context)

        except Exception as e:
            print(f"Lỗi Gemini API: {e}")
            return self._fallback_response(question, context)

    def _fallback_response(self, question: str, context: str) -> str:
        print("Không tìm được")
        """Câu trả lời dự phòng khi không thể gọi Gemini API"""
        return f"""Dựa trên thông tin tìm được, đây là những gì liên quan đến câu hỏi "{question}":

{context}

Đây là thông tin thô từ cơ sở dữ liệu. Bạn có thể cần phân tích thêm để hiểu rõ hơn."""


app = FastAPI(title="RAG Chatbot API", description="API cho hệ thống RAG chatbot")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

rag_index = RAGIndex()
llm_service = LLMService()


@app.on_event("startup")
def startup_event() -> None:
    rag_index.build()
    print("🤖 LLM Provider: Gemini")
    if not GEMINI_API_KEY:
        print("⚠️  GEMINI_API_KEY chưa được cấu hình")
    else:
        print("✅ Gemini API key đã được cấu hình")


@app.post("/ask")
def ask(req: QueryRequest):
    # Tìm kiếm context
    # hits = rag_index.search(req.question, k=8)
    hits = query_triples_for_context()

    # Tạo câu trả lời từ LLM
    answer = llm_service.generate_answer(req.question, hits)

    return {
        "question": req.question,
        "answer": answer,
        "context": '',
        "confidence": 1,
        "llm_provider": "gemini",
    }


@app.get("/")
def read_root():
    return FileResponse("static/index.html")
