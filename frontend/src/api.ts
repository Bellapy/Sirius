import type {
  GraphNode,
  MentoriaTurnMsg,
  NodeDetail,
  RevisaoItem,
  RoadmapGraph,
  RoadmapListItem,
} from "./types";

const API_BASE = "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `Erro ${resp.status} em ${path}`);
  }
  return resp.json();
}

export const api = {
  listRoadmaps: () => request<RoadmapListItem[]>("/roadmaps"),
  importRoadmap: (slug: string) =>
    request<{ nodes: number; edges: number }>(`/roadmaps/${slug}/import`, { method: "POST" }),
  enrichRoadmap: (slug: string) =>
    request<{ nodes_classified: number; new_edges: number }>(`/roadmaps/${slug}/enrich`, {
      method: "POST",
    }),
  getGraph: (slug: string) => request<RoadmapGraph>(`/roadmaps/${slug}/graph`),
  getNode: (nodeId: string) => request<NodeDetail>(`/nodes/${encodeURIComponent(nodeId)}`),
  startMentoria: (nodeId: string) =>
    request<{ session_id: string; turn: MentoriaTurnMsg }>(
      `/nodes/${encodeURIComponent(nodeId)}/mentoria/start`,
      { method: "POST" }
    ),
  sendMentoriaTurn: (sessionId: string, text: string) =>
    request<{ turn: MentoriaTurnMsg }>(`/mentoria/${sessionId}/turn`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  endMentoria: (sessionId: string) =>
    request<{ encerrada: boolean }>(`/mentoria/${sessionId}/end`, { method: "POST" }),
  getRevisao: () => request<RevisaoItem[]>("/revisao"),
};

export type { GraphNode };
