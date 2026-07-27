---
name: content-templates
description: Use ao gerar o texto de explicação de um nó do grafo (chamada de IA que produz generated_content.texto). Define qual dos 3 templates (A/B/C) usar conforme node_type, a estrutura de seções de cada um, a regra anti-alucinação de interconexão via lista fechada de arestas, e a regra de isolamento de chamadas (1 nó, ou lote de 2-3 relacionados, por chamada — nunca múltiplos nós numa chamada só). Não usar para classificação de tipo de nó ou para auditoria — só para a geração do conteúdo em si.
---

# Templates de geração de conteúdo

Escolha do template é determinada por `node_type` — nunca um template genérico único.

## Template A — `atomic_comparable` (ex: PostgreSQL)

1. O que é
2. Por que existe (dor histórica que resolve)
3. Casos de uso reais
4. Trade-offs
5. Comparação direta com alternativas vizinhas no grafo
6. Como se conecta com o resto de um sistema real
7. Adoção de mercado

## Template B — `atomic_conceptual` (ex: idempotência)

1. O que é
2. Que problema resolve
3. Onde costuma falhar na prática (exemplo real de bug)
4. Onde se conecta com outros nós do grafo
5. Exemplo concreto de aplicação

## Template C — `branch` (ex: "Bancos de Dados")

1. O que é (definição direta da categoria)
2. Visão geral do ecossistema / panorama de mercado
3. Mapa de decisão: em qual sub-tópico entrar, dependendo do problema
4. Lista dos filhos, cada um com uma frase de gancho

## Regra anti-alucinação — interconexão obrigatória

Todo prompt de geração recebe como insumo fechado a lista real de arestas
daquele nó (`relation_type` + `confidence`). O prompt deve instruir o
modelo a **só** tecer na explicação as conexões dessa lista — nunca
inventar uma conexão nova. Isso é o que torna a auditoria mecanicamente
possível depois (ver skill `audit-checklist`).

## Regra de isolamento de chamadas

- Nunca gerar conteúdo de múltiplos nós numa única chamada de API.
- Cada nó (ou pequeno lote de 2-3 nós fortemente relacionados) recebe sua
  própria chamada isolada.
- O prompt de alta exigência (persona, regras anti-alucinação, formato do
  template) é repetido do zero em cada chamada — não acumular contexto
  longo entre nós, isso degrada qualidade.
- Modelo: Sonnet, sem raciocínio estendido (ver roteamento em CLAUDE.md).

## Timing — não gerar antecipado

Conteúdo só é gerado quando o usuário abre aquele nó pela primeira vez.
Nunca gerar em lote antecipado para nós ainda não visitados.
