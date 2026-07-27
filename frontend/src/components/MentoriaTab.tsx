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
      <div className="mentoria-zen">
        <p className="empty-state" style={{ textAlign: "center" }}>
          Nenhuma sessão ativa. Abra um nó na aba Estudo (ou reabra um da Revisão) e clique em
          "Iniciar Mentoria".
        </p>
      </div>
    );
  }

  if (ended) {
    return (
      <div className="mentoria-zen">
        <h2>Sessão encerrada</h2>
        <p className="muted">
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
    <div className="mentoria-zen">
      <div className="mentoria-eyebrow">Mentoria · {active.nodeLabel}</div>
      <div className="mentoria-card">
        <p className="mentoria-question">{active.currentQuestion}</p>
      </div>
      <div className="mentoria-form">
        <textarea
          rows={5}
          placeholder="Escreva sua resposta com suas próprias palavras..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
        />
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <div className="mentoria-actions">
          <button className="primary" disabled={sending || !answer.trim()} onClick={submit}>
            {sending ? <span className="spinner" /> : null} Responder
          </button>
          <button className="danger-outline" disabled={sending} onClick={encerrar}>
            Encerrar sessão
          </button>
        </div>
      </div>
    </div>
  );
}
