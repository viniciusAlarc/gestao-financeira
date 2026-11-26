# Design do gestao-financeira

> **Estado: direção A escolhida pelo dono em 2026-11-25 e implementada no app.** A direção B
> fica como registro da alternativa. A auditoria foi feita em 25/11/2026 sobre `templates/`,
> `financas/static/financas/app.css` e o `manifest.webmanifest`, já com a rotina diária e a barra
> de seis abas.

## 1. O problema (auditoria curta)

O app não parece "de IA" por falta de componente, e sim por **falta de contraste de hierarquia e
de identidade**. Os pontos concretos:

| Onde | O que está hoje | Efeito |
| --- | --- | --- |
| Tela inicial | Três cartões iguais (`dl.painel`), rótulo de 11px em caixa alta e número de 2rem; o saldo só se diferencia pela cor | O saldo, o gasto e o previsto têm o mesmo peso; a ordem "saldo → fixo → gasto → previsto" não existe |
| Navegação no celular | Seis abas com rótulo de 10px (`0.625rem`); "Lançamentos" vira "Lançar"; o ativo é só um ponto de 4px | O texto é o menor da tela e o destino atual quase não se vê |
| Listas | Lançamentos e previstos usam a mesma linha de 44–52px, sem estados visuais | Pago, atrasado e vence hoje não se distinguem; o pago era apenas cinza |
| Leitura do mês | Previstos não tinha navegação de mês e a tela inicial somava o aberto de todos os meses | O mês não era uma unidade de leitura |
| Paleta | `--acento: #18181b` (quase preto), verde e vermelho só nos números | Correta, mas sem identidade; tudo é cinza-neutro |
| Tipografia | Fonte do sistema; títulos com o mesmo peso dos rótulos | Nenhum contraste de família ou de escala |
| PWA | Tema `#f6f7f9` | Claro e neutro; combina com o fundo, mas não dá personalidade |

O que **não** é problema: alvo de toque, foco visível, contraste de texto e a estrutura dos
formulários. As duas direções mantêm essas conquistas.

## 2. Direções propostas

Duas direções entregues, cada uma com amostra estática e sem rede. A escolha é do dono; nenhuma
foi aplicada.

### A — Papel e tinta · **escolhida em 2026-11-25**

- **Ideia:** editorial e quente. A hierarquia vem da tipografia e das linhas, não de cartões
  iguais; o saldo é um número grande sem caixa, e o fixo é um bloco de três colunas.
- **Paleta:** fundo `#F3EEE4` · superfície `#FBF8F1` · superfície alta `#EDE5D6` · linha
  `#D8CFBD` · texto `#211D16` · texto médio `#5A5244` · acento `#2F5D45` · positivo `#256B4E` ·
  negativo `#A23B2A` · atenção `#8A5A12`.
- **Tipografia proposta:** Fraunces nos títulos (SIL OFL 1.1, para self-host; **não baixada nesta
  tarefa**). Texto e números na fonte do sistema, com números tabulares. A amostra substitui a
  Fraunces por Georgia/Palatino.
- **Onde brilha:** leitura calma, cara de caderno; bom para o uso a dois.
- **Onde exige cuidado:** títulos serifados podem soar "retrô"; a fonte self-hosted precisa entrar
  no build.
- **Amostra:** `docs-dev/design/amostras/direcao-a.html`

### B — Noturno de bolso · alternativa não escolhida

- **Ideia:** painel escuro, denso e calmo. Superfícies em camadas e um único teal como acento;
  cartões arredondados; o saldo é um cartão e os números são sempre o herói.
- **Paleta:** fundo `#0F141B` · superfície `#161D26` · superfície alta `#1E2733` · linha
  `#2A3542` · texto `#F2F6FA` · texto médio `#B6C2CF` · acento e positivo `#5AC8B0` · negativo
  `#FF8A7A` · atenção `#F2C46D`.
- **Tipografia proposta:** Inter nos títulos e no texto (SIL OFL 1.1, para self-host; **não
  baixada nesta tarefa**). A amostra usa a fonte do sistema com peso 700 nos títulos e números
  tabulares.
