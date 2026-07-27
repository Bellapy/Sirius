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
  if (!items) return <p style={{ color: "var(--text-dim)" }}>Carregando...</p>;
  if (items.length === 0)
    return <p style={{ color: "var(--text-dim)" }}>Nenhuma sessão de mentoria ainda.</p>;

  return (
    <div style={{ maxWidth: 720 }}>
      <h2>Revisão</h2>
      <p style={{ color: "var(--text-dim)" }}>
        Nós com sessão de mentoria — os não validados aparecem primeiro, pra refazer.
      </p>
      <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {items.map((item) => (
          <li
            key={item.node_id}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.6rem 0.9rem",
              border: "1px solid var(--border)",
              borderRadius: 8,
              background: "var(--bg-elevated)",
            }}
          >
            <div>
              <div>{item.label}</div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
                {item.roadmap_origin} ·{" "}
                {item.veredito_validado ? "validado" : "ainda não validado"}
              </div>
            </div>
            <button className="primary" onClick={() => onReopenMentoria(item.node_id)}>
              Refazer
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
