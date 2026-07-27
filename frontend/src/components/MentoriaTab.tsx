import { useState } from "react";
import { api } from "../api";

export interface ActiveMentoria {
  sessionId: string;
  nodeId: string;
  nodeLabel: string;
  currentQuestion: string;
}

export function MentoriaTab({
  active,
  onUpdateQuestion,
  onSessionEnded,
}: {
  active: ActiveMentoria | null;
  onUpdateQuestion: (text: string) => void;
  onSessionEnded: () => void;
}) {
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const [ended, setEnded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!active) {
    return (
      <p style={{ color: "var(--text-dim)" }}>
        Nenhuma sessão ativa. Abra um nó na aba Estudo (ou reabra um da Revisão) e clique em "Iniciar
        Mentoria".
      </p>
    );
  }

  if (ended) {
    return (
      <div style={{ maxWidth: 560 }}>
        <h2>Sessão encerrada</h2>
        <p style={{ color: "var(--text-dim)" }}>
          O estado do nó "{active.nodeLabel}" foi atualizado. Volte para Estudo para ver.
        </p>
        <button
          className="primary"
          onClick={() => {
            setEnded(false);
            onSessionEnded();
          }}
        >
          Voltar
        </button>
      </div>
    );
  }

  async function submit() {
    if (!answer.trim() || !active) return;
    setSending(true);
    setError(null);
    try {
      const resp = await api.sendMentoriaTurn(active.sessionId, answer);
      onUpdateQuestion(resp.turn.text);
      setAnswer("");
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setSending(false);
    }
  }

  async function encerrar() {
    if (!active) return;
    setSending(true);
    try {
      await api.endMentoria(active.sessionId);
      setEnded(true);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <p style={{ color: "var(--text-dim)", fontSize: "0.85rem" }}>Mentoria sobre "{active.nodeLabel}"</p>
      <div
        style={{
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "1.25rem",
          background: "var(--bg-elevated)",
          marginBottom: "1rem",
        }}
      >
        <p style={{ margin: 0, fontSize: "1.05rem" }}>{active.currentQuestion}</p>
      </div>
      <textarea
        rows={5}
        style={{ width: "100%" }}
        placeholder="Escreva sua resposta com suas próprias palavras..."
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
      />
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
        <button className="primary" disabled={sending || !answer.trim()} onClick={submit}>
          Responder
        </button>
        <button disabled={sending} onClick={encerrar}>
          Encerrar sessão
        </button>
      </div>
    </div>
  );
}
