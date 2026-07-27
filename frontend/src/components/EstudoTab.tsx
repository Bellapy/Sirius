import { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import { api } from "../api";
import { layoutNodes } from "../graphLayout";
import type { GraphEdge, GraphNode, NodeDetail } from "../types";
import { SimpleMarkdown } from "./SimpleMarkdown";

const NODE_TYPE_LABEL: Record<string, string> = {
  branch: "ramificação",
  atomic_comparable: "atômico comparável",
  atomic_conceptual: "atômico conceitual",
};

function buildChildrenMap(edges: GraphEdge[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const e of edges) {
    if (e.relation_type !== "prerequisite_of") continue;
    if (!map.has(e.source_id)) map.set(e.source_id, []);
    map.get(e.source_id)!.push(e.target_id);
  }
  return map;
}

export function EstudoTab({
  roadmapSlug,
  onStartMentoria,
}: {
  roadmapSlug: string | null;
  onStartMentoria: (nodeId: string) => void;
}) {
  const [graph, setGraph] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<NodeDetail | null>(null);
  const [loadingNode, setLoadingNode] = useState(false);
  const [path, setPath] = useState<string[]>([]);

  useEffect(() => {
    if (!roadmapSlug) return;
    setGraph(null);
    setSelected(null);
    setPath([]);
    api
      .getGraph(roadmapSlug)
      .then(setGraph)
      .catch((e) => setError(e.message || String(e)));
  }, [roadmapSlug]);

  const nodeById = useMemo(() => {
    const m = new Map<string, GraphNode>();
    graph?.nodes.forEach((n) => m.set(n.id, n));
    return m;
  }, [graph]);

  const childrenMap = useMemo(
    () => (graph ? buildChildrenMap(graph.edges) : new Map<string, string[]>()),
    [graph]
  );

  const rootIds = useMemo(() => {
    if (!graph) return [];
    const hasParent = new Set<string>();
    for (const e of graph.edges) {
      if (e.relation_type === "prerequisite_of") hasParent.add(e.target_id);
    }
    return graph.nodes.filter((n) => !hasParent.has(n.id)).map((n) => n.id);
  }, [graph]);

  const currentNodeIds = path.length === 0 ? rootIds : childrenMap.get(path[path.length - 1]) || [];

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graph) return { flowNodes: [] as Node[], flowEdges: [] as Edge[] };
    const currentNodes = currentNodeIds.map((id) => nodeById.get(id)!).filter(Boolean);
    const idSet = new Set(currentNodeIds);
    const currentEdges = graph.edges.filter((e) => idSet.has(e.source_id) && idSet.has(e.target_id));
    const positions = layoutNodes(currentNodes, currentEdges);

    const flowNodes: Node[] = currentNodes.map((n) => {
      const childCount = childrenMap.get(n.id)?.length || 0;
      return {
        id: n.id,
        position: positions[n.id],
        data: { label: n.label },
        className: `rf-node type-${n.node_type} status-${n.status}${childCount ? " has-children" : ""}`,
      };
    });
    const flowEdges: Edge[] = currentEdges.map((e) => ({
      id: `${e.source_id}->${e.target_id}-${e.relation_type}`,
      source: e.source_id,
      target: e.target_id,
      label: e.relation_type === "prerequisite_of" ? undefined : e.relation_type,
      style: { stroke: e.origin === "llm_inferred" ? "var(--accent-dim)" : "var(--text-faint)" },
      labelStyle: { fill: "var(--text-dim)", fontSize: 11 },
      animated: false,
    }));
    return { flowNodes, flowEdges };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph, path]);

  async function openNode(nodeId: string) {
    setLoadingNode(true);
    setSelected(null);
    try {
      const detail = await api.getNode(nodeId);
      setSelected(detail);
      setGraph((g) =>
        g
          ? { ...g, nodes: g.nodes.map((n) => (n.id === nodeId ? { ...n, status: detail.status } : n)) }
          : g
      );
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoadingNode(false);
    }
  }

  if (!roadmapSlug) {
    return <p className="muted">Escolha um roadmap na aba Mapas primeiro.</p>;
  }
  if (error) {
    return <p style={{ color: "var(--danger)" }}>Erro: {error}</p>;
  }
  if (!graph) {
    return (
      <div className="loading-state">
        <span className="spinner" /> Carregando grafo...
      </div>
    );
  }

  const selectedChildCount = selected ? childrenMap.get(selected.id)?.length || 0 : 0;

  return (
    <div className="estudo-layout">
      <div className="graph-pane">
        <div className="breadcrumb">
          <button
            className={`breadcrumb-item${path.length === 0 ? " current" : ""}`}
            onClick={() => setPath([])}
          >
            Visão geral
          </button>
          {path.map((id, i) => (
            <span key={id} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <span className="breadcrumb-sep">›</span>
              <button
                className={`breadcrumb-item${i === path.length - 1 ? " current" : ""}`}
                onClick={() => setPath(path.slice(0, i + 1))}
              >
                {nodeById.get(id)?.label || id}
              </button>
            </span>
          ))}
        </div>

        <div className="graph-canvas">
          <ReactFlow nodes={flowNodes} edges={flowEdges} onNodeClick={(_, node) => openNode(node.id)} fitView>
            <Background color="var(--border-soft)" gap={22} />
            <Controls />
          </ReactFlow>
        </div>

        <div className="graph-legend">
          <span className="legend-item">
            <span className="legend-swatch" /> não iniciado
          </span>
          <span className="legend-item">
            <span className="legend-swatch status-lido" /> lido
          </span>
          <span className="legend-item">
            <span className="legend-swatch status-validado" /> validado pela mentora
          </span>
          <span className="legend-item">
            <span className="legend-swatch shape-branch" /> ramificação
          </span>
          <span className="legend-item">
            <span className="legend-swatch shape-atomic_comparable" /> atômico comparável
          </span>
          <span className="legend-item">
            <span className="legend-swatch shape-atomic_conceptual" /> atômico conceitual
          </span>
          <span className="legend-item">nó com "···" tem sub-tópicos — clique e depois "Ver sub-tópicos"</span>
        </div>
      </div>

      {selected && (
        <aside className="detail-panel">
          <div className="detail-panel-header">
            <button className="ghost" onClick={() => setSelected(null)} style={{ marginBottom: "0.6rem" }}>
              ← Fechar
            </button>
            <h2 style={{ marginBottom: "0.4rem" }}>{selected.label}</h2>
            <div className="detail-panel-badges">
              <span className="badge">{NODE_TYPE_LABEL[selected.node_type] || selected.node_type}</span>
              <span className={`badge${selected.status === "validado" ? " badge-validado" : " badge-pendente"}`}>
                <span className="badge-dot" /> {selected.status.replace("_", " ")}
              </span>
            </div>
          </div>
          <div className="detail-panel-body">
            {selected.generated_content?.status === "revisar_manualmente" && (
              <div className="warn-box">Este conteúdo reprovou a auditoria 2x e precisa de revisão manual.</div>
            )}
            {selected.generated_content && <SimpleMarkdown text={selected.generated_content.texto} />}
          </div>
          <div className="detail-panel-footer">
            {selectedChildCount > 0 && (
              <button
                onClick={() => {
                  setPath([...path, selected.id]);
                  setSelected(null);
                }}
              >
                Ver sub-tópicos ({selectedChildCount})
              </button>
            )}
            <button
              className="primary"
              disabled={!selected.generated_content}
              onClick={() => onStartMentoria(selected.id)}
            >
              Iniciar Mentoria
            </button>
          </div>
        </aside>
      )}

      {loadingNode && (
        <div className="loading-state" style={{ position: "fixed", bottom: 20, right: 20 }}>
          <span className="spinner" /> Gerando conteúdo...
        </div>
      )}
    </div>
  );
}
