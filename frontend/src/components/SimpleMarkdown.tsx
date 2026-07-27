import type { ReactNode } from "react";

/** Renderizador minimo: o texto gerado usa so #/##, listas com "-" e paragrafos.
 * Evita puxar uma lib de markdown so para isso. */
export function SimpleMarkdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  let listBuffer: string[] = [];

  function flushList(key: string) {
    if (listBuffer.length) {
      blocks.push(
        <ul key={key}>
          {listBuffer.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  }

  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("## ")) {
      flushList(`ul-${i}`);
      blocks.push(<h3 key={i}>{trimmed.slice(3)}</h3>);
    } else if (trimmed.startsWith("# ")) {
      flushList(`ul-${i}`);
      blocks.push(<h2 key={i}>{trimmed.slice(2)}</h2>);
    } else if (trimmed.startsWith("- ")) {
      listBuffer.push(trimmed.slice(2));
    } else if (trimmed === "") {
      flushList(`ul-${i}`);
    } else {
      flushList(`ul-${i}`);
      blocks.push(<p key={i}>{trimmed}</p>);
    }
  });
  flushList("ul-end");

  return <div>{blocks}</div>;
}
