# Sistema de trilhas de estudo com IA — especificação técnica

## Visão e objetivo

Sistema pessoal (uso individual, sem login) que transforma os roadmaps do
roadmap.sh em trilhas de estudo profundas e interligadas, geradas por IA,
com validação de aprendizado via mentoria socrática. Critério de sucesso:
em alguns meses, o usuário deve se sentir confiante o suficiente pra
conversar sobre os temas com outros desenvolvedores, se sair bem em
entrevistas técnicas, e tomar decisões de arquitetura no trabalho com
base no que aprendeu aqui.

Princípio inegociável: **nenhum conceito recebe explicação rasa**. O que
varia entre conceitos é a ramificação (quantos sub-tópicos ele merece),
nunca a qualidade ou profundidade da explicação em si.

## Restrição de custo — requisito de engenharia, não detalhe

O usuário paga a API do próprio bolso, separado do plano Claude.ai Pro.
Meta: manter o custo de estudar um roadmap inteiro (do zero até o fim,
incluindo mentoria) abaixo de ~$4 USD. Isso é obrigatório, não opcional:

- **Cache de prompt obrigatório** em toda chamada que reutiliza instruções
  fixas (templates, regras anti-alucinação, prompt da mentora).
- **Batch API obrigatório** para classificação estrutural e de arestas
  (não é uma tarefa urgente/em tempo real).
- **Geração de conteúdo sob demanda**, nunca antecipada em lote — ver
  seção "Timing de geração" abaixo.
- **Modo simulado obrigatório para desenvolvimento**: a camada de acesso
  à IA deve ser uma interface abstrata com duas implementações — uma
  real (API da Anthropic) e uma simulada (respostas fixas/fixture, sem
  custo). Todo o sistema deve ser construído e testado contra a versão
  simulada primeiro. Só trocar para chamadas reais depois de validado, e
  mesmo assim começando por um único nó de teste antes de qualquer lote
  maior.

## Roteamento de modelo por tarefa

| Tarefa | Modelo | Motivo |
|---|---|---|
| Classificação de tipo de nó (atômico comparável / atômico conceitual / ramificação) | Haiku | Tarefa mecânica, alto volume |
| Classificação de relações/arestas do grafo | Haiku | Idem |
| Geração de conteúdo (os 3 templates) | Sonnet, sem raciocínio estendido | Tarefa bem estruturada, não precisa de Opus |
| Auditoria de conteúdo gerado | Haiku | Checagem mecânica contra lista fechada de arestas |
| Sessão de Mentoria | Sonnet, sem raciocínio estendido | Precisa manter contexto e nuance conversacional |

Nunca usar Opus ou modo de raciocínio estendido ("extra thinking") nesse
sistema — não há tarefa aqui que justifique o custo.

## Fonte de dados

- Repositório open source `kamranahmedse/developer-roadmap` (GitHub),
  clonado localmente — não fazer scraping do site.
- Cada roadmap chega como estrutura JSON/YAML de nós + markdown de
  descrição por tópico.
- Licença do conteúdo do roadmap.sh não permite redistribuição pública —
  irrelevante aqui pois o uso é estritamente pessoal, mas não transformar
  isso num produto distribuído sem revisar a licença de novo.
- Suporte a múltiplos roadmaps, escolhidos livremente pelo usuário,
  cada um mantendo seu próprio grafo salvo e navegável.

## Schema do grafo

```
nodes: {
  id, label, roadmap_origin, description_md,
  node_type: 'atomic_comparable' | 'atomic_conceptual' | 'branch',
  embedding (vetor),
  generated_content: { template_usado, texto, auditoria: [...] } | null
}

edges: {
  source_id, target_id,
  relation_type: 'prerequisite_of' | 'alternative_to'
               | 'contrasts_with' | 'composes_with'
               | 'applied_in',
  origin: 'roadmap' | 'llm_inferred' | 'manual',
  confidence: float
}
```

## Pipeline de enriquecimento do grafo

1. Importar estrutura original do roadmap (vira arestas `origin: roadmap`,
   majoritariamente `prerequisite_of`).
