#!/usr/bin/env python3
"""
Demo đơn giản: Semantic Web + RAG + Chatbot
Sử dụng DBpedia để lấy thông tin thành phố và tạo chatbot thông minh
"""

import os
import sys
from dotenv import load_dotenv
from SPARQLWrapper import SPARQLWrapper, JSON
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()


class SimpleSemanticWebRAG:
    def __init__(self):
        """Khởi tạo hệ thống Semantic Web + RAG"""
        # Kiểm tra API key
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Lỗi: Vui lòng thiết lập OPENAI_API_KEY trong file .env")
            print("💡 Tạo file .env với nội dung: OPENAI_API_KEY=your_api_key_here")
            sys.exit(1)

        # Khởi tạo SPARQL wrapper cho DBpedia
        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.sparql.setReturnFormat(JSON)

        # Khởi tạo OpenAI components
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="gpt-3.5-turbo",
            temperature=0.7,
        )

        self.vector_store = None
        self.cities_data = []

    def query_dbpedia_cities(self, limit=10):
        """Query thông tin thành phố từ DBpedia"""
        print(f"🔍 Đang query {limit} thành phố từ DBpedia...")

        query = """
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?city ?cityName ?country ?description ?population
        WHERE {
            ?city a dbo:City .
            ?city rdfs:label ?cityName .
            ?city dbo:country ?country .
            ?city rdfs:comment ?description .
            FILTER(LANG(?cityName) = "en")
            FILTER(LANG(?description) = "en")
            OPTIONAL { ?city dbo:populationTotal ?population }
        }
        LIMIT """ + str(
            limit
        )

        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            cities = []
            for result in results["results"]["bindings"]:
                city_info = {
                    "name": result["cityName"]["value"],
                    "country": result["country"]["value"]
                    .split("/")[-1]
                    .replace("_", " "),
                    "description": result["description"]["value"],
                    "population": result.get("population", {}).get("value", "Unknown"),
                }
                cities.append(city_info)

            self.cities_data = cities
            print(f"✅ Đã lấy được {len(cities)} thành phố từ DBpedia")
            return cities

        except Exception as e:
            print(f"❌ Lỗi khi query DBpedia: {e}")
            return []

    def setup_rag(self):
        """Thiết lập RAG system"""
        if not self.cities_data:
            print("❌ Chưa có dữ liệu thành phố. Vui lòng query DBpedia trước.")
            return False

        print("🔧 Đang thiết lập RAG system...")

        # Tạo documents từ dữ liệu thành phố
        documents = []
        for city in self.cities_data:
            content = f"""
            Thành phố: {city['name']}
            Quốc gia: {city['country']}
            Mô tả: {city['description']}
            Dân số: {city['population']}
            """

            metadata = {
                "city_name": city["name"],
                "country": city["country"],
                "source": "DBpedia",
            }

            documents.append(Document(page_content=content, metadata=metadata))

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        split_docs = text_splitter.split_documents(documents)

        # Tạo vector store
        self.vector_store = Chroma.from_documents(
            documents=split_docs, embedding=self.embeddings
        )

        print("✅ RAG system đã được thiết lập thành công!")
        return True

    def chat(self, question):
        """Chat với hệ thống RAG"""
        if not self.vector_store:
            return "❌ RAG system chưa được thiết lập. Vui lòng setup trước."

        # Template prompt
        template = """
        Bạn là một trợ lý thông minh chuyên về thông tin địa lý và thành phố.
        Sử dụng thông tin sau đây để trả lời câu hỏi của người dùng.
        Nếu bạn không tìm thấy thông tin trong context, hãy nói rằng bạn không biết.
        
        Context: {context}
        
        Câu hỏi: {question}
        
        Trả lời bằng tiếng Việt:
        """

        prompt = PromptTemplate(
            template=template, input_variables=["context", "question"]
        )

        # Tạo QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": prompt},
        )

        try:
            response = qa_chain.run(question)
            return response
        except Exception as e:
            return f"❌ Lỗi khi xử lý câu hỏi: {e}"


def main():
    """Hàm main để chạy demo"""
    print("🌍 Demo: Semantic Web + RAG + Chatbot")
    print("=" * 50)

    # Khởi tạo hệ thống
    system = SimpleSemanticWebRAG()

    # Query dữ liệu từ DBpedia
    cities = system.query_dbpedia_cities(limit=15)
    if not cities:
        print("❌ Không thể lấy dữ liệu từ DBpedia. Thoát chương trình.")
        return

    # Hiển thị danh sách thành phố
    print("\n📋 Danh sách thành phố đã lấy:")
    for i, city in enumerate(cities[:5], 1):  # Chỉ hiển thị 5 thành phố đầu
        print(f"{i}. {city['name']} ({city['country']})")
    if len(cities) > 5:
        print(f"... và {len(cities) - 5} thành phố khác")

    # Thiết lập RAG
    if not system.setup_rag():
        return

    print("\n💬 Bắt đầu chat! (Gõ 'quit' để thoát)")
    print("-" * 50)

    # Chat loop
    while True:
        try:
            question = input("\n🤔 Câu hỏi của bạn: ").strip()

            if question.lower() in ["quit", "exit", "thoát"]:
                print("👋 Tạm biệt!")
                break

            if not question:
                continue

            print("🤖 Đang tìm kiếm thông tin...")
            response = system.chat(question)
            print(f"💡 Trả lời: {response}")

        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    main()
