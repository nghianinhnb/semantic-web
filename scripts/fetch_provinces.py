#!/usr/bin/env python3
"""
Fetch Vietnamese provinces from DBpedia using SPARQL and write a minimal RDF Turtle file.

Query:
  PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  PREFIX yago: <http://dbpedia.org/class/yago/>

  SELECT DISTINCT ?province ?provinceLabel WHERE {
    ?province rdf:type yago:WikicatProvincesOfVietnam .
    ?province rdfs:label ?provinceLabel .
    FILTER (lang(?provinceLabel) = "en")
  }
"""

import os
from typing import List, Tuple

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON


DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"


def fetch_provinces() -> List[Tuple[str, str]]:
    sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(
        """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX yago: <http://dbpedia.org/class/yago/>

        SELECT DISTINCT ?province ?provinceLabel
        WHERE {
          ?province rdf:type yago:WikicatProvincesOfVietnam .
          ?province rdfs:label ?provinceLabel .
          FILTER (lang(?provinceLabel) = "en")
        }
        """
    )
    results = sparql.query().convert()
    provinces: List[Tuple[str, str]] = []
    for binding in results["results"]["bindings"]:
        uri = binding["province"]["value"]
        label = binding["provinceLabel"]["value"]
        provinces.append((uri, label))
    return provinces


def write_turtle(destination_path: str, provinces: List[Tuple[str, str]]) -> None:
    g = Graph()
    ex = Namespace("http://example.org/vn/ontology#")
    g.bind("rdfs", RDFS)
    g.bind("ex", ex)

    province_class = ex.Province
    g.add((province_class, RDF.type, RDFS.Class))
    g.add((province_class, RDFS.label, Literal("Province")))

    for uri, label in provinces:
        s = URIRef(uri)
        g.add((s, RDF.type, province_class))
        g.add((s, RDFS.label, Literal(label, lang="en")))

    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    g.serialize(destination=destination_path, format="turtle")


def main() -> None:
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "provinces.ttl"))
    provinces = fetch_provinces()
    write_turtle(output_path, provinces)
    print(f"Wrote {len(provinces)} provinces to {output_path}")


if __name__ == "__main__":
    main()