2. Gerar embedding da descrição de cada nó.
3. Filtrar pares candidatos por similaridade de cosseno (evita explosão
   combinatória de N²).
4. Classificar a relação de cada par candidato com vocabulário fechado
   (as 5 categorias acima, nunca texto livre) — modelo Haiku, via Batch
   API.
5. Curadoria manual opcional em nós de alto valor (hubs de system
   design), mas não obrigatória para o MVP.

## Classificação automática de tipo de nó

Combinação de dois sinais, não um sozinho:

1. **Sinal estrutural (automático, sem custo de IA)**: centralidade no
   grafo (grau de conexão) calculada com lib de grafos (ex: `networkx`
   em Python) — indica candidato a `branch` se muitos filhos paralelos,
   ou `atomic_comparable` se tem arestas `alternative_to` no mesmo
   nível de abstração.
2. **Confirmação semântica (uma chamada Haiku curta por nó)**: recebe o
   nó + vizinhos diretos, confirma ou corrige a classificação do sinal
   estrutural.

## Regra de ramificação

- Nós classificados como `branch` podem ter filhos vindos da estrutura
  original do roadmap **e/ou** propostos pela IA quando ela julgar que o
  tópico merece mais profundidade do que a fonte mostra.
- Limite: no máximo **5 filhos novos por nó, por passada de
  classificação** (contando fonte original + propostos pela IA
  combinados) — evita explosão de custo numa única passada, mas permite
  crescimento orgânico ilimitado em profundidade ao longo do tempo real
  de uso.
- Sem limite de profundidade — um filho pode virar `branch` de seus
  próprios filhos depois, se e quando o usuário chegar até ele.

## Timing de geração (crítico para custo)

- **Estrutura (classificação de tipo de nó + arestas)**: passada única e
  barata (Haiku, Batch API) assim que o usuário escolhe um roadmap —
  gera o "mapa" visual completo (títulos, ramificações, conexões) sem
  gerar nenhum texto de explicação ainda.
- **Conteúdo (texto de explicação de cada template)**: gerado **apenas
  quando o usuário abre aquele nó pela primeira vez** — nunca em lote
  antecipado. Isso é o que mantém o custo proporcional ao uso real.

## Templates de geração de conteúdo

Escolhido por tipo de nó (nunca um template único genérico):

**Template A — atômico comparável** (ex: PostgreSQL)
1. O que é
2. Por que existe (dor histórica que resolve)
3. Casos de uso reais
4. Trade-offs
5. Comparação direta com alternativas vizinhas no grafo
6. Como se conecta com o resto de um sistema real
7. Adoção de mercado

**Template B — atômico conceitual** (ex: idempotência)
1. O que é
2. Que problema resolve
3. Onde costuma falhar na prática (exemplo real de bug)
4. Onde se conecta com outros nós do grafo
5. Exemplo concreto de aplicação

**Template C — ramificação** (ex: "Bancos de Dados")
1. O que é (definição direta da categoria)
2. Visão geral do ecossistema / panorama de mercado
3. Mapa de decisão: em qual sub-tópico entrar, dependendo do problema
4. Lista dos filhos, cada um com uma frase de gancho

### Interconexão obrigatória (anti-alucinação)

Todo prompt de geração recebe como insumo fechado a lista real de
arestas daquele nó (com `relation_type` e `confidence`) e é instruído a
**só** tecer na explicação as conexões dessa lista — nunca inventar uma
conexão nova livremente. Isso torna a interconexão auditável
mecanicamente (a auditoria confere se toda conexão mencionada no texto
corresponde a uma aresta real da lista).

### Geração em fases pequenas e isoladas

Nunca gerar conteúdo de múltiplos nós numa única chamada de API — cada
nó (ou pequeno lote de 2-3 relacionados) recebe sua própria chamada
isolada, com o prompt de alta exigência repetido do zero, para evitar
degradação de qualidade por acúmulo de contexto longo.

## Auditoria

