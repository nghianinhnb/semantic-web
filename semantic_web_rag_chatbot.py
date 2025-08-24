import os
import pandas as pd
from typing import List, Dict
from dotenv import load_dotenv
import streamlit as st
from SPARQLWrapper import SPARQLWrapper, JSON
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()


class DBpediaSemanticWeb:
    """Class để query DBpedia và xử lý semantic web data"""

    def __init__(self):
        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.sparql.setReturnFormat(JSON)

    def query_cities_info(self, limit: int = 10) -> List[Dict]:
        """Query thông tin về các thành phố từ DBpedia"""
        query = """
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT DISTINCT ?city ?cityName ?country ?population ?description ?area
        WHERE {
            ?city a dbo:City .
            ?city rdfs:label ?cityName .
            ?city dbo:country ?country .
            ?city rdfs:comment ?description .
            FILTER(LANG(?cityName) = "en")
            FILTER(LANG(?description) = "en")
            OPTIONAL { ?city dbo:populationTotal ?population }
            OPTIONAL { ?city dbo:areaTotal ?area }
        }
        LIMIT """ + str(
            limit
        )

        self.sparql.setQuery(query)
        results = self.sparql.query().convert()

        cities_data = []
        for result in results["results"]["bindings"]:
            city_info = {
                "city": result["city"]["value"],
                "name": result["cityName"]["value"],
                "country": result["country"]["value"].split("/")[-1].replace("_", " "),
                "description": result["description"]["value"],
                "population": result.get("population", {}).get("value", "Unknown"),
                "area": result.get("area", {}).get("value", "Unknown"),
            }
            cities_data.append(city_info)

        return cities_data

    def query_specific_city(self, city_name: str) -> Dict:
        """Query thông tin chi tiết về một thành phố cụ thể"""
        query = (
            """
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT DISTINCT ?city ?cityName ?country ?population ?description ?area ?timeZone ?elevation
        WHERE {
            ?city a dbo:City .
            ?city rdfs:label ?cityName .
            ?city dbo:country ?country .
            ?city rdfs:comment ?description .
            FILTER(LANG(?cityName) = "en")
            FILTER(LANG(?description) = "en")
            FILTER(CONTAINS(LCASE(?cityName), LCASE("""
            + f'"{city_name}"'
            + """)))
            OPTIONAL { ?city dbo:populationTotal ?population }
            OPTIONAL { ?city dbo:areaTotal ?area }
            OPTIONAL { ?city dbo:timeZone ?timeZone }
            OPTIONAL { ?city dbo:elevation ?elevation }
        }
        LIMIT 1
        """
        )

        self.sparql.setQuery(query)
        results = self.sparql.query().convert()

        if results["results"]["bindings"]:
            result = results["results"]["bindings"][0]
            return {
                "city": result["city"]["value"],
                "name": result["cityName"]["value"],
                "country": result["country"]["value"].split("/")[-1].replace("_", " "),
                "description": result["description"]["value"],
                "population": result.get("population", {}).get("value", "Unknown"),
                "area": result.get("area", {}).get("value", "Unknown"),
                "timeZone": result.get("timeZone", {}).get("value", "Unknown"),
                "elevation": result.get("elevation", {}).get("value", "Unknown"),
            }
        return None


class RAGSystem:
    """Class để xử lý RAG (Retrieval-Augmented Generation)"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="gpt-3.5-turbo",
            temperature=0.7,
        )
        self.vector_store = None

    def create_documents_from_cities(self, cities_data: List[Dict]) -> List[Document]:
        """Tạo documents từ dữ liệu thành phố cho vector store"""
        documents = []
        for city in cities_data:
            # Tạo text mô tả chi tiết về thành phố
            content = f"""
            Thành phố: {city['name']}
            Quốc gia: {city['country']}
            Mô tả: {city['description']}
            Dân số: {city['population']}
            Diện tích: {city['area']}
            """

            metadata = {
                "city_name": city["name"],
                "country": city["country"],
                "source": "DBpedia",
            }

            documents.append(Document(page_content=content, metadata=metadata))

        return documents

    def setup_vector_store(self, documents: List[Document]):
        """Thiết lập vector store từ documents"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

        split_docs = text_splitter.split_documents(documents)
        self.vector_store = Chroma.from_documents(
            documents=split_docs, embedding=self.embeddings
        )

    def query_rag(self, question: str, k: int = 3) -> str:
        """Query RAG system với câu hỏi"""
        if not self.vector_store:
            return "Vector store chưa được thiết lập. Vui lòng load dữ liệu trước."

        # Template cho prompt
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
            retriever=self.vector_store.as_retriever(search_kwargs={"k": k}),
            chain_type_kwargs={"prompt": prompt},
        )

        return qa_chain.run(question)


