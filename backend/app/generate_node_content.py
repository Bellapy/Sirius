import argparse
from dataclasses import asdict

from app.ai.factory import get_provider
from app.content_generation import build_edge_context, generate_and_audit
from app.db import fetch_node, fetch_node_edges_with_labels, get_connection, save_generated_content


def generate_for_node(conn, node_id: str, ai_provider) -> dict:
    node = fetch_node(conn, node_id)
    if node is None:
        raise ValueError(f"No '{node_id}' nao encontrado")
    if node["node_type"] is None:
        raise ValueError(
            f"No '{node_id}' ainda nao foi classificado (node_type nulo) — rode enrich_roadmap.py primeiro"
        )

    edges, node_by_id = fetch_node_edges_with_labels(conn, node_id)
    edge_context = build_edge_context(node_id, edges, node_by_id)

    result = generate_and_audit(
        label=node["label"],
        node_type=node["node_type"],
        description_md=node["description_md"],
        edge_context=edge_context,
        ai_provider=ai_provider,
    )

    generated_content = {
        "template_usado": result.template_usado,
        "texto": result.texto,
        "auditoria": [asdict(a) for a in result.auditoria],
        "status": result.status,
    }
    save_generated_content(conn, node_id, generated_content)
    return generated_content


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera (e audita) o conteudo de um unico no ja classificado")
    parser.add_argument("node_id", help="Id qualificado do no (ex: backend:gKTSe9yQFVbPVlLzWB0hC)")
    args = parser.parse_args()

    conn = get_connection()
    ai_provider = get_provider()
    result = generate_for_node(conn, args.node_id, ai_provider)
    conn.close()

    print(f"status: {result['status']}")
    for tentativa in result["auditoria"]:
        print(f"  tentativa {tentativa['tentativa']}: aprovado={tentativa['aprovado']} motivo={tentativa['motivo']}")
    print("\n" + result["texto"])


if __name__ == "__main__":
    main()
