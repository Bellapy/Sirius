# CriadorDeMapas

Sistema pessoal (uso individual, sem login) que transforma roadmaps do
roadmap.sh em trilhas de estudo profundas e interligadas, geradas por IA,
com validação de aprendizado via mentoria socrática. Especificação
completa em [docs/especificacao_tecnica.md.md](docs/especificacao_tecnica.md.md)
— leia lá antes de qualquer trabalho estrutural. Regras específicas de
templates de conteúdo, classificação/ramificação de nó e auditoria estão
nas skills correspondentes em `.claude/skills/`, não aqui.

## Restrição de custo

Meta: estudar um roadmap inteiro (geração + mentoria) custa menos de
~$4 USD. Isso é requisito de engenharia, não opcional:

- Toda chamada de IA passa antes por uma interface abstrata com
  implementação **simulada** (fixtures, sem custo) e implementação
  **real** (API Anthropic). Construir e testar contra a simulada
  primeiro; só habilitar chamada real após aprovação explícita do
  usuário, começando por um único nó de teste.
- Cache de prompt obrigatório em toda chamada que reutiliza instruções
  fixas.
- Batch API obrigatória para classificação estrutural e de arestas.
- Nunca gerar conteúdo em lote antecipado — só sob demanda, quando o
  usuário abre o nó.
- Nunca usar Opus ou raciocínio estendido nesse sistema.

## Roteamento de modelo por tarefa

| Tarefa | Modelo |
|---|---|
| Classificação de tipo de nó | Haiku |
| Classificação de arestas | Haiku |
| Geração de conteúdo (templates A/B/C) | Sonnet, sem extended thinking |
| Auditoria de conteúdo | Haiku |
| Sessão de Mentoria | Sonnet, sem extended thinking |
