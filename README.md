# Dự án RAG + Semantic Web (DBpedia + Silk + Jena)

## Cài đặt

### Dependencies
```bash
# Python dependencies
pip install rdflib SPARQLWrapper requests

# Docker (nếu chưa có)
# sudo apt install docker.io docker-compose
```

## Chạy

### 1. Lấy dữ liệu DBpedia
```bash
python scripts/fetch_provinces.py
```

### 2. Hợp nhất RDF
```bash
python scripts/merge_rdf.py
```

### 3. Khởi động Fuseki
```bash
docker compose up -d
```

### 4. Nạp dữ liệu
```bash
bash scripts/load_to_fuseki.sh
```

### 5. Truy vấn SPARQL
Truy cập: `http://localhost:3030/vn/query`

Query tỉnh mới và số tỉnh cũ gộp vào:

```sparql
PREFIX ex: <http://example.org/vn/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?new_province ?new_label (COUNT(?old_province) AS ?old_count) WHERE {
  ?new_province ex:formedBy ?old_province .
  ?new_province rdfs:label ?new_label .
}
GROUP BY ?new_province ?new_label
ORDER BY DESC(?old_count) ?new_label
```

Query tỉnh cũ -> tỉnh mới:

```sparql
PREFIX ex: <http://example.org/vn/ontology#>
SELECT ?old_label ?new_label WHERE {
  ?old_province ex:mergedInto ?new_province .
  ?old_province ex:canonicalLabel ?old_label .
  ?new_province ex:canonicalLabel ?new_label .
}
ORDER BY ?new_label ?old_label
```


### 6. RAG Service (tùy chọn)
```bash
cd rag
./start_chatbot.sh
```

## Cấu trúc
- `data/mapping.csv` - Mapping tỉnh cũ -> mới
- `data/merged.ttl` - RDF gộp cuối cùng
- `scripts/` - Script xử lý
- `rag/` - RAG service