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
    return <p style={{ color: "var(--text-dim)" }}>Carregando roadmaps...</p>;
  }

  const filtered = roadmaps.filter((r) => r.slug.includes(filter.toLowerCase()));

  return (
    <div style={{ maxWidth: 720 }}>
      <h2>Mapas</h2>
      <p style={{ color: "var(--text-dim)" }}>
        Escolha um roadmap do{" "}
        <code style={{ color: "var(--text)" }}>developer-roadmap</code> para estudar. Importar +
        enriquecer roda a classificação de estrutura uma única vez (modo simulado por padrão).
      </p>
      <input
        placeholder="filtrar..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        style={{ width: "100%", marginBottom: "1rem" }}
      />
      <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {filtered.map((r) => (
          <li
            key={r.slug}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.6rem 0.9rem",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              background: "var(--bg-elevated)",
            }}
          >
            <span>{r.slug}</span>
            {r.imported ? (
              <button className="primary" onClick={() => onOpenRoadmap(r.slug)}>
                Abrir
              </button>
            ) : (
              <button disabled={busySlug === r.slug} onClick={() => handleImportAndEnrich(r.slug)}>
                {busySlug === r.slug ? "Importando..." : "Importar"}
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
