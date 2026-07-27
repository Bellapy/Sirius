export type NodeType = "atomic_comparable" | "atomic_conceptual" | "branch";
export type NodeStatus = "nao_iniciado" | "lido" | "validado";

export interface RoadmapListItem {
  slug: string;
  imported: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: NodeType | null;
  status: NodeStatus;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
  relation_type: string;
  origin: string;
  confidence: number;
}

export interface RoadmapGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface AuditAttempt {
  tentativa: number;
  aprovado: boolean;
  motivo: string | null;
}

export interface GeneratedContent {
  template_usado: string;
  texto: string;
  auditoria: AuditAttempt[];
  status: "aprovado" | "revisar_manualmente";
}

export interface NodeDetail {
  id: string;
  label: string;
  roadmap_origin: string;
  description_md: string | null;
  node_type: NodeType;
  generated_content: GeneratedContent | null;
  status: NodeStatus;
}

export interface MentoriaTurnMsg {
  role: "mentora" | "usuario";
  text: string;
}

export interface RevisaoItem {
  session_id: string;
  node_id: string;
  label: string;
  roadmap_origin: string;
  veredito_validado: boolean | null;
  veredito_motivo: string | null;
  started_at: string;
}
