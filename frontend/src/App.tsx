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

  const isFullBleed = activeTab === "estudo";

  return (
    <div className="app-shell">
      <TopNav active={activeTab} onChange={setActiveTab} />
      {globalError && (
        <div className="banner-error">
          {globalError}
          <button className="ghost" onClick={() => setGlobalError(null)}>
            fechar
          </button>
        </div>
      )}
      <main className="page" style={isFullBleed ? { display: "flex", flexDirection: "column" } : undefined}>
        {isFullBleed ? (
          <div style={{ flex: 1, minHeight: 0 }}>
            <EstudoTab roadmapSlug={selectedRoadmap} onStartMentoria={startMentoria} />
          </div>
        ) : (
          <div className={`page-inner${activeTab === "mentoria" ? " narrow" : ""}`}>
            {activeTab === "mapas" && <MapasTab onOpenRoadmap={openRoadmap} />}
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
              <RevisaoTab onReopenMentoria={(nodeId) => startMentoria(nodeId)} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
