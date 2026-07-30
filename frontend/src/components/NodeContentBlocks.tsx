import type { ReactNode, SVGProps } from "react";

interface Section {
  title: string;
  lines: string[];
}

/** Quebra o markdown gerado em blocos por "## Secao" — o "# Titulo" inicial
 * e descartado aqui pois ja aparece no header do modal. */
function parseSections(text: string): Section[] {
  const sections: Section[] = [];
  let current: Section | null = null;

  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (line.startsWith("## ")) {
      current = { title: line.slice(3).trim(), lines: [] };
      sections.push(current);
    } else if (!line.startsWith("# ") && current) {
      current.lines.push(raw);
    }
  }
  return sections;
}

function renderSectionBody(lines: string[]): ReactNode[] {
  const blocks: ReactNode[] = [];
  let listBuffer: string[] = [];
  let key = 0;

  function flushList() {
    if (listBuffer.length) {
      blocks.push(
        <ul key={`ul-${key++}`}>
          {listBuffer.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  }

  for (const raw of lines) {
    const trimmed = raw.trim();
    if (trimmed.startsWith("- ")) {
      listBuffer.push(trimmed.slice(2));
    } else if (trimmed === "") {
      flushList();
    } else {
      flushList();
      blocks.push(<p key={`p-${key++}`}>{trimmed}</p>);
    }
  }
  flushList();
  return blocks;
}

function Icon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props} />
  );
}

function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

function SectionIcon({ title }: { title: string }) {
  const t = normalize(title);

  if (t.includes("o que")) {
    return (
      <Icon>
        <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.5.4.8 1 .8 1.6v.5h5.4v-.5c0-.6.3-1.2.8-1.6A6 6 0 0 0 12 3Z" />
      </Icon>
    );
  }
  if (t.includes("problema") || t.includes("por que")) {
    return (
      <Icon>
        <circle cx="12" cy="12" r="8" />
        <circle cx="12" cy="12" r="3.2" />
      </Icon>
    );
  }
  if (t.includes("falha") || t.includes("onde")) {
    return (
      <Icon>
        <path d="M12 3 2 20h20L12 3Z" />
        <path d="M12 10v4M12 17h.01" />
      </Icon>
    );
  }
  if (t.includes("conex")) {
    return (
      <Icon>
        <path d="M9 15 15 9" />
        <path d="M11 6.5 12.6 4.9a3.3 3.3 0 0 1 4.7 4.7L15.7 11" />
        <path d="M13 17.5 11.4 19.1a3.3 3.3 0 0 1-4.7-4.7L8.3 13" />
      </Icon>
    );
  }
  if (t.includes("caso") || t.includes("exemplo") || t.includes("aplicac")) {
    return (
      <Icon>
        <path d="M9 3h6M10 3v5.5L5.5 18a1.5 1.5 0 0 0 1.4 2h10.2a1.5 1.5 0 0 0 1.4-2L14 8.5V3" />
      </Icon>
    );
  }
  if (t.includes("trade")) {
    return (
      <Icon>
        <path d="M12 3v18M7 7l-4 6a3 3 0 0 0 6 0l-4-6M17 7l-4 6a3 3 0 0 0 6 0l-4-6" />
      </Icon>
    );
  }
  if (t.includes("compara")) {
    return (
      <Icon>
        <path d="M6 4v16M18 4v16M4 8h4M16 8h4M4 16h4M16 16h4" />
      </Icon>
    );
  }
  if (t.includes("adoc") || t.includes("mercado") || t.includes("ecossistema") || t.includes("panorama")) {
    return (
      <Icon>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M3.5 12h17M12 3.5a13 13 0 0 1 0 17M12 3.5a13 13 0 0 0 0 17" />
      </Icon>
    );
  }
  if (t.includes("mapa de decis")) {
    return (
      <Icon>
        <path d="m9 4-5.5 2v14L9 18l6 2 5.5-2V4L15 6 9 4Z" />
        <path d="M9 4v14M15 6v14" />
      </Icon>
    );
  }
  if (t.includes("filho")) {
    return (
      <Icon>
        <path d="M6 3v6c0 2 1 3 3 3h6c2 0 3-1 3-3V3M12 12v9M8 21h8" />
      </Icon>
    );
  }
  return (
    <Icon>
      <path d="M7 3h7l4 4v14H7z" />
      <path d="M14 3v4h4M9.5 12h5M9.5 15.5h5" />
    </Icon>
  );
}

export function NodeContentBlocks({ text }: { text: string }) {
  const sections = parseSections(text);
  return (
    <div className="knowledge-blocks">
      {sections.map((s, i) => (
        <section key={i} className="knowledge-block">
          <h4 className="knowledge-block-title">
            <SectionIcon title={s.title} />
            {s.title}
          </h4>
          <div className="knowledge-block-body">{renderSectionBody(s.lines)}</div>
        </section>
      ))}
    </div>
  );
}
