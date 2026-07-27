export type Tab = "mapas" | "estudo" | "mentoria" | "revisao";

const TABS: { id: Tab; label: string }[] = [
  { id: "mapas", label: "Mapas" },
  { id: "estudo", label: "Estudo" },
  { id: "mentoria", label: "Mentoria" },
  { id: "revisao", label: "Revisão" },
];

export function TopNav({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        gap: "1.5rem",
        padding: "0.75rem 1.5rem",
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-elevated)",
      }}
    >
      <span style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.15rem" }}>
        Sirius
      </span>
      <div style={{ display: "flex", gap: "0.25rem" }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            style={{
              border: "none",
              background: active === tab.id ? "var(--bg-hover)" : "transparent",
              color: active === tab.id ? "var(--text)" : "var(--text-dim)",
              borderRadius: "6px",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
