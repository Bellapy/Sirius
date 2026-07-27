import { useState } from "react";
import { api } from "./api";
import { EstudoTab } from "./components/EstudoTab";
import { MapasTab } from "./components/MapasTab";
import { MentoriaTab, type ActiveMentoria } from "./components/MentoriaTab";
import { RevisaoTab } from "./components/RevisaoTab";
import { TopNav, type Tab } from "./components/TopNav";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("mapas");
  const [selectedRoadmap, setSelectedRoadmap] = useState<string | null>(null);
  const [activeMentoria, setActiveMentoria] = useState<ActiveMentoria | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);

  function openRoadmap(slug: string) {
    setSelectedRoadmap(slug);
    setActiveTab("estudo");
  }

  async function startMentoria(nodeId: string) {
    try {
      const node = await api.getNode(nodeId);
      const resp = await api.startMentoria(nodeId);
      setActiveMentoria({
        sessionId: resp.session_id,
        nodeId,
        nodeLabel: node.label,
        currentQuestion: resp.turn.text,
      });
      setActiveTab("mentoria");
    } catch (e: any) {
      setGlobalError(e.message || String(e));
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <TopNav active={activeTab} onChange={setActiveTab} />
      {globalError && (
        <div style={{ background: "var(--danger-dim)", color: "var(--text)", padding: "0.5rem 1.5rem" }}>
          {globalError}{" "}
          <button onClick={() => setGlobalError(null)} style={{ marginLeft: "0.5rem" }}>
            fechar
          </button>
        </div>
      )}
      <main style={{ flex: 1, padding: "1.5rem", overflow: "auto" }}>
        {activeTab === "mapas" && <MapasTab onOpenRoadmap={openRoadmap} />}
        {activeTab === "estudo" && (
          <EstudoTab roadmapSlug={selectedRoadmap} onStartMentoria={startMentoria} />
        )}
        {activeTab === "mentoria" && (
          <MentoriaTab
            active={activeMentoria}
            onUpdateQuestion={(text) =>
              setActiveMentoria((m) => (m ? { ...m, currentQuestion: text } : m))
            }
            onSessionEnded={() => setActiveMentoria(null)}
          />
        )}
        {activeTab === "revisao" && (
          <RevisaoTab
            onReopenMentoria={(nodeId) => {
              startMentoria(nodeId);
            }}
          />
        )}
      </main>
    </div>
  );
}

export default App;
