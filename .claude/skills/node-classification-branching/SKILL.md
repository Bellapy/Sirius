---
name: node-classification-branching
description: Use ao classificar o node_type de um nó do grafo (atomic_comparable / atomic_conceptual / branch), ao classificar relation_type de uma aresta candidata, ou ao decidir se/quantos filhos novos um nó branch pode receber numa passada. Cobre a combinação sinal estrutural (grau/centralidade, sem custo de IA) + confirmação semântica (Haiku), o vocabulário fechado de 5 relation_types, e o limite de 5 filhos novos por nó por passada. Não usar para geração de texto de conteúdo (ver skill content-templates) nem para auditoria pós-geração (ver skill audit-checklist).
---

# Classificação de tipo de nó e regra de ramificação

## Classificação de node_type

Combinação de dois sinais — nunca decidir por só um deles:

1. **Sinal estrutural (automático, sem custo de IA)**: centralidade/grau
   de conexão no grafo, calculado com lib de grafos (ex: `networkx`).
   - Muitos filhos paralelos → candidato a `branch`.
   - Arestas `alternative_to` no mesmo nível de abstração → candidato a
     `atomic_comparable`.
2. **Confirmação semântica (1 chamada Haiku curta por nó)**: recebe o nó
   + vizinhos diretos, confirma ou corrige a classificação do sinal
   estrutural.

Três valores possíveis de `node_type`: `atomic_comparable`,
`atomic_conceptual`, `branch`.

## Classificação de relation_type (arestas)

Vocabulário fechado, nunca texto livre — modelo Haiku, via Batch API:

- `prerequisite_of`
- `alternative_to`
- `contrasts_with`
- `composes_with`
- `applied_in`

Pares candidatos são pré-filtrados por similaridade de cosseno do
embedding da descrição, para evitar explosão combinatória de N².

## Regra de ramificação

- Nós `branch` podem ganhar filhos da estrutura original do roadmap
  **e/ou** propostos pela IA quando ela julgar que o tópico merece mais
  profundidade do que a fonte mostra.
- **Limite: no máximo 5 filhos novos por nó, por passada de
  classificação** — soma de filhos vindos da fonte original + propostos
  pela IA nessa passada. Isso evita explosão de custo numa única
  passada.
- Não há limite de profundidade nem de crescimento ao longo do tempo:
  um filho pode virar `branch` de seus próprios filhos depois, quando o
  usuário chegar até ele — cada passada futura tem seu próprio limite de
  5, independente das anteriores.
