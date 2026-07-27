from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ai.factory import get_provider
from app.ai.types import MentoriaTurn
from app.content_generation import build_edge_context, generate_and_audit
from app.db import (
    add_mentoria_turn,
    end_mentoria_session,
    fetch_node,
    fetch_node_edges_with_labels,
    fetch_roadmap_graph,
    get_connection,
    get_mentoria_turns,
    get_node_progress,
    init_db,
    mark_node_opened,
    save_enrichment_results,
    save_generated_content,
    start_mentoria_session,
    upsert_roadmap,
)
from app.embeddings import get_embedding_provider
from app.graph_pipeline import enrich_graph
from app.roadmap_parser import list_available_roadmaps, parse_roadmap

router = APIRouter(prefix="/api")


def get_db():
    conn = get_connection()
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()


class MentoriaTurnRequest(BaseModel):
    text: str


@router.get("/roadmaps")
def list_roadmaps(conn=Depends(get_db)):
    imported = {
        row[0] for row in conn.execute("SELECT DISTINCT roadmap_origin FROM nodes").fetchall()
    }
    return [{"slug": slug, "imported": slug in imported} for slug in list_available_roadmaps()]


@router.post("/roadmaps/{slug}/import")
def import_roadmap(slug: str, conn=Depends(get_db)):
    parsed = parse_roadmap(slug)
    if not parsed["nodes"]:
        raise HTTPException(404, f"Roadmap '{slug}' nao encontrado ou sem nos reais")
    upsert_roadmap(conn, parsed["nodes"], parsed["edges"])
    return {"nodes": len(parsed["nodes"]), "edges": len(parsed["edges"])}


@router.post("/roadmaps/{slug}/enrich")
def enrich_roadmap(slug: str, conn=Depends(get_db)):
    nodes, edges = fetch_roadmap_graph(conn, slug)
    if not nodes:
        raise HTTPException(404, f"Roadmap '{slug}' nao foi importado ainda")
    result = enrich_graph(nodes, edges, get_provider(), get_embedding_provider())
    save_enrichment_results(conn, result["node_types"], result["new_edges"], result["embeddings"])
    return {"nodes_classified": len(result["node_types"]), "new_edges": len(result["new_edges"])}


@router.get("/roadmaps/{slug}/graph")
def get_roadmap_graph(slug: str, conn=Depends(get_db)):
    nodes, edges = fetch_roadmap_graph(conn, slug)
    if not nodes:
        raise HTTPException(404, f"Roadmap '{slug}' nao foi importado ainda")
    type_rows = conn.execute(
        "SELECT id, node_type FROM nodes WHERE roadmap_origin = ?", (slug,)
    ).fetchall()
    node_types = {r[0]: r[1] for r in type_rows}
    out_nodes = []
    for n in nodes:
        progress = get_node_progress(conn, n["id"])
        out_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "node_type": node_types.get(n["id"]),
            "status": progress["status"],
        })
    return {"nodes": out_nodes, "edges": edges}


@router.get("/nodes/{node_id}")
def get_node_detail(node_id: str, conn=Depends(get_db)):
    node = fetch_node(conn, node_id)
    if node is None:
        raise HTTPException(404, "No nao encontrado")
    if node["node_type"] is None:
        raise HTTPException(400, "No ainda nao classificado — rode o enriquecimento do roadmap primeiro")

    if node["generated_content"] is None:
        edges, node_by_id = fetch_node_edges_with_labels(conn, node_id)
        edge_context = build_edge_context(node_id, edges, node_by_id)
        result = generate_and_audit(
            label=node["label"],
            node_type=node["node_type"],
            description_md=node["description_md"],
            edge_context=edge_context,
            ai_provider=get_provider(),
        )
        generated_content = {
            "template_usado": result.template_usado,
            "texto": result.texto,
            "auditoria": [
                {"tentativa": a.tentativa, "aprovado": a.aprovado, "motivo": a.motivo}
                for a in result.auditoria
            ],
            "status": result.status,
        }
        save_generated_content(conn, node_id, generated_content)
        node["generated_content"] = generated_content

    mark_node_opened(conn, node_id)
    progress = get_node_progress(conn, node_id)
    return {**node, "status": progress["status"]}


@router.post("/nodes/{node_id}/mentoria/start")
def start_mentoria(node_id: str, conn=Depends(get_db)):
    node = fetch_node(conn, node_id)
    if node is None or node["generated_content"] is None:
        raise HTTPException(400, "Abra o no (para gerar o conteudo) antes de iniciar a mentoria")

    session_id = start_mentoria_session(conn, node_id)
    reply = get_provider().mentoria_reply(node["generated_content"]["texto"], history=[], user_message="")
    add_mentoria_turn(conn, session_id, 0, "mentora", reply)
    return {"session_id": session_id, "turn": {"role": "mentora", "text": reply}}


@router.post("/mentoria/{session_id}/turn")
def post_mentoria_turn(session_id: str, payload: MentoriaTurnRequest, conn=Depends(get_db)):
    row = conn.execute("SELECT node_id FROM mentoria_sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Sessao de mentoria nao encontrada")
    node_id = row[0]
    node = fetch_node(conn, node_id)

    turns = get_mentoria_turns(conn, session_id)
    next_index = len(turns)
    add_mentoria_turn(conn, session_id, next_index, "usuario", payload.text)

    history = [MentoriaTurn(role=t["role"], text=t["text"]) for t in turns]
    reply = get_provider().mentoria_reply(node["generated_content"]["texto"], history=history, user_message=payload.text)
    add_mentoria_turn(conn, session_id, next_index + 1, "mentora", reply)
    return {"turn": {"role": "mentora", "text": reply}}


@router.post("/mentoria/{session_id}/end")
def end_mentoria(session_id: str, conn=Depends(get_db)):
    row = conn.execute("SELECT node_id FROM mentoria_sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Sessao de mentoria nao encontrada")
    node_id = row[0]
    node = fetch_node(conn, node_id)
    turns = get_mentoria_turns(conn, session_id)
    history = [MentoriaTurn(role=t["role"], text=t["text"]) for t in turns]

    validado, motivo = get_provider().mentoria_veredito(node["generated_content"]["texto"], history)
    end_mentoria_session(conn, session_id, node_id, validado, motivo)
    return {"encerrada": True}


@router.get("/revisao")
def get_revisao(conn=Depends(get_db)):
    rows = conn.execute(
        """
        SELECT ms.id, ms.node_id, n.label, n.roadmap_origin, ms.veredito_validado, ms.veredito_motivo, ms.started_at
        FROM mentoria_sessions ms
        JOIN nodes n ON n.id = ms.node_id
        ORDER BY ms.started_at DESC
        """
    ).fetchall()

    latest_by_node = {}
    for r in rows:
        node_id = r[1]
        if node_id in latest_by_node:
            continue
        latest_by_node[node_id] = {
            "session_id": r[0],
            "node_id": node_id,
            "label": r[2],
            "roadmap_origin": r[3],
            "veredito_validado": bool(r[4]) if r[4] is not None else None,
            "veredito_motivo": r[5],
            "started_at": r[6],
        }

    items = list(latest_by_node.values())
    items.sort(key=lambda i: (i["veredito_validado"] is True, i["started_at"]))
    return items
