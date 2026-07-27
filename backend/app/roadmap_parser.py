import json
from pathlib import Path

from app.config import ROADMAPS_DIR

REAL_NODE_TYPES = {"topic", "subtopic"}


def list_available_roadmaps() -> list[str]:
    if not ROADMAPS_DIR.exists():
        return []
    return sorted(
        p.name for p in ROADMAPS_DIR.iterdir()
        if p.is_dir() and (p / f"{p.name}.json").exists()
    )


def _load_content_by_node_id(content_dir: Path) -> dict[str, str]:
    by_id = {}
    if not content_dir.exists():
        return by_id
    for f in content_dir.glob("*.md"):
        if "@" not in f.stem:
            continue
        node_id = f.stem.rsplit("@", 1)[1]
        by_id[node_id] = f.read_text(encoding="utf-8")
    return by_id


def parse_roadmap(slug: str) -> dict:
    """Parse a roadmap.sh roadmap directory into our nodes/edges schema.

    Only 'topic' and 'subtopic' react-flow nodes are real graph nodes —
    other types (section, vertical, paragraph, title, button, legend,
    label) are pure layout decoration and are discarded, along with any
    edge touching them.
    """
    roadmap_dir = ROADMAPS_DIR / slug
    json_path = roadmap_dir / f"{slug}.json"
    raw = json.loads(json_path.read_text(encoding="utf-8"))

    content_by_id = _load_content_by_node_id(roadmap_dir / "content")

    real_ids: set[str] = set()
    nodes = []
    for n in raw.get("nodes", []):
        if n.get("type") not in REAL_NODE_TYPES:
            continue
        label = (n.get("data") or {}).get("label", "").strip()
        if not label:
            continue
        raw_id = n["id"]
        real_ids.add(raw_id)
        qualified_id = f"{slug}:{raw_id}"
        nodes.append({
            "id": qualified_id,
            "label": label,
            "roadmap_origin": slug,
            "description_md": content_by_id.get(raw_id),
        })

    edges = []
    seen = set()
    for e in raw.get("edges", []):
        source, target = e.get("source"), e.get("target")
        if source not in real_ids or target not in real_ids:
            continue
        key = (source, target)
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "source_id": f"{slug}:{source}",
            "target_id": f"{slug}:{target}",
            "relation_type": "prerequisite_of",
            "origin": "roadmap",
            "confidence": 1.0,
        })

    return {"nodes": nodes, "edges": edges}
