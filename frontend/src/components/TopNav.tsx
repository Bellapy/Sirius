export type Tab = "mapas" | "estudo" | "mentoria" | "revisao";

const TABS: { id: Tab; label: string }[] = [
  { id: "mapas", label: "Mapas" },
  { id: "estudo", label: "Estudo" },
  { id: "mentoria", label: "Mentoria" },
  { id: "revisao", label: "Revisão" },
];

export function TopNav({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <nav className="top-nav">
      <span className="nav-brand">Sirius</span>
      <div className="nav-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`nav-tab${active === tab.id ? " active" : ""}`}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
