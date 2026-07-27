import type { GraphEdge, GraphNode } from "./types";

/** Layout simples em camadas por profundidade (BFS a partir dos nos raiz),
 * usando as arestas prerequisite_of. Sem dependencia externa de layout. */
export function layoutNodes(
  nodes: GraphNode[],
  edges: GraphEdge[]
): Record<string, { x: number; y: number }> {
  const prereq = edges.filter((e) => e.relation_type === "prerequisite_of");
  const incoming = new Map<string, number>();
  const adjacency = new Map<string, string[]>();

  for (const n of nodes) {
    incoming.set(n.id, 0);
    adjacency.set(n.id, []);
  }
  for (const e of prereq) {
    if (!adjacency.has(e.source_id) || !incoming.has(e.target_id)) continue;
    adjacency.get(e.source_id)!.push(e.target_id);
    incoming.set(e.target_id, (incoming.get(e.target_id) || 0) + 1);
  }

  const level = new Map<string, number>();
  const queue: string[] = [];
  for (const n of nodes) {
    if ((incoming.get(n.id) || 0) === 0) {
      level.set(n.id, 0);
      queue.push(n.id);
    }
  }
  // grafos com ciclo ou nos desconectados: garante que todo mundo entre
  for (const n of nodes) {
    if (!level.has(n.id)) {
      level.set(n.id, 0);
      queue.push(n.id);
    }
  }

  const visitedEdgesCount = new Map<string, number>();
  let head = 0;
  const maxIterations = nodes.length * 4 + 10;
  let iterations = 0;
  while (head < queue.length && iterations < maxIterations) {
    iterations++;
    const current = queue[head++];
    const currentLevel = level.get(current)!;
    for (const next of adjacency.get(current) || []) {
      const seen = (visitedEdgesCount.get(next) || 0) + 1;
      visitedEdgesCount.set(next, seen);
      level.set(next, Math.max(level.get(next) || 0, currentLevel + 1));
      if (seen === (incoming.get(next) || 0)) {
        queue.push(next);
      }
    }
  }

  const MAX_PER_COLUMN = 12;
  const LEVEL_WIDTH = 620;
  const SUBCOLUMN_WIDTH = 230;
  const ROW_HEIGHT = 90;

  const countPerLevel = new Map<number, number>();
  const positions: Record<string, { x: number; y: number }> = {};
  for (const n of nodes) {
    const lvl = level.get(n.id) || 0;
    const idx = countPerLevel.get(lvl) || 0;
    countPerLevel.set(lvl, idx + 1);
    const subcolumn = Math.floor(idx / MAX_PER_COLUMN);
    const row = idx % MAX_PER_COLUMN;
    positions[n.id] = { x: lvl * LEVEL_WIDTH + subcolumn * SUBCOLUMN_WIDTH, y: row * ROW_HEIGHT };
  }
  return positions;
}
