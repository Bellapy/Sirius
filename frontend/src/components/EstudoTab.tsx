import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { excerptFromMarkdown } from "../markdownExcerpt";
import type { GraphEdge, GraphNode, NodeDetail } from "../types";
import { NodeDetailModal } from "./NodeDetailModal";

type StepState = "concluido" | "atual" | "futuro";

const STEP_LABEL: Record<StepState, string> = {
  concluido: "Concluído",
  atual: "Passo atual",
  futuro: "Ainda não estudado",
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

function progressRingStyle(pct: number) {
  return {
    background: `conic-gradient(var(--lilac) ${pct * 3.6}deg, var(--border) 0deg)`,
  };
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
  const currentNodes = useMemo(
    () => currentNodeIds.map((id) => nodeById.get(id)).filter((n): n is GraphNode => Boolean(n)),
    [currentNodeIds, nodeById]
  );

  const currentStepIndex = currentNodes.findIndex((n) => n.status !== "validado");
  const validatedCount = currentNodes.filter((n) => n.status === "validado").length;
  const progressPct = currentNodes.length ? Math.round((validatedCount / currentNodes.length) * 100) : 0;

  function stepStateFor(node: GraphNode, idx: number): StepState {
    if (node.status === "validado") return "concluido";
    if (idx === currentStepIndex) return "atual";
    return "futuro";
  }

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
        <span className="spinner" /> Carregando trilha...
      </div>
    );
  }

  const selectedChildCount = selected ? childrenMap.get(selected.id)?.length || 0 : 0;

  return (
    <div className="trail-layout">
      <div className="trail-main">
        <div className="trail-header">
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

          {currentNodes.length > 0 && (
            <div className="trail-progress">
              <div className="progress-ring" style={progressRingStyle(progressPct)}>
                <span className="progress-ring-value">{progressPct}%</span>
              </div>
              <span className="trail-progress-label">progresso desta trilha</span>
            </div>
          )}
        </div>

        <div className="trail-list">
          <div className="trail-start-marker">
            <span className="trail-start-dot" />
            Início da trilha
          </div>

          {currentNodes.map((n, i) => {
            const state = stepStateFor(n, i);
            const childCount = childrenMap.get(n.id)?.length || 0;
            const excerpt = excerptFromMarkdown(n.description_md);
            return (
              <button
                key={n.id}
                className={`trail-card state-${state}`}
                onClick={() => openNode(n.id)}
              >
                <span className="trail-card-badge">Etapa {i + 1}</span>
                <h3 className="trail-card-title">{n.label}</h3>
                {excerpt && <p className="trail-card-desc">{excerpt}</p>}
                <div className="trail-card-footer">
                  <span>{STEP_LABEL[state]}</span>
                  {childCount > 0 && <span>{childCount} sub-tópicos ›</span>}
                </div>
              </button>
            );
          })}

          {currentNodes.length === 0 && (
            <p className="empty-state">Esse tópico não tem sub-tópicos próprios ainda.</p>
          )}
        </div>
      </div>

      <aside className="trail-sidebar">
        <h4 className="trail-sidebar-title">Trilha da jornada</h4>
        <ul className="trail-sidebar-list">
          {currentNodes.map((n, i) => {
            const state = stepStateFor(n, i);
            return (
              <li key={n.id} className={`trail-sidebar-item state-${state}`} onClick={() => openNode(n.id)}>
                {state === "atual" ? (
                  <span className="trail-sidebar-dot-pulse" />
                ) : (
                  <span className="trail-sidebar-icon">{state === "concluido" ? "✓" : ""}</span>
                )}
                {n.label}
              </li>
            );
          })}
        </ul>

        <div className="trail-reminder-card">
          <h5>Lembrete</h5>
          <p>Grandes conquistas começam com pequenos passos consistentes.</p>
        </div>
      </aside>

      {selected && (
        <NodeDetailModal
          node={selected}
          childCount={selectedChildCount}
          onClose={() => setSelected(null)}
          onDrillIn={() => {
            setPath([...path, selected.id]);
            setSelected(null);
          }}
          onStartMentoria={() => onStartMentoria(selected.id)}
        />
      )}

      {loadingNode && (
        <div className="loading-state" style={{ position: "fixed", bottom: 20, right: 20 }}>
          <span className="spinner" /> Gerando conteúdo...
        </div>
      )}
    </div>
  );
}
