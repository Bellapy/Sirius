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
      <h1 className="animate-fade-in-up">Mapas</h1>
      <p className="lede">
        Escolha um roadmap do <code>developer-roadmap</code> para estudar. Importar carrega a
        estrutura original; em seguida a classificação de tipos e conexões roda uma única vez
        (modo simulado por padrão, sem custo).
      </p>
      <div className="search-bar">
        <svg className="search-bar-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
          <path d="M20 20L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <input
          className="search-input"
          placeholder="Filtrar roadmaps..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>
      <ul className="roadmap-grid">
        {filtered.map((r) => (
          <li key={r.slug} className="roadmap-card">
            <div className="roadmap-card-top">
              <div className="roadmap-card-title">{r.slug}</div>
              <div className={`roadmap-card-status${r.imported ? " is-ready" : ""}`}>
                <span className="roadmap-card-status-dot" />
                {r.imported ? "Importado e pronto para estudo" : "Ainda não importado"}
              </div>
            </div>
            <div className="roadmap-card-footer">
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
            </div>
          </li>
        ))}
        {filtered.length === 0 && <li className="empty-state">Nenhum roadmap encontrado para "{filter}".</li>}
      </ul>
    </div>
  );
}
