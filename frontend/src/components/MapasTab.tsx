import { useEffect, useState } from "react";
import { api } from "../api";
import type { RoadmapListItem } from "../types";

export function MapasTab({ onOpenRoadmap }: { onOpenRoadmap: (slug: string) => void }) {
  const [roadmaps, setRoadmaps] = useState<RoadmapListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busySlug, setBusySlug] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  function load() {
    api
      .listRoadmaps()
      .then(setRoadmaps)
      .catch((e) => setError(String(e.message || e)));
  }

  useEffect(load, []);

  async function handleImportAndEnrich(slug: string) {
    setBusySlug(slug);
    setError(null);
    try {
      await api.importRoadmap(slug);
      await api.enrichRoadmap(slug);
      load();
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setBusySlug(null);
    }
  }

  if (error) {
    return <p style={{ color: "var(--danger)" }}>Erro: {error}</p>;
  }
  if (!roadmaps) {
    return (
      <div className="loading-state">
        <span className="spinner" /> Carregando roadmaps...
      </div>
    );
  }

  const filtered = roadmaps.filter((r) => r.slug.includes(filter.toLowerCase()));

  return (
    <div>
      <h2>Mapas</h2>
      <p className="muted">
        Escolha um roadmap do <code>developer-roadmap</code> para estudar. Importar carrega a
        estrutura original; em seguida a classificação de tipos e conexões roda uma única vez
        (modo simulado por padrão, sem custo).
      </p>
      <input
        className="search-input"
        placeholder="Filtrar roadmaps..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      <ul className="list">
        {filtered.map((r) => (
          <li key={r.slug} className="list-item">
            <div>
              <div className="list-item-title">{r.slug}</div>
              <div className="list-item-sub">
                {r.imported ? "importado e pronto para estudo" : "ainda não importado"}
              </div>
            </div>
            {r.imported ? (
              <button className="primary" onClick={() => onOpenRoadmap(r.slug)}>
                Abrir
              </button>
            ) : (
              <button disabled={busySlug === r.slug} onClick={() => handleImportAndEnrich(r.slug)}>
                {busySlug === r.slug ? (
                  <>
                    <span className="spinner" /> Importando...
                  </>
                ) : (
                  "Importar"
                )}
              </button>
            )}
          </li>
        ))}
        {filtered.length === 0 && <li className="empty-state">Nenhum roadmap encontrado para "{filter}".</li>}
      </ul>
    </div>
  );
}
