#!/usr/bin/env python3
"""
Demo test DBpedia query - Không cần OpenAI API
Chỉ để kiểm tra kết nối và dữ liệu từ DBpedia
"""

from SPARQLWrapper import SPARQLWrapper, JSON
import json


def test_dbpedia_connection():
    """Test kết nối và query DBpedia"""
    print("🌍 Test kết nối DBpedia")
    print("=" * 40)

    # Khởi tạo SPARQL wrapper
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    # Query đơn giản để test
    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?city ?cityName ?country ?description
    WHERE {
        ?city a dbo:City .
        ?city rdfs:label ?cityName .
        ?city dbo:country ?country .
        ?city rdfs:comment ?description .
        FILTER(LANG(?cityName) = "en")
        FILTER(LANG(?description) = "en")
    }
    LIMIT 5
    """

    try:
        print("🔍 Đang query DBpedia...")
        sparql.setQuery(query)
        results = sparql.query().convert()

        print(
            f"✅ Kết nối thành công! Tìm thấy {len(results['results']['bindings'])} kết quả"
        )

        print("\n📋 Kết quả:")
        print("-" * 40)

        for i, result in enumerate(results["results"]["bindings"], 1):
            city_name = result["cityName"]["value"]
            country = result["country"]["value"].split("/")[-1].replace("_", " ")
            description = result["description"]["value"][:100] + "..."  # Cắt ngắn mô tả

            print(f"{i}. {city_name} ({country})")
            print(f"   Mô tả: {description}")
            print()

        return True

    except Exception as e:
        print(f"❌ Lỗi khi kết nối DBpedia: {e}")
        return False


def test_specific_city_query():
    """Test query thành phố cụ thể"""
    print("\n🏙️ Test query thành phố cụ thể")
    print("=" * 40)

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    # Query thông tin về London
    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?city ?cityName ?country ?description ?population ?area
    WHERE {
        ?city a dbo:City .
        ?city rdfs:label ?cityName .
        ?city dbo:country ?country .
        ?city rdfs:comment ?description .
        FILTER(LANG(?cityName) = "en")
        FILTER(LANG(?description) = "en")
        FILTER(CONTAINS(LCASE(?cityName), "london"))
        OPTIONAL { ?city dbo:populationTotal ?population }
        OPTIONAL { ?city dbo:areaTotal ?area }
    }
    LIMIT 1
    """

    try:
        sparql.setQuery(query)
        results = sparql.query().convert()

        if results["results"]["bindings"]:
            result = results["results"]["bindings"][0]

            print("✅ Tìm thấy thông tin về London:")
            print(f"   Tên: {result['cityName']['value']}")
            print(
                f"   Quốc gia: {result['country']['value'].split('/')[-1].replace('_', ' ')}"
            )
            print(f"   Dân số: {result.get('population', {}).get('value', 'Unknown')}")
            print(f"   Diện tích: {result.get('area', {}).get('value', 'Unknown')}")
            print(f"   Mô tả: {result['description']['value'][:200]}...")
        else:
            print("❌ Không tìm thấy thông tin về London")

        return True

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False


def main():
    """Hàm main"""
    print("🧪 Test DBpedia Connection")
    print("=" * 50)

    # Test kết nối cơ bản
    if test_dbpedia_connection():
        print("\n✅ Test kết nối DBpedia thành công!")
    else:
        print("\n❌ Test kết nối DBpedia thất bại!")
        return

    # Test query thành phố cụ thể
    if test_specific_city_query():
        print("\n✅ Test query thành phố cụ thể thành công!")
    else:
        print("\n❌ Test query thành phố cụ thể thất bại!")

    print("\n🎉 Tất cả test hoàn thành!")
    print("💡 Bây giờ bạn có thể chạy demo đầy đủ với OpenAI API")


if __name__ == "__main__":
    main()
