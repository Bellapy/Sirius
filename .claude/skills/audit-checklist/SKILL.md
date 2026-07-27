---
name: audit-checklist
description: Use imediatamente após gerar o texto de um nó (generated_content.texto), antes de salvá-lo como definitivo. Define o checklist mecânico de auditoria (checagem de conexões contra a lista fechada de arestas + checagem de conteúdo de enchimento), o formato de resposta esperado (aprovado / reprovado + motivo), e o fluxo de retentativa (máx. 2 tentativas reprovadas, depois marcar "revisar manualmente"). Não usar para escrever o conteúdo em si (ver skill content-templates) nem para classificar node_type/arestas (ver skill node-classification-branching).
---

# Checklist de auditoria de conteúdo gerado

A auditoria é uma **segunda chamada separada**, que não escreveu o texto
original — modelo Haiku, checagem mecânica contra lista fechada.

## O que checar

1. **Toda conexão mencionada no texto está na lista de arestas fornecida
   ao gerador?** (mesma lista que foi passada como insumo fechado na
   geração — ver skill `content-templates`, seção anti-alucinação). Se o
   texto menciona uma relação com outro nó que não está na lista →
   reprovar.
2. **O texto não é conteúdo de enchimento artificial?** (frases vazias,
   padding para parecer mais completo sem agregar substância).

## Formato de resposta

Só duas saídas possíveis:
- `aprovado`
- `reprovado + motivo` (motivo curto e específico, referenciando qual
  checagem falhou)

## Fluxo de retentativa

1. Se reprovado: regenerar o conteúdo incluindo o motivo da reprovação
   no prompt de geração.
2. Máximo **2 tentativas de geração no total** (a original + 1
   regeneração). Se as 2 forem reprovadas, **parar** de tentar
   automaticamente — marcar o nó como "revisar manualmente" em vez de
   insistir. Não existe uma 3ª tentativa automática.
3. Registrar cada tentativa (aprovada ou não) no histórico de auditoria
   do nó (`generated_content.auditoria: [...]`).
