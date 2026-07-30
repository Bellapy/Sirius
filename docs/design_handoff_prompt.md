# Prompt para IA de design — redesign visual do Sirius

> Este arquivo é o prompt pronto para ser enviado a uma IA especializada em
> design de interfaces. Ele documenta o sistema e todas as telas existentes
> em detalhe suficiente para alguém que nunca viu o projeto. **Não descreve
> nem pede mudança de nenhuma regra de negócio, fluxo ou funcionalidade —
> só o design visual.**

---

## 1. Contexto do sistema

O **Sirius** é um sistema pessoal (uso individual, sem login, sem
multiusuário) que transforma roadmaps técnicos do
[roadmap.sh](https://roadmap.sh) (ex: "Backend", "DevOps", "System Design")
em trilhas de estudo profundas, com conteúdo gerado por IA e validação de
aprendizado por meio de uma mentora socrática (também IA). O usuário é um
desenvolvedor estudando sozinho, num navegador desktop, provavelmente por
sessões longas (por isso a app precisa ser confortável de olhar por horas,
sem cansar a vista).

Princípio central do produto: **nenhum conceito recebe explicação rasa** —
a app não é uma lista de tarefas gamificada, é uma ferramenta de estudo
séria. Por isso o design deve evitar qualquer estética de "app de hábito"
(sem confete, sem streak, sem contador de dias, sem emoji decorativo).

É uma SPA React rodando localmente (não hospedada publicamente), consumindo
uma API REST própria. O grafo de tópicos é renderizado com a biblioteca
**react-flow** (importante: qualquer proposta de design para a tela de
Estudo precisa ser implementável estilizando os elementos DOM que o
react-flow gera — nós como `<div>` posicionados por `transform`, um canvas
com zoom/pan nativo, controles de zoom no canto — não dá pra trocar por uma
lib de canvas totalmente diferente).

O idioma da interface é **português do Brasil**, e deve continuar sendo.

### Modelo de dados relevante para o design

- Todo **tópico/nó** do grafo tem um `node_type`, sempre um destes três,
  usado para estudo (e hoje também para a forma visual do nó no grafo):
  - `branch` — um tópico "guarda-chuva" que se ramifica em sub-tópicos
    (ex: "Bancos de Dados").
  - `atomic_comparable` — um tópico que faz mais sentido comparado a
    alternativas (ex: "PostgreSQL" vs "MySQL").
  - `atomic_conceptual` — um conceito isolado (ex: "Idempotência").
- Todo nó tem um `status` de progresso, com uma regra de negócio
  importante que **o design precisa comunicar visualmente sem ambiguidade**:
  - `nao_iniciado` — o usuário nunca abriu esse tópico.
  - `lido` — o usuário já abriu e leu o conteúdo gerado.
  - `validado` — a mentora de IA confirmou, ao final de uma sessão de
    mentoria, que o usuário realmente entendeu o assunto (não decorou).
    **`validado` nunca é setado por um clique manual do usuário** — só a
    mentoria consegue promover um nó a esse estado. O design deve deixar
    claro que esse é um selo "conquistado", não uma caixinha que se marca
    sozinho.
- Nós têm arestas entre si (`prerequisite_of`, `alternative_to`,
  `contrasts_with`, `composes_with`, `applied_in`) — hoje só
  `prerequisite_of` é usado visualmente (define hierarquia pai/filho no
  grafo); as outras aparecem como rótulo de texto na aresta quando
  presentes.

---

## 2. Diretrizes visuais (obrigatórias)

- **Paleta**: tons terrosos, escura. Elegante e de baixo contraste — não é
  um dashboard SaaS genérico claro, é pensada pra sessões longas de
  leitura/estudo sem cansar a vista.
- **Aparência**: moderna, elegante, profissional — nível de um produto SaaS
  premium atual. **Evitar qualquer aparência genérica ou "cara de IA"**
  (gradientes clichê, glow roxo/azul padrão de ferramenta de IA, ícones
  fofos, emojis, cards com sombra exagerada tipo Bootstrap default).
- **Hierarquia visual**: clara em cada tela — deve ficar óbvio à primeira
  vista qual é a informação mais importante daquela tela.
- **Espaçamento e alinhamento**: generosos e intencionais, não apertados.
- **Tipografia**: bem definida, com escala clara entre título de página,
  subtítulos e corpo de texto. (A versão atual usa Space Grotesk para
  títulos e Atkinson Hyperlegible para corpo — pode manter, trocar ou
  ajustar a combinação, mas a lógica de "uma fonte com personalidade pros
  títulos + uma fonte muito legível pro corpo" deve se manter, pois o corpo
  de texto é conteúdo educacional denso, lido por longos períodos.)
- **Componentes consistentes**: botões, badges, cards, inputs devem seguir
  um mesmo sistema em todas as telas — nada de cada tela inventar seu
  próprio estilo de botão.
- **Ícones**: só quando agregam valor real (ex: indicar direção, estado);
  nunca como decoração.
- **Acessibilidade/contraste**: alto o suficiente pra leitura confortável
  mesmo sendo um tema escuro de baixo contraste — texto principal precisa
  ser legível sem esforço.
- **Cantos e sombra**: se usar sombra, sutil (profundidade discreta, não
  cards "flutuando" agressivamente); raio de borda suave, não exagerado.
- **Zero gamificação vazia**: sem confete, sem streak, sem badge de
  "conquista" fofo, sem cor vibrante de celebração. A única "recompensa"
  visual do sistema é o preenchimento do nó quando ele é validado pela
  mentora — e isso deve parecer merecido/sóbrio, não uma animação de jogo.

### O que já foi tentado (contexto, não é pra copiar)

A versão atual usa um tema escuro terroso (fundo `#1f1b16`, texto creme
`#f1e7d6`, accent terracota `#c99566`), Space Grotesk + Atkinson
Hyperlegible, cards com `border-radius` entre 10–22px e sombras bem sutis.
Cumpre o brief tecnicamente mas está sendo considerada "sem vida" pelo
stakeholder — sinta-se livre pra propor uma direção nova dentro dessas
diretrizes (paleta terrosa, escura, elegante), não precisa preservar esses
tokens exatos. O que **não pode mudar** é o que está descrito na seção 1
(regras de negócio, estados, fluxos).

---

## 3. Estrutura global (presente em todas as telas)

### 3.1 Barra de navegação (topo, fixa)

- Fica no **topo**, nunca lateral — decisão de produto, não é negociável.
- Contém: nome do produto ("Sirius") à esquerda, e 4 abas de navegação:
  **Mapas, Estudo, Mentoria, Revisão** (nessa ordem, é a ordem de
  prioridade de uso).
- A aba ativa tem destaque visual (hoje: fundo levemente colorido + cor de
  texto diferenciada).
- Não há menu lateral, não há segundo nível de navegação, não há avatar de
  usuário (sistema é single-user, sem conta/login).

### 3.2 Banner de erro global

- Quando qualquer chamada à API falha, uma faixa de erro aparece **logo
  abaixo da barra de navegação**, ocupando a largura toda, com a mensagem
  de erro e um botão "fechar".
- É transitório — não é uma tela, é uma notificação inline que o usuário
  dispensa manualmente.

### 3.3 Container de conteúdo

- Abaixo do banner (quando presente), a área de conteúdo da aba ativa
  ocupa o resto da tela.
- Duas variantes de layout hoje:
  - **Largura controlada, com padding generoso e centralizada** — usada em
    Mapas e Revisão (listas).
  - **Full-bleed** (ocupa 100% da altura/largura disponível, sem padding
    de página) — usada em Estudo, porque o grafo precisa do espaço todo.
  - **Centralizada vertical E horizontalmente, "modo zen"** — usada em
    Mentoria (ver seção 3.6).

---

## 4. Tela: Mapas

### Objetivo

Ponto de entrada do sistema. O usuário escolhe qual roadmap técnico quer
estudar. É a primeira tela que qualquer usuário vê.

### Fluxo de uso esperado

1. Usuário abre o app → cai em Mapas.
2. Vê uma lista de todos os roadmaps disponíveis (hoje ~90, vindos do
   repositório open-source `developer-roadmap`) — nomes técnicos como
   `backend`, `frontend`, `devops`, `system-design`, `python`, etc.
3. Pode digitar num campo de busca pra filtrar a lista por nome.
4. Para um roadmap ainda não estudado, clica em "Importar" — isso dispara
   duas chamadas de API em sequência (importar estrutura + classificar
   tópicos), com feedback de carregamento no próprio botão. Pode demorar
   alguns segundos.
5. Depois de importado, o mesmo item da lista passa a mostrar "Abrir" no
   lugar de "Importar".
6. Clicar em "Abrir" leva para a aba Estudo, já com aquele roadmap
   carregado.

### Componentes presentes

- Título de página ("Mapas") + parágrafo curto de explicação abaixo do
  título (o que a tela faz, resumidamente).
- Campo de busca/filtro (input de texto simples, sem botão de busca
  separado — filtra em tempo real conforme digita).
- Lista de roadmaps, organizada como **grade de cards** (não uma lista
  vertical única) — cada card tem:
  - Nome do roadmap (slug técnico, ex: "backend").
  - Uma linha de status abaixo do nome: "ainda não importado" ou
    "importado e pronto para estudo".
  - Um botão de ação à direita: "Importar" (com estado de carregamento
    "Importando...") ou "Abrir" (destacado/primário), dependendo do
    status.
- Estado vazio: se o filtro não bate com nenhum roadmap, mostra uma
  mensagem simples "Nenhum roadmap encontrado para '{termo buscado}'."

### Hierarquia visual atual

1º nome do roadmap (mais importante — é o que o usuário está escaneando),
2º o botão de ação (precisa ser claramente clicável), 3º o status
textual (apoio, pode ser discreto).

### Estados possíveis

- **Carregando** (inicial): a lista inteira ainda não chegou da API —
  mostra um indicador de carregamento simples no lugar da lista.
- **Erro**: a chamada pra listar roadmaps falhou — mostra mensagem de erro
  no lugar da lista.
- **Vazio (por filtro)**: lista carregada, mas filtro não bate com nada.
- **Item individual "importando"**: um card específico mostra o botão em
  estado de carregamento enquanto a importação está em andamento; os
  outros cards continuam normais e clicáveis.
- Não existe estado de "seleção múltipla" ou "edição" nessa tela — é
  puramente navegacional.

### Ações do usuário

- Filtrar por texto.
- Importar um roadmap (ação que dispara duas chamadas de API em cadeia).
- Abrir um roadmap já importado (navega para Estudo).

### Informação mais importante

O nome do roadmap e se ele já está pronto pra ser estudado ou não — o
usuário está essencialmente escaneando essa lista pra decidir "o que eu
vou estudar hoje".

### Relação com outras telas

É o ponto de partida. "Abrir" leva direto pra Estudo com o roadmap
selecionado carregado.

---

## 5. Tela: Estudo

### Objetivo

Onde o usuário efetivamente navega pelos tópicos de um roadmap, lê o
conteúdo gerado de cada um, e decide o que estudar em seguida. É a tela
mais usada e mais complexa do sistema.

### Fluxo de uso esperado

1. Usuário chega vindo de Mapas (ou volta pra essa aba já com um roadmap
   selecionado anteriormente na sessão).
2. Vê um **grafo visual navegável** dos tópicos — mas não o grafo inteiro
   de uma vez (um roadmap típico tem 100+ tópicos; mostrar tudo de uma vez
   é ruim). Em vez disso:
   - A visão inicial ("Visão geral") mostra só os tópicos de **topo**
     (tópicos que não são pré-requisito de nenhum outro, ou seja, as
     "portas de entrada" do roadmap).
   - Cada tópico que tem sub-tópicos mostra um indicador visual sutil de
     que "tem mais coisa dentro".
   - Clicar num tópico abre um **painel de detalhe** (lateral, sem sair da
     tela) mostrando o conteúdo daquele tópico.
   - Se aquele tópico tiver sub-tópicos, o painel mostra um botão "Ver
     sub-tópicos (N)" — clicar nisso troca a visão do grafo para mostrar
     **só os filhos diretos** daquele tópico (drill-down), e fecha o
     painel.
   - Uma **trilha de navegação (breadcrumb)** no topo do grafo mostra o
     caminho percorrido ("Visão geral › Bancos de Dados › ...") e cada
     item dela é clicável pra voltar a qualquer nível anterior.
3. Ao clicar num tópico sem conteúdo ainda gerado, o sistema **gera o
   conteúdo na hora** (chamada de IA em tempo real) — leva alguns
   segundos, com indicador de carregamento visível.
4. Depois de ler, o usuário pode clicar em "Iniciar Mentoria" (dentro do
   painel de detalhe) pra ser testado sobre aquele tópico — isso navega
   pra aba Mentoria.

### Componentes presentes

**Painel principal (grafo)**:
- Barra de breadcrumb (trilha de navegação) no topo da área do grafo.
- Canvas do grafo em si (biblioteca react-flow): nós (caixas com o nome do
  tópico) conectados por linhas/arestas, com zoom e pan livres pelo mouse.
  Tem controles nativos de zoom (+/-/enquadrar tudo) fixados num canto do
  canvas.
- Uma barra de legenda fixada embaixo do canvas, explicando o significado
  visual de cada estado/forma de nó (ver "Estados" abaixo) — é texto de
  apoio, sempre visível, baixo contraste.

**Painel de detalhe (lateral, aparece só quando um nó está selecionado)**:
- Botão "Fechar" no topo.
- Título = nome do tópico.
- Duas etiquetas (badges) lado a lado: o tipo do tópico (ramificação /
  atômico comparável / atômico conceitual) e o status de progresso
  (não iniciado / lido / validado).
- Corpo: o conteúdo gerado do tópico, em texto formatado (títulos,
  subtítulos, parágrafos, listas — é conteúdo educacional real, similar a
  um artigo técnico).
- Se o conteúdo reprovou auditoria automática 2 vezes (situação rara, de
  qualidade), aparece um aviso destacado no topo do corpo avisando que
  esse conteúdo "precisa de revisão manual".
- Rodapé fixo do painel com até dois botões: "Ver sub-tópicos (N)" (só se
  o nó tiver filhos) e "Iniciar Mentoria" (desabilitado até o conteúdo
  terminar de carregar).

### Hierarquia visual atual

No grafo: a forma/preenchimento do nó é a informação mais importante
(estado de progresso > tipo do tópico > label do texto, nessa ordem de
prioridade visual). No painel de detalhe: nome do tópico > badges de
estado > conteúdo em si > ações no rodapé.

### Estados possíveis

- **Sem roadmap selecionado**: mensagem simples pedindo pra escolher um
  roadmap na aba Mapas primeiro.
- **Carregando o grafo**: indicador de carregamento no lugar do canvas.
- **Erro ao carregar o grafo**: mensagem de erro.
- **Estado de cada nó individual no grafo** (é o estado mais importante do
  sistema inteiro, visualmente falando):
  - `nao_iniciado` → hoje: só contorno, sem preenchimento.
  - `lido` → hoje: preenchimento parcial/translúcido.
  - `validado` → hoje: preenchimento total, cor de destaque — precisa
    parecer "conquistado", não uma cor de sucesso genérica de formulário.
  - Independente do status, a **forma/borda** do nó também comunica o
    `node_type` (hoje: ramificação = cantos quase retos; atômico
    comparável = cantos moderadamente arredondados; atômico conceitual =
    formato pílula/totalmente arredondado).
  - Nó com sub-tópicos tem um indicador visual extra (hoje: "···" sutil
    abaixo do texto).
- **Painel de detalhe carregando conteúdo pela primeira vez**: indicador
  de carregamento flutuante enquanto a IA gera o texto.
- **Painel de detalhe com conteúdo pronto**: estado normal de leitura.
- **Painel de detalhe com conteúdo reprovado 2x na auditoria**: aviso
  vermelho/atenção no topo do corpo.
- **Botão "Iniciar Mentoria" desabilitado**: enquanto o conteúdo ainda não
  carregou.

### Ações do usuário

- Fazer zoom/pan no grafo.
- Clicar num nó → abre painel de detalhe (gera conteúdo se necessário).
- Fechar o painel de detalhe.
- Clicar em "Ver sub-tópicos" → drill-down (troca o conjunto de nós
  mostrados no grafo).
- Clicar em qualquer item do breadcrumb → volta pra aquele nível.
- Clicar em "Iniciar Mentoria" → navega pra aba Mentoria com uma sessão
  iniciada sobre aquele tópico.

### Informação mais importante

No grafo: **quais tópicos já foram validados** (dá o senso de progresso
real) e **quais têm mais profundidade escondida** (pra saber onde
explorar). No painel: o conteúdo do tópico em si — é a peça de leitura
principal do produto inteiro.

### Comportamento específico que influencia o design

- O grafo pode ter dezenas de nós visíveis ao mesmo tempo (mesmo com
  drill-down, alguns níveis têm 20-40 nós de topo) — o design dos nós
  precisa continuar legível em densidade média/alta, não só isolado.
- O painel de detalhe ocupa uma fatia lateral da tela **sem cobrir o
  grafo inteiro** — os dois ficam visíveis ao mesmo tempo.
- É a única tela com uma barra de navegação secundária (o breadcrumb) —
  ela reduz a carga cognitiva de "onde eu estou dentro da árvore de
  tópicos".

### Relação com outras telas

Vem de Mapas (roadmap selecionado). Leva pra Mentoria (botão "Iniciar
Mentoria"). É a tela de onde se acessa qualquer conteúdo gerado.

---

## 6. Tela: Mentoria

### Objetivo

Testar se o usuário realmente entendeu um tópico (não decorou), através de
perguntas socráticas feitas por uma IA mentora. É o único jeito de um nó
virar `validado`.

### Fluxo de uso esperado

1. Usuário chega vindo do botão "Iniciar Mentoria" em Estudo (ou "Refazer"
   em Revisão) — nunca navega direto pra essa aba sem uma sessão ativa
   vinda de outro lugar.
2. Vê **uma pergunta por vez**, feita pela mentora, apresentada de forma
   grande e central na tela — nada mais compete por atenção.
3. Escreve a resposta num campo de texto livre, abaixo da pergunta.
4. Clica em "Responder" → a resposta é enviada, e a **pergunta na tela é
   substituída** pela próxima pergunta/comentário da mentora. **Não fica
   um histórico de mensagens acumulando na tela** — é sempre só a
   pergunta atual visível, não é uma interface de chat/WhatsApp.
5. Pode repetir esse ciclo quantas vezes quiser.
6. A qualquer momento, pode clicar em "Encerrar sessão" — isso pede pra
   mentora dar um veredito final (aprovado/reprovado), mas **esse veredito
   nunca é mostrado ao usuário como nota ou resultado explícito** — ele só
   atualiza o estado do nó por trás (visível depois na tela de Estudo).
   Depois de encerrar, o usuário só vê uma confirmação neutra de que a
   sessão terminou e o estado foi atualizado.

### Componentes presentes

- Um rótulo pequeno acima do card principal, indicando sobre qual tópico
  é a sessão atual (discreto, não é o foco).
- Um card grande e centralizado (na tela toda, tanto horizontal quanto
  verticalmente) contendo só a pergunta/fala atual da mentora, em
  destaque tipográfico.
- Abaixo do card: campo de texto multi-linha pra resposta do usuário.
- Dois botões abaixo do campo: "Responder" (ação principal) e "Encerrar
  sessão" (ação secundária/destrutiva-leve, mais discreta).
- Tela de encerramento: mensagem curta confirmando que a sessão terminou e
  que o estado do nó foi atualizado, com um botão "Voltar".
- Estado sem sessão ativa: mensagem explicando que não há sessão ativa e
  onde iniciar uma (nem chegar aqui direto faz sentido sem vir de outro
  lugar).

### Hierarquia visual atual

A pergunta da mentora é, disparadamente, o elemento mais importante da
tela — deve ser a primeira coisa que os olhos encontram. Tudo o resto
(rótulo do tópico, botões) é deliberadamente secundário.

### Estados possíveis

- **Sem sessão ativa**: mensagem de orientação, sem card nem formulário.
- **Sessão ativa, aguardando resposta**: pergunta visível, campo de texto
  vazio, botão "Responder" desabilitado até haver texto digitado.
- **Enviando resposta**: botão "Responder" mostra indicador de
  carregamento, campo de texto e botões ficam bloqueados brevemente.
- **Erro ao enviar**: mensagem de erro discreta abaixo do campo de texto,
  sem perder o que foi digitado.
- **Sessão encerrada**: card de pergunta desaparece, mostra só a mensagem
  de confirmação neutra.

### Ações do usuário

- Escrever e enviar uma resposta (ciclo repetível).
- Encerrar a sessão a qualquer momento.
- Voltar (depois de encerrada) — retorna ao estado "sem sessão ativa".

### Informação mais importante

A pergunta atual. Literalmente só isso deveria competir por atenção nessa
tela — é intencionalmente um "modo foco".

### Comportamento específico que influencia o design

- **Não pode parecer um app de chat/mensageria** — sem bolhas de
  conversa, sem histórico visível, sem avatar da mentora. É mais parecido
  com um cartão de flashcard/entrevista do que um chat.
- O veredito (aprovado/reprovado) é **deliberadamente escondido** do
  usuário nessa tela — o design não deve tentar "revelar" essa informação
  de forma implícita (tipo cor do botão de encerrar mudando) — a intenção
  de produto é que o usuário só descubra o resultado voltando pra Estudo e
  vendo o nó preenchido ou não.

### Relação com outras telas

Só é alcançável a partir de Estudo ou Revisão (nunca via navegação direta
sem contexto). Depois de encerrada, o resultado é refletido visualmente
de volta em Estudo (nó fica `validado` ou continua como estava) e um novo
registro aparece em Revisão.

---

## 7. Tela: Revisão

### Objetivo

Listar tópicos que já passaram por pelo menos uma sessão de mentoria,
priorizando os que **ainda não foram validados**, pra incentivar o usuário
a refazer/tentar de novo.

### Fluxo de uso esperado

1. Usuário abre a aba Revisão.
2. Vê uma lista de tópicos com sessão de mentoria prévia — os **não
   validados aparecem primeiro** (são a prioridade).
3. Cada item mostra o nome do tópico, o roadmap de origem, e um indicador
   claro de validado/não validado.
4. Clica em "Refazer" → inicia uma nova sessão de mentoria sobre aquele
   tópico, navegando pra aba Mentoria.

### Componentes presentes

- Título de página ("Revisão") + parágrafo curto explicando o critério de
  ordenação (não validados primeiro).
- Lista em grade de cards (mesmo padrão visual da lista de Mapas), cada
  card com:
  - Nome do tópico.
  - Nome do roadmap de origem (informação secundária/apoio).
  - Uma etiqueta (badge) indicando "validado" ou "não validado".
  - Botão "Refazer".
- Estado vazio: mensagem simples avisando que ainda não há nenhuma sessão
  de mentoria registrada.

### Hierarquia visual atual

Nome do tópico > etiqueta de validado/não validado (esse status é o
motivo de a lista existir, merece destaque) > roadmap de origem > botão de
ação.

### Estados possíveis

- **Carregando**: indicador de carregamento no lugar da lista.
- **Erro**: mensagem de erro.
- **Vazio**: nenhuma sessão de mentoria ainda existe no sistema.
- **Lista normal**: itens ordenados com não-validados primeiro.

### Ações do usuário

- Clicar em "Refazer" num item → inicia nova sessão de mentoria sobre
  aquele tópico (navega pra Mentoria).

### Informação mais importante

O status validado/não-validado de cada item — é literalmente o critério
de ordenação e o motivo de existir dessa tela.

### Relação com outras telas

Populada pelo histórico de sessões geradas em Mentoria. "Refazer" leva de
volta pra Mentoria. Concettualmente é uma "fila de pendências" que só
existe depois que o usuário já passou por pelo menos uma sessão de
mentoria em algum tópico.

---

## 8. Resumo cross-tela: o que precisa ser consistente

- **Sistema de estados de progresso** (não iniciado / lido / validado)
  aparece de formas diferentes em 3 lugares (nó do grafo em Estudo, badge
  no painel de detalhe, badge em Revisão) — precisam usar a mesma
  linguagem visual (mesma cor "validado" em todo lugar, por exemplo).
- **Sistema de badges/etiquetas** (tipo de tópico, status) deve ser um
  único componente reutilizado, não reinventado por tela.
- **Botões primário vs. secundário vs. desabilitado** precisam de
  hierarquia visual clara e consistente em todas as 4 telas.
- **Estados de carregamento e erro** devem ter o mesmo padrão visual em
  toda a aplicação (hoje: um spinner pequeno + texto, e mensagens de erro
  em vermelho/terracota escuro).
- **Cards de lista** (Mapas e Revisão) devem parecer parte do mesmo
  sistema de design.

---

## 9. O que pedir à IA de design

Com base em tudo isso, proponha um **redesign visual completo e coeso**
das 4 telas (Mapas, Estudo, Mentoria, Revisão) mais a estrutura global
(barra de navegação, banner de erro), respeitando integralmente:

1. Todas as diretrizes visuais da seção 2 (paleta terrosa escura,
   moderna, elegante, SaaS premium, tipografia com hierarquia clara,
   espaçamento generoso, componentes consistentes, ícones só quando
   agregam valor, acessível, sofisticada, **nada de "cara de IA"
   genérica**).
2. Todos os fluxos, estados, componentes e regras de negócio descritos
   nas seções 3 a 7, sem remover, adicionar ou alterar nenhuma
   funcionalidade — só a forma visual.
3. A consistência cross-tela descrita na seção 8.
4. As restrições técnicas: é uma SPA React, o grafo da tela Estudo é
   renderizado por react-flow (nós são `<div>`s posicionados por CSS
   transform dentro de um canvas com pan/zoom nativo — a proposta de
   design pode estilizar esses elementos livremente via CSS, mas não pode
   assumir uma tecnologia de renderização diferente pra esse componente
   específico).

Entregue: paleta de cores final (com valores hex), sistema tipográfico
(fontes + escala de tamanhos), sistema de espaçamento, especificação
visual de cada componente reutilizável (botão primário/secundário/
desabilitado, badge, card, input, breadcrumb, nó do grafo em cada
combinação de tipo×status), e uma descrição visual de cada uma das 4
telas montadas com esses componentes.