- **Onde brilha:** contraste alto, leitura no escuro, cara de app de banco.
- **Onde exige cuidado:** tema escuro no PWA (`theme-color`, `manifest.webmanifest` e barra do
  sistema); legibilidade no sol; conferir contraste dos estados.
- **Amostra:** `docs-dev/design/amostras/direcao-b.html`

Uma terceira direção (alto contraste, monocromática) fica para depois da escolha, se o dono quiser
um contraste ainda maior. Duas opções fortes bastam para a decisão.

## 3. Princípios de componente

1. **Um número por bloco**, com rótulo curto e uma nota de uma linha. O número é o herói; não há
   chip de ícone em indicador.
2. **Fixo do mês em três partes** (entra fixo, sai fixo, sobra fixa). O texto deixa claro que o
   gasto do mês é o realizado e que os dois **não se somam**.
3. **Lista do mês** em ordem de vencimento, uma linha por item, alvo de toque ≥44px. O estado
   aparece por **texto + cor**, nunca só pela cor.
4. **Pago** é verde, com check e o rótulo "Pago"; aberto é neutro; atrasado e vence hoje têm
   estado próprio (a direção A mostra os três; a B mantém a mesma lógica).
5. **Navegação** com seis destinos. No celular, cinco na barra + "Mais" (A) ou seis com rótulo
   curto; o item ativo tem fundo tingido, não só um ponto.
6. **Formulários** com rótulo em cima, campo de 44px, erro ligado ao campo (`aria-describedby`) e
   um único botão primário.
7. **Números tabulares** em valores, datas e percentuais; descrição com quebra (`overflow-wrap`).
8. **Tokens no `:root`**; claro e escuro por token, sem cor solta no componente.

## 4. Anti-patterns (G19)

Vale para a rodada 2 e para qualquer peça nova:

- **Proibido filete colorido em aresta**: `border-left`/`border-top` de 2px ou mais, barra em
  `::before`/`::after`, `box-shadow: inset 3px 0 0` ou gradiente de parada dura fingindo filete.
- **Sem gradiente** em fundo de card ou header.
- **Sem chip de ícone colorido** em card de KPI/resumo.
- **Sem pílula grande de cor viva** (`border-radius: 50px`); raio pequeno.
- **Sem sombra pesada** em item de listagem.
- A cor de identidade vive no **texto, no número, no ponto ou no badge**; a borda do container não
  é portadora.
- Estado "selecionado" usa **contorno inteiro**, não faixa.
- **Reusar classe existente conta como escrever a peça**: copiar um `.note`/`.card` traz o filete
  junto.

## 5. O que a amostra não é

- Não é o app: HTML estático, dados inventados, sem JavaScript, sem rede e sem fonte baixada.
- A direção A foi escolhida; a B fica como registro da alternativa.
- Não altera `templates/`, `financas/` nem o PWA.

## 6. Próximo passo

1. A escolha (A) está registrada com data no `PROGRESS.md` e a direção foi implementada no app em
   2026-11-25: tokens, navegação de cinco abas + "Mais", início, lançamentos, previstos,
   relatório e tema do PWA.
2. Falta a fonte Fraunces self-hosted (SIL OFL 1.1): o app usa a serifa do sistema, como a
   amostra. Fica como P4-9.
3. Falta a conferência no celular e a 360/375px (P3-16).

## 7. Como abrir as amostras

Os arquivos abrem offline no navegador. Na vila, o link é:

- A: `http://localhost:4777/api/arquivo?path=/home/vinicius/Documents/Projetos-pessoais/gestao-financeira/docs-dev/design/amostras/direcao-a.html`
- B: `http://localhost:4777/api/arquivo?path=/home/vinicius/Documents/Projetos-pessoais/gestao-financeira/docs-dev/design/amostras/direcao-b.html`

Abaixo de 860px aparece a barra inferior; a partir de 860px, a navegação do topo. Abrir a 360px e
a 1280px para conferir a leitura e a ausência de rolagem horizontal.
