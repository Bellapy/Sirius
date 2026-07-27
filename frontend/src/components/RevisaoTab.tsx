import { useEffect, useState } from "react";
import { api } from "../api";
import type { RevisaoItem } from "../types";

export function RevisaoTab({ onReopenMentoria }: { onReopenMentoria: (nodeId: string) => void }) {
  const [items, setItems] = useState<RevisaoItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getRevisao()
      .then(setItems)
      .catch((e) => setError(e.message || String(e)));
  }, []);

  if (error) return <p style={{ color: "var(--danger)" }}>Erro: {error}</p>;
  if (!items)
    return (
      <div className="loading-state">
        <span className="spinner" /> Carregando...
      </div>
    );

  return (
    <div>
      <h2>Revisão</h2>
      <p className="muted">Nós com sessão de mentoria — os não validados aparecem primeiro, pra refazer.</p>
      {items.length === 0 ? (
        <p className="empty-state">Nenhuma sessão de mentoria ainda.</p>
      ) : (
        <ul className="list">
          {items.map((item) => (
            <li key={item.node_id} className="list-item">
              <div>
                <div className="list-item-title">{item.label}</div>
                <div className="list-item-sub">{item.roadmap_origin}</div>
              </div>
              <span className={`badge${item.veredito_validado ? " badge-validado" : " badge-pendente"}`}>
                <span className="badge-dot" /> {item.veredito_validado ? "validado" : "não validado"}
              </span>
              <button className="primary" onClick={() => onReopenMentoria(item.node_id)}>
                Refazer
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