Após gerar o conteúdo, uma segunda chamada (Haiku, separada, sem ter
escrito o texto original) recebe o texto + a lista de arestas fornecida
e responde só "aprovado" ou "reprovado + motivo", checando
mecanicamente:
- Toda conexão mencionada está na lista de arestas fornecida?
- O texto não é conteúdo de enchimento artificial?

Se reprovar, regenerar incluindo o motivo no prompt. Após 2 tentativas
reprovadas, marcar o nó como "revisar manualmente" em vez de insistir
automaticamente.

## Modo Mentoria

Baseado neste prompt de persona, já validado pelo usuário anteriormente
— usar como base direta, adaptando apenas para receber como contexto
inicial o conteúdo já gerado e salvo do nó em questão (não gera
explicação nova, só testa entendimento):

- Método socrático: nunca responder com explicação direta, sempre com
  perguntas direcionais.
- Restrição de vocabulário anti-decoreba: proibir jargão óbvio ao pedir
  que o usuário explique um conceito.
- Detecção de resposta decorada ("isso soa como definição de livro,
  como você explicaria pra sua avó?").
- Desafios práticos e cenários reais que forcem combinar conceitos
  (isso substitui a antiga "camada de síntese" separada — não existe
  mais como conteúdo pré-gerado, é comportamento emergente da mentoria).
- Ajuste dinâmico de dificuldade conforme o desempenho do usuário.
- Avaliação final estilo entrevista técnica sênior.
- **Sem monólogos longos** — a IA deve falar menos que o usuário.

Ao final da sessão, a Mentora emite um veredito separado da conversa
("validado: sim/não + motivo curto"), usado só para atualizar o estado
visual do nó — nunca exposto como nota ou pontuação ao usuário.

## Interface

- Roda como aplicação própria (não mais como Claude Artifact — decisão
  revertida ao optar por Claude Code), mas mantém os mesmos princípios
  de design já validados:
- Paleta calma, baixo contraste, tons terrosos/escuros — nunca tema
  claro de alto contraste. Cores de estado discretas (contorno = não
  iniciado, preenchimento parcial = lido, preenchimento total = validado
  pela mentora — nunca por clique manual do usuário).
- Sem elementos de gamificação vazia: sem confete, sem streak, sem
  contador de dias. Recompensa visual só ocorre quando a mentoria
  valida entendimento real.
- Tipografia: evitar serifa clássica (lembra e-commerce/editorial) —
  usar uma sans com personalidade para títulos (ex: Space Grotesk) e uma
  fonte otimizada para legibilidade prolongada no corpo (ex: Atkinson
  Hyperlegible), para reduzir fadiga visual.
- Barra de navegação **no topo**, nunca lateral.
- Abas: Mapas (escolher/continuar roadmap), Estudo (mapa interligado por
  fase), Mentoria (sessão de desafio único por vez, não histórico de
  chat contínuo), Revisão (perguntas/desafios salvos para refazer).
- Dentro de uma fase, os tópicos formam uma rede navegável livremente
  (não uma sequência forçada) — fases são a única sequência linear
  macro; dentro delas é rede, não trilho.
- Tela de Mentoria não deve parecer um chat tradicional: um
  desafio/pergunta por vez, resposta escrita, feedback direto e curto,
  sem histórico de bolhas acumulando na tela durante a sessão.

## Plano de implementação sugerido (fases para o Claude Code executar)

1. Estrutura de dados + parser do repositório roadmap.sh (sem IA ainda)
2. Camada de acesso à IA com interface abstrata (real + simulada) e
   roteamento de modelo por tarefa
3. Pipeline de enriquecimento do grafo (embeddings, classificação de
   arestas, classificação de tipo de nó) — testado 100% em modo simulado
   primeiro
4. Geração de conteúdo pelos 3 templates + auditoria — testado em modo
   simulado, depois validado com 1 nó real antes de qualquer lote
5. Persistência (progresso, sessões de mentoria, histórico de auditoria)
6. Interface: tela de Mapas → Estudo → Mentoria → Revisão, nessa ordem
   de prioridade de construção
7. Só then habilitar geração real em escala, com cache de prompt e
   Batch API já ativos desde o primeiro uso real
