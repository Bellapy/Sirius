import { useEffect, useMemo, useState, type CSSProperties } from "react";
import ReactFlow, { Background, Controls, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import { api } from "../api";
import { layoutNodes } from "../graphLayout";
import type { GraphEdge, GraphNode, NodeDetail } from "../types";
import { SimpleMarkdown } from "./SimpleMarkdown";

function nodeStyle(node: GraphNode): CSSProperties {
  const borderRadius = node.node_type === "branch" ? 4 : node.node_type === "atomic_comparable" ? 10 : 20;
  const base: CSSProperties = {
    border: `2px solid ${node.status === "nao_iniciado" ? "var(--text-dim)" : "var(--accent)"}`,
    borderRadius,
    padding: "8px 12px",
    fontSize: 13,
    color: node.status === "validado" ? "#1a1713" : "var(--text)",
    background:
      node.status === "validado"
        ? "var(--fill-validado)"
        : node.status === "lido"
          ? "var(--fill-lido)"
          : "var(--bg-elevated)",
  };
  return base;
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

  useEffect(() => {
    if (!roadmapSlug) return;
    setGraph(null);
    setSelected(null);
    api
      .getGraph(roadmapSlug)
      .then(setGraph)
      .catch((e) => setError(e.message || String(e)));
  }, [roadmapSlug]);

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graph) return { flowNodes: [] as Node[], flowEdges: [] as Edge[] };
    const positions = layoutNodes(graph.nodes, graph.edges);
    const flowNodes: Node[] = graph.nodes.map((n) => ({
      id: n.id,
      position: positions[n.id],
      data: { label: n.label },
      style: nodeStyle(n),
    }));
    const flowEdges: Edge[] = graph.edges.map((e) => ({
      id: `${e.source_id}->${e.target_id}-${e.relation_type}`,
      source: e.source_id,
      target: e.target_id,
      label: e.relation_type === "prerequisite_of" ? undefined : e.relation_type,
      style: { stroke: e.origin === "llm_inferred" ? "var(--accent-dim)" : "var(--text-dim)" },
      animated: false,
    }));
    return { flowNodes, flowEdges };
  }, [graph]);

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
    return <p style={{ color: "var(--text-dim)" }}>Escolha um roadmap na aba Mapas primeiro.</p>;
  }
  if (error) {
    return <p style={{ color: "var(--danger)" }}>Erro: {error}</p>;
  }
  if (!graph) {
    return <p style={{ color: "var(--text-dim)" }}>Carregando grafo...</p>;
  }

  return (
    <div style={{ display: "flex", height: "calc(100vh - 130px)" }}>
      <div style={{ flex: selected ? "0 0 60%" : "1 1 100%" }}>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          onNodeClick={(_, node) => openNode(node.id)}
          fitView
        >
          <Background color="var(--border)" gap={24} />
          <Controls />
        </ReactFlow>
      </div>
      {selected && (
        <aside
          style={{
            flex: "0 0 40%",
            borderLeft: "1px solid var(--border)",
            padding: "1.5rem",
            overflowY: "auto",
          }}
        >
          <button onClick={() => setSelected(null)} style={{ marginBottom: "1rem" }}>
            Fechar
          </button>
          <h2>{selected.label}</h2>
          <p style={{ color: "var(--text-dim)", fontSize: "0.85rem" }}>
            {selected.node_type} · status: {selected.status}
          </p>
          {selected.generated_content?.status === "revisar_manualmente" && (
            <p style={{ color: "var(--danger)" }}>
              Este conteúdo reprovou a auditoria 2x e precisa de revisão manual.
            </p>
          )}
          {selected.generated_content && <SimpleMarkdown text={selected.generated_content.texto} />}
          <button
            className="primary"
            style={{ marginTop: "1rem" }}
            disabled={!selected.generated_content}
            onClick={() => onStartMentoria(selected.id)}
          >
            Iniciar Mentoria
          </button>
        </aside>
      )}
      {loadingNode && (
        <div style={{ position: "fixed", bottom: 20, right: 20, color: "var(--text-dim)" }}>
          Gerando conteúdo...
        </div>
      )}
    </div>
  );
}
