/** Resumo curto a partir da descricao original do roadmap.sh (nunca do
 * conteudo gerado por IA — isso evitaria gerar conteudo pago so pra
 * mostrar previa de varios nos ao mesmo tempo). Remove o titulo em H1,
 * a secao de links ("Visit the following resources...") e trunca. */
export function excerptFromMarkdown(md: string | null, maxLen = 150): string {
  if (!md) return "";

  const withoutHeading = md.replace(/^#\s+.*$/m, "").trim();
  const linksIndex = withoutHeading.search(/visit the following resources/i);
  const body = linksIndex >= 0 ? withoutHeading.slice(0, linksIndex) : withoutHeading;

  const firstParagraph = body
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .find((p) => p.length > 0);

  if (!firstParagraph) return "";

  const clean = firstParagraph.replace(/\s+/g, " ").trim();
  if (clean.length <= maxLen) return clean;
  return clean.slice(0, maxLen).replace(/\s+\S*$/, "") + "...";
}
