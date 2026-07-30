import type { NodeDetail } from "../types";
import { NodeContentBlocks } from "./NodeContentBlocks";

const STATUS_LABEL: Record<string, string> = {
  nao_iniciado: "Não iniciado",
  lido: "Lido",
  validado: "Concluído",
};

export function NodeDetailModal({
  node,
  childCount,
  onClose,
  onDrillIn,
  onStartMentoria,
}: {
  node: NodeDetail;
  childCount: number;
  onClose: () => void;
  onDrillIn: () => void;
  onStartMentoria: () => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="node-modal" onClick={(e) => e.stopPropagation()}>
        <div className="node-modal-header">
          <div>
            <span className="node-modal-badge">{STATUS_LABEL[node.status]}</span>
            <h2 className="node-modal-title">{node.label}</h2>
          </div>
          <button className="node-modal-close" onClick={onClose} aria-label="Fechar">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 6L18 18M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <div className="node-modal-body">
          {node.generated_content?.status === "revisar_manualmente" && (
            <div className="warn-box">Este conteúdo reprovou a auditoria 2x e precisa de revisão manual.</div>
          )}
          {node.generated_content ? (
            <NodeContentBlocks text={node.generated_content.texto} />
          ) : (
            <p>Gerando conteúdo...</p>
          )}
        </div>
        <div className="node-modal-footer">
          {childCount > 0 && (
            <button className="btn-ghost-outline" onClick={onDrillIn}>
              Ver sub-tópicos ({childCount})
            </button>
          )}
          <button className="btn-gradient" disabled={!node.generated_content} onClick={onStartMentoria}>
            Iniciar Mentoria
          </button>
        </div>
      </div>
    </div>
  );
}
