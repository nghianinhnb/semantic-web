#!/usr/bin/env python3
"""
Merge provinces RDF (from DBpedia) with a CSV mapping of old -> new provinces to produce a merged RDF graph.

Output triples:
  - ex:formedBy(newProvince, oldProvince)
  - ex:mergedInto(oldProvince, newProvince)
  - ex:canonicalLabel for canonicalized plain labels (best-effort)
"""

import csv
import os
from typing import Dict, List, Tuple, Optional

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef


EX = Namespace("http://example.org/vn/ontology#")


def load_provinces_graph(path: str) -> Graph:
    g = Graph()
    g.parse(path, format="turtle")
    return g


def build_label_index(g: Graph) -> Dict[str, URIRef]:
    label_to_uri: Dict[str, URIRef] = {}
    for s, p, o in g.triples((None, RDFS.label, None)):
        if isinstance(o, Literal):
            key = str(o).strip().lower()
            if key not in label_to_uri:
                label_to_uri[key] = s
    return label_to_uri


def parse_mapping_csv(path: str) -> List[Tuple[str, str]]:
    """
    Returns list of (old_label, new_label) pairs.
    Supports CSV header variations and trims header/key whitespace.
    Expects columns: new_province, old_province
    old_province may contain multiple labels separated by '|'.
    """
    mappings: List[Tuple[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Normalize fieldnames to trimmed lowercase for lookup
        field_map: Dict[str, str] = {}
        for name in reader.fieldnames or []:
            field_map[name] = name
        
        def get_cell(row: Dict[str, str], key: str) -> str:
            # Try exact key, trimmed key, and lowercase-trimmed key
            if key in row:
                return row.get(key) or ""
            trimmed = key.strip()
            if trimmed in row:
                return row.get(trimmed) or ""
            for k in row.keys():
                if k.strip().lower() == trimmed.lower():
                    return row.get(k) or ""
            return ""

        for raw_row in reader:
            # Build a trimmed-key row view
            row: Dict[str, str] = { (k.strip() if isinstance(k, str) else k): v for k, v in raw_row.items() }

            new_label = (get_cell(row, "new_province") or "").strip()
            old_field = (get_cell(row, "old_province") or "").strip()
            if not new_label or not old_field:
                continue
            for old_part in old_field.split("|"):
                old_label = old_part.strip()
                if old_label:
                    mappings.append((old_label, new_label))
    return mappings


def merge_graph(prov_graph: Graph, mappings: List[Tuple[str, str]]) -> Graph:
    merged = Graph()
    merged.bind("ex", EX)
    merged.bind("rdfs", RDFS)

    label_index = build_label_index(prov_graph)

    def resolve(label: str) -> Optional[URIRef]:
        key = label.strip().lower()
        return label_index.get(key)

    for old_label, new_label in mappings:
        old_uri = resolve(old_label)
        new_uri = resolve(new_label)

        # If new label not found in DBpedia (e.g., Vietnamese), mint a local URI
        if new_uri is None:
            slug = (
                new_label.strip().lower()
                .replace(" ", "-")
                .replace("đ", "d")
                .replace("Đ", "D")
            )
            new_uri = URIRef(f"http://example.org/vn/entity/{slug}")
            merged.add((new_uri, RDF.type, EX.Province))
            merged.add((new_uri, RDFS.label, Literal(new_label)))
            merged.add((new_uri, EX.canonicalLabel, Literal(new_label)))

        if old_uri is None:
            # Skip if we cannot resolve old label to DBpedia entity
            continue

        if (old_uri, RDF.type, None) not in merged:
            merged.add((old_uri, RDF.type, EX.Province))
            merged.add((old_uri, EX.canonicalLabel, Literal(old_label)))

        merged.add((new_uri, EX.formedBy, old_uri))
        merged.add((old_uri, EX.mergedInto, new_uri))

    return merged


def main() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    prov_path = os.path.join(base_dir, "data", "provinces.ttl")
    mapping_path = os.path.join(base_dir, "data", "mapping.csv")
    output_path = os.path.join(base_dir, "data", "merged.ttl")

    prov_graph = load_provinces_graph(prov_path)
    mappings = parse_mapping_csv(mapping_path)
    merged_graph = merge_graph(prov_graph, mappings)
    merged_graph.serialize(destination=output_path, format="turtle")
    print(f"Wrote merged graph with {len(merged_graph)} triples -> {output_path}")


if __name__ == "__main__":
    main()