class SemanticWebRAGChatbot:
    """Class chính kết hợp Semantic Web + RAG + Chatbot"""

    def __init__(self):
        self.dbpedia = DBpediaSemanticWeb()
        self.rag = RAGSystem()
        self.cities_data = []

    def load_cities_data(self, limit: int = 20):
        """Load dữ liệu thành phố từ DBpedia"""
        st.info("Đang tải dữ liệu từ DBpedia...")
        self.cities_data = self.dbpedia.query_cities_info(limit)

        if self.cities_data:
            st.success(f"Đã tải {len(self.cities_data)} thành phố từ DBpedia")

            # Tạo documents và setup vector store
            documents = self.rag.create_documents_from_cities(self.cities_data)
            self.rag.setup_vector_store(documents)
            st.success("Đã thiết lập RAG system thành công!")
        else:
            st.error("Không thể tải dữ liệu từ DBpedia")

    def chat_with_city_info(self, user_question: str) -> str:
        """Chat với thông tin thành phố"""
        return self.rag.query_rag(user_question)

    def get_city_details(self, city_name: str) -> Dict:
        """Lấy thông tin chi tiết về một thành phố"""
        return self.dbpedia.query_specific_city(city_name)


def main():
    st.set_page_config(
        page_title="Semantic Web + RAG Chatbot Demo", page_icon="🌍", layout="wide"
    )

    st.title("🌍 Demo: Semantic Web + RAG + Chatbot")
    st.markdown(
        """
    Demo này kết hợp:
    - **Semantic Web**: Query DBpedia để lấy thông tin thành phố
    - **RAG**: Tạo vector database từ dữ liệu semantic web
    - **Chatbot**: Sử dụng ChatGPT API để trả lời câu hỏi
    """
    )

    # Kiểm tra API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Vui lòng thiết lập OPENAI_API_KEY trong file .env")
        st.code("OPENAI_API_KEY=your_api_key_here")
        return

    # Khởi tạo chatbot
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = SemanticWebRAGChatbot()

    chatbot = st.session_state.chatbot

    # Sidebar để load dữ liệu
    with st.sidebar:
        st.header("⚙️ Cài đặt")

        if st.button("🔄 Load dữ liệu từ DBpedia"):
            with st.spinner("Đang tải dữ liệu..."):
                chatbot.load_cities_data(limit=15)

        if chatbot.cities_data:
            st.success(f"✅ Đã load {len(chatbot.cities_data)} thành phố")

            # Hiển thị danh sách thành phố
            st.subheader("📋 Danh sách thành phố")
            city_names = [city["name"] for city in chatbot.cities_data]
            selected_city = st.selectbox("Chọn thành phố để xem chi tiết:", city_names)

            if selected_city:
                city_details = chatbot.get_city_details(selected_city)
                if city_details:
                    st.json(city_details)

    # Main chat interface
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("💬 Chat với thông tin thành phố")

        # Chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Hỏi về thông tin thành phố..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.write(prompt)

            # Get bot response
            with st.chat_message("assistant"):
                with st.spinner("Đang tìm kiếm thông tin..."):
                    response = chatbot.chat_with_city_info(prompt)
                    st.write(response)

                    # Add assistant response to chat history
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": response}
                    )

    with col2:
        st.header("📊 Thống kê")

        if chatbot.cities_data:
            # Tạo DataFrame để hiển thị
            df = pd.DataFrame(chatbot.cities_data)

            st.subheader("🌍 Thành phố theo quốc gia")
            country_counts = df["country"].value_counts()
            st.bar_chart(country_counts)

            st.subheader("📈 Dân số (nếu có)")
            # Lọc dữ liệu có population
            pop_data = df[df["population"] != "Unknown"].copy()
            if not pop_data.empty:
                pop_data["population"] = pd.to_numeric(
                    pop_data["population"], errors="coerce"
                )
                pop_data = pop_data.dropna(subset=["population"])
                if not pop_data.empty:
                    st.bar_chart(pop_data.set_index("name")["population"])
                else:
                    st.info("Không có dữ liệu dân số")
            else:
                st.info("Không có dữ liệu dân số")

        # Gợi ý câu hỏi
        st.subheader("💡 Gợi ý câu hỏi")
        suggested_questions = [
            "Thành phố nào có dân số lớn nhất?",
            "Kể cho tôi về thành phố London",
            "Những thành phố nào thuộc về Đức?",
            "Thành phố nào có diện tích lớn nhất?",
            "Mô tả về khí hậu của các thành phố",
        ]

        for question in suggested_questions:
            if st.button(question, key=question):
                st.session_state.chat_history.append(
                    {"role": "user", "content": question}
                )
                with st.chat_message("user"):
                    st.write(question)

                with st.chat_message("assistant"):
                    with st.spinner("Đang tìm kiếm..."):
                        response = chatbot.chat_with_city_info(question)
                        st.write(response)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": response}
                        )


if __name__ == "__main__":
    main()
