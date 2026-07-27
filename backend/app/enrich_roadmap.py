import argparse

from app.ai.factory import get_provider
from app.db import fetch_roadmap_graph, get_connection, init_db, save_enrichment_results
from app.embeddings import get_embedding_provider
from app.graph_pipeline import enrich_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Roda o pipeline de enriquecimento sobre um roadmap ja importado")
    parser.add_argument("slug", help="Slug do roadmap ja importado (ver import_roadmap.py)")
    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)
    nodes, edges = fetch_roadmap_graph(conn, args.slug)
    if not nodes:
        print(f"Nenhum no encontrado para '{args.slug}' — rode import_roadmap.py primeiro")
        return

    ai_provider = get_provider()
    embedding_provider = get_embedding_provider()

    result = enrich_graph(nodes, edges, ai_provider, embedding_provider)
    save_enrichment_results(conn, result["node_types"], result["new_edges"], result["embeddings"])
    conn.close()

    from collections import Counter
    counts = Counter(result["node_types"].values())
    print(
        f"Enriquecido '{args.slug}': {len(nodes)} nos classificados ({dict(counts)}), "
        f"{len(result['new_edges'])} novas arestas inferidas"
    )


if __name__ == "__main__":
    main()
