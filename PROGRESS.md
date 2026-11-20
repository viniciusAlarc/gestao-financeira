# gestao-financeira — Progresso

> Memória oficial do projeto (guardrail G5). Toda mudança de código entra aqui, na mesma
> resposta que a produziu. Mais recente no topo.

## 2026-11-19 — Relatório expande os gastos de cada categoria

**Pedido do dono:** na tela de relatórios, expandir cada categoria e ver os gastos que a compõem.

**O que mudou:**
- `financas/views.py`: o relatório agora carrega os movimentos do mês por categoria, com
  `select_related("categoria")`, mantendo a soma e o percentual por categoria.
- `templates/relatorio.html`: cada categoria é um `<details>` nativo (abre e fecha sem JS), com a
  data, a descrição e o valor de cada gasto.
- `financas/static/financas/app.css`: resumo com alvo de toque, chevron que gira ao abrir e lista
  interna discreta.
- `financas/tests.py`: teste de expansão (categoria, descrição e valor presentes no HTML).

**Testes:** 232, OK.

**Aberto:** o deploy (`git pull`, `collectstatic` e Reload) e a conferência no celular.

## 2026-11-19 — Categorização e recategorização do histórico concluídas (P2-15 fechado)

**Resultado:** o `importar_pluggy` rodou sem `--dry-run` e recategorizou o histórico; o relatório do
mês deixou de mostrar "Não categorizado" e passou a exibir as categorias do app (Compras, Moradia,
Transporte, Alimentação etc.). As transferências e o investimento ficaram fora do gasto.

**O que ficou pronto:**
- Mapa das 23 categorias da Pluggy, regras por descrição e fallback.
- A recategorização dos movimentos em "Não categorizado"; os já categorizados à mão foram preservados.
- A rotina de 2x/dia aplica o mapa aos novos movimentos.

**Aberto:** P3-9 (uso real), P3-10 (renovação), P3-12 (backup), P2-14/P2-16 (banco do PC).

**Testes:** 231, OK.

## 2026-11-19 — Mapa completo de categorias implementado (P2-15 em fechamento)

**Pedido do dono:** ampliar o mapa com as 23 categorias do histórico e recategorizar.

**O que mudou:**
- `MAPA_CATEGORIAS_PLUGGY` completo: Alimentação (Food delivery, Groceries, Eating out), Compras
  (Electronics, Shopping, Clothing), Transporte (Gas stations, Parking), Saúde (Pharmacy, Dentist,
  Hospital), Pets, Moradia (Services, Telecommunications), Cartão de crédito, Impostos, Investimento
  (fora do gasto), Salário, Rendimentos, Lazer (Digital services) e Transferência (Transfer - PIX,
  Same person transfer, Transfers; fora do gasto).
- Testes do mapa completo, das receitas, do investimento e das transferências; a suíte está em 231.

**Falta:** o deploy e a recategorização do histórico com backup antes; depois o relatório confirma.

**Testes:** 231, OK.

## 2026-11-19 — Recategorização do histórico ficou parcial (P2-15 em andamento)

**Resultado:** o comando rodou, mas o relatório do mês continuou com a maior parte em "Não
categorizado" e só uma transação em "Alimentação".

**Causa:** o mapa foi montado com as 3 categorias dos últimos 7 dias (Food delivery, Income taxes,
Transfers); o histórico tem outras categorias da Pluggy, que caíram no fallback. As regras por
descrição não cobriram as descrições do histórico.

**Próximo:** rodar o dry-run sem `--desde` para listar todas as categorias da Pluggy do histórico,
ampliar o mapa/regras e recategorizar de novo (com backup antes). O P2-15 continua em andamento.

## 2026-11-19 — Categorização automática implementada (P2-15 em fechamento)

**Pedido do dono:** categorizar automaticamente, sem retrabalho.

**Decisões do dono:** `Food delivery` → Alimentação; `Transfers` → Transferência fora do gasto;
recategorizar os já importados.

**O que mudou:**
- `financas/importacao_pluggy.py`: mapa da `category` da Pluggy (`Food delivery` → Alimentação,
  `Income taxes` → Impostos, `Transfers` → Transferência com `entra_no_gasto=False`), regras por
  descrição (`ifood`/`rappi`/`uber eats`, `darf`/`receita federal`, `transferencia entre contas`/
  `ted`) e fallback `Não categorizado`.
- O importador atualiza a categoria dos movimentos existentes que estão em `Não categorizado`
  quando revê a transação; preserva os categorizados à mão. O relatório ganhou `Atualizados`.
- O comando mostra `Atualizados`/`Seriam atualizados`.
- Testes: 9 novos em `CategoriaMappingTests`; a suíte está em 227.

**Falta:** criar as categorias "Alimentação" (despesa) e "Transferência" (despesa e receita, fora
do gasto) no app; o deploy; rodar o `importar_pluggy` sem `--desde` com `--dry-run` e depois com o
"pode" (G3) para recategorizar o histórico. O backup vem antes.

**Testes:** 227, OK.

## 2026-11-19 — Rotina automática validada (P2-21 fechado)

**Resultado:** o workflow `Importar Pluggy` rodou à mão no GitHub Actions e o endpoint respondeu
`200`. O primeiro teste deu `404` porque o servidor ainda não tinha o `git pull` + Reload; depois
disso, a rotina funcionou sem criar duplicata (os movimentos já estavam importados).

**O que ficou pronto:**
- Endpoint `POST /tarefas/importar-pluggy/` com `IMPORT_TOKEN` e `IMPORT_CONTA` no `.env` do
  servidor; o secret `IMPORT_TOKEN` no GitHub.
- Workflow duas vezes por dia (10:00 e 19:00 UTC = 07:00 e 16:00 em Brasília), com
  `workflow_dispatch` para rodar à mão. O endpoint importa os últimos 7 dias para reduzir o consumo
  de CPU do plano grátis.
- O MeuPluggy atualiza a cada 24h; a rotina diária é o teto útil.

**Aberto:** P2-15 (categorias automáticas), P3-9 (uso real), P3-12 (backup), P2-14/P2-16 (banco do
PC).

**Testes:** 218, OK.

## 2026-11-18 — Rotina automática de importação (P2-21 implementado, falta o deploy)

**Escolha do dono:** GitHub Actions (R$ 0), em vez do PythonAnywhere Developer (US$ 10/mês).

**O que mudou:**
- `financas/views.py`: endpoint `importar_pluggy_tarefa` com token no header e conta em
  `IMPORT_CONTA`; dispara o comando via `call_command`.
- `financas/urls.py`: rota `tarefas/importar-pluggy/`.
- `.github/workflows/importar-pluggy.yml`: workflow diário (09:00 UTC) + `workflow_dispatch`.
- `.env.example`: `IMPORT_TOKEN` e `IMPORT_CONTA`.
- `financas/tests.py`: 4 testes do endpoint (sem token, token errado, token certo e conta vazia).
- `docs-dev/a-codar/03-deploy-pythonanywhere.md`: seção de operação da rotina.

**Testes:** 218, OK (214 + 4 novos).

**Aberto:** o deploy (commit/push, `.env` com o token e a conta, secret no GitHub, `git pull` +
Reload) e o primeiro disparo manual. O MeuPluggy atualiza a cada 24h; a rotina diária é o teto útil.
O mapeamento de categorias (P2-15) continua aberto.

## 2026-11-18 — P2-13 fechado: importação da Pluggy validada

**Resultado:** dry-run, importação real, idempotência (Criados: 0 na segunda execução) e fuso do
`date` conferidos em 2026-11-18. A importação da fase 7 está concluída.

**O que falta:**
- **P2-15 (categorias automáticas):** o dono quer que os movimentos entrem categorizados, sem
  retrabalho. O dry-run mostra as categorias da Pluggy; a categorização da Pluggy pode ser
  trial-only. A decisão é mapear as categorias da Pluggy + regras por descrição, com "Não
  categorizado" como fallback.
- **P2-21 (rotina automática):** o MeuPluggy atualiza a cada 24h, então o teto útil é uma rotina
  diária. Opções: endpoint no app + GitHub Actions (R$ 0) ou upgrade do PythonAnywhere
  (US$ 10/mês), além do manual.
- P2-14/P2-16 continuam no banco do PC; P3-12 (backup) e P3-9 (uso real) seguem.

**Testes:** 214, OK.

## 2026-11-18 — Importação real da Pluggy concluída (P2-13 em fechamento)

**Resultado:** o `importar_pluggy` rodou contra a conta real no servidor, com o período escolhido,
e gravou os movimentos. O dono confirmou que a importação funcionou.

**O que foi feito:**
- `python manage.py importar_pluggy --conta "..."` no console do PythonAnywhere, sem `--dry-run`,
  depois do dry-run validado.
- Os movimentos entram com `origem = pluggy`, `id_externo` da transação, autoria do usuário técnico
  `Pluggy` e categoria `Não categorizado`.
- O banco do PC não foi tocado.

**O que falta:** provar a idempotência rodando o comando de novo (Criados: 0) e conferir o fuso do
`date` em uma transação conhecida. A decisão das categorias continua no P2-15.

**Testes:** 214, OK.

## 2026-11-18 — Dry-run da Pluggy validado (P2-12 fechado, P2-13 em andamento)

**Pedido do dono:** seguir a integração com a Pluggy.

**O que foi feito:**
- O dono criou/preencheu a **Demo App** no dashboard da Pluggy e o item do **MeuPluggy**, e
  cadastrou `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET` e `PLUGGY_ITEM_ID` no `.env` do servidor.
- O dry-run do `importar_pluggy` rodou contra a conta real no console do PythonAnywhere, sem gravar.
  A `api.pluggy.ai` está na allowlist do plano grátis e o `requests` usou o proxy.
- A aplicação em PRD foi enviada ao time de vendas; não é necessária para o uso pessoal. O Meu
  Pluggy continua após o trial de 15 dias.

**O que falta:** a importação real (P2-13), a conferência do fuso do `date` em uma transação
conhecida e a prova de idempotência rodando o comando de novo. A decisão das categorias segue no
P2-15; por ora, todo movimento importado cai em "Não categorizado".

**Testes:** 214, OK.

## 2026-11-18 — Pluggy está na allowlist do PythonAnywhere free (correção)

**Pergunta do dono:** se o plano atual permite a integração por API, inclusive com outra API ou
outro banco.

**Verificação:** a allowlist de saída do PythonAnywhere free
(`https://www.pythonanywhere.com/whitelist/`) inclui **`api.pluggy.ai`**. O cliente do projeto usa
`requests.Session()`, que aplica o proxy da conta automaticamente. Portanto a Pluggy **pode rodar no
plano grátis**. As entradas de 2026-11-17 que diziam o contrário estavam erradas: assumi que a API
não estava na lista sem conferir a allowlist completa.

**O que muda:** a P3-11 (Pluggy no plano grátis) deixa de existir. O que falta para a fase 7 é o
P2-12 (credenciais e `itemId` no `.env` do servidor) e o P2-13 (dry-run contra a conta real, agora
podendo rodar no próprio servidor).

**Não é preciso** trocar de banco nem de agregador: o bloqueio era o host, e a Pluggy já está
liberada nele. Outras APIs (Belvo, bancos) só funcionariam se estivessem na allowlist.

## 2026-11-18 — Lista de lançamentos mostra quem lançou

**Pedido do dono:** exibir o usuário que fez o lançamento.

**O que mudou:**
- `financas/views.py`: a lista de lançamentos passou a trazer `criado_por` no `select_related`,
  evitando uma consulta por lançamento.
- `templates/lancamentos.html`: cada item mostra "Lançado por <username>" abaixo da descrição e do
  valor.
- `financas/static/financas/app.css`: classe `.movimento-meta` discreta (texto suave, 12px).
- `financas/tests.py`: teste `test_lista_mostra_quem_lancou` em `DoisUsuariosTests`.

**Testes:** `.venv/bin/python manage.py test` → **214 testes, OK** (213 da base + 1 novo).

**Aberto:** a mudança ainda não está no servidor. Para aparecer em
https://viniciusapps.pythonanywhere.com é preciso commit, push, `git pull`, `collectstatic` (o CSS
mudou) e **Reload**.

## 2026-11-17 — Categorias e gastos fixos importados para o servidor (P2-20 fechado)

**Pedido do dono:** trazer as categorias e os gastos fixos do banco do PC para o MVP, em massa.

**O que foi feito:**
- Exportação no PC com `dumpdata financas.Conta financas.Categoria financas.GastoFixo --indent 2 >
  /tmp/iniciais.json`. A `Conta` entrou junto porque `GastoFixo.conta` é FK e a importação falharia
  sem ela. Movimentos e previstos ficaram de fora; o histórico fica no PC e o app gera o previsto do
  mês a partir dos gastos fixos.
- Conferência de que o banco do servidor estava vazio (0 contas, 0 categorias, 0 gastos) antes de
  importar.
- Upload do arquivo para `/home/viniciusapps/iniciais.json` (fora do repo) e `loaddata` no servidor.
- Ajustes no admin: nome da conta, saldo inicial, padrão/ativa, categorias e gastos fixos.
- Arquivos temporários apagados no servidor e no PC. O `db.sqlite3` do PC não foi tocado.

**Resultado:** conta, categorias e gastos fixos disponíveis no MVP; o lançamento rápido está
desbloqueado. A segunda conta de login e o uso real ficam na P3-9.

## 2026-11-17 — App no ar no PythonAnywhere (P2-18 e P2-19 fechados)

**Resultado:** o app está em **https://viniciusapps.pythonanywhere.com**, com HTTPS, tela de login
e CSS servido. O banco é novo (opção A, escolhida pelo dono depois de parar no passo 5 da opção B);
o `db.sqlite3` do PC não foi tocado.

**O que foi feito:**
- Repositório tornado público com `gh repo edit --visibility public`, porque o clone no
  PythonAnywhere falhou no privado. A varredura do histórico não achou `.env`, banco, certificado
  nem chave; o primeiro nome da segunda conta aparece nos documentos e em dois commits.
- Commit `3c71e26` com as configurações de produção (`STATIC_ROOT`,
  `SECURE_PROXY_SSL_HEADER`, cookies `Secure` e `CSRF_TRUSTED_ORIGINS`) enviado ao GitHub.
- No servidor: `git pull`, `.env` com `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS` e
  `DJANGO_CSRF_TRUSTED_ORIGINS`, `migrate` (banco novo, 0001-0006), `collectstatic` e o WSGI
  apontando para `config.settings`.
- O WSGI padrão foi colado com indentação e deu `IndentationError: unexpected indent`; corrigido
  apagando o arquivo e colando o código na coluna 1.
- A primeira tela de debug mostrou o `.env` ausente e o código antigo (`DEBUG=True`,
  `STATIC_ROOT=None`); o diagnóstico foi refeito com comandos de uma linha, porque o console
  embaralhou um bloco longo na colagem.

**Verificação externa:** `curl` em `/` → `/login/?next=/` **200**; `/static/financas/app.css`
**200**; HTML com manifest e ícones do PWA.

**Testes:** suíte local **213 OK** (sem mudança de código desde a última execução).

**Aberto:** cadastros iniciais no admin (P2-20), uso real a dois (P3-9), renovação mensal (P3-10),
backup semanal (P3-12) e a Pluggy no plano grátis (P3-11).

## 2026-11-17 — Publicação do MVP no PythonAnywhere (D6 revista, P3-3 fechado)

**Pedido do dono (2026-11-17):** publicar o MVP para a namorada usar, com solução básica e
acesso controlado; a ideia de um "link do Claude" foi descartada por não rodar Django.

**Decisão:** PythonAnywhere no plano Beginner (gratuito), registrada no dossiê D6
(`docs-dev/a-codar/02-decisao-d6-onde-roda.md`). Custo R$ 0; o app deixa de depender do PC de
casa. Limitações aceitas: web app expira a cada mês, 100 s de CPU/dia, 512 MB de disco e a API
da Pluggy não é acessível no plano grátis (allowlist de saída).

**Atualização (mesma data):** o dono criou a conta no PythonAnywhere (`viniciusapps`). Ele começou
pela opção B, parou no passo 5 e mudou para a **opção A (banco novo)**: o `migrate` no servidor cria
o banco do zero e o `db.sqlite3` do PC não é tocado. O deploy está em andamento (P2-18/P2-19).

**Repositório público (mesma data):** o repositório estava privado e o clone no PythonAnywhere
falhou; a pedido do dono, foi tornado público com `gh repo edit --visibility public`. A varredura do
histórico não encontrou `.env`, banco, certificado nem chave; o primeiro nome da segunda conta
aparece nos documentos e em dois commits.

**O que mudou:**
- `config/settings.py`: `STATIC_ROOT`, `SECURE_PROXY_SSL_HEADER`, cookies `Secure` quando
  `DEBUG=0` e `CSRF_TRUSTED_ORIGINS` vindo de `DJANGO_CSRF_TRUSTED_ORIGINS`.
- `.env.example`: as três variáveis de produção documentadas.
- `.gitignore`: `staticfiles/` (gerado pelo `collectstatic`).
- `docs-dev/a-codar/03-deploy-pythonanywhere.md` (novo): passo a passo completo, com banco A/B
  (G3), WSGI, estáticos, Force HTTPS, verificação, atualizações e backup.
- `docs-dev/guias/OPERACAO.md`: linha de produção na tabela "Subir", seção de produção e
  correção das menções ao Inter (agora Pluggy).
- `AGENTS.md`, `docs-dev/a-codar/01-plano-desenvolvimento.md` e `PENDENCIAS.md`: D6 revista,
  fase 8 decidida e itens novos (P2-17 a P2-19, P3-10 a P3-12).
- `docs-dev/painel.json`: fase de publicação em andamento e entrega de 2026-11-17.

**Arquivos:** `config/settings.py`, `.env.example`, `.gitignore`, `AGENTS.md`,
`docs-dev/a-codar/01-plano-desenvolvimento.md`, `docs-dev/a-codar/02-decisao-d6-onde-roda.md`,
`docs-dev/a-codar/03-deploy-pythonanywhere.md`, `docs-dev/guias/OPERACAO.md`, `PENDENCIAS.md`,
`docs-dev/painel.json`.

**Testes:** `.venv/bin/python manage.py test` → **213 testes, OK**. `collectstatic --noinput` →
131 arquivos. `check --deploy` com env de produção → só W004 (HSTS) e W008 (redirect), cobertos
pelo Force HTTPS do PythonAnywhere.

**Aberto:** executar o deploy na conta `viniciusapps` (P2-18), criar o banco novo pela opção A
(P2-19, G3), renovar o web app mensalmente (P3-10), backup semanal (P3-12) e a Pluggy no plano
grátis (P3-11). Nada publicado ainda: o deploy está em andamento.

## 2026-11-10 — Importação da Pluggy escrita e testada (P2-13)

**Pedido do dono (2026-11-10):** continuar o P2-13 com a doc da transação em mãos.

**O que mudou:**
- Doc oficial de `GET /v2/transactions` conferida: paginação por cursor (`next`),
  filtros `dateFrom`/`dateTo` (inclusivos, sobre a data da transação) e `amount` com
  sinal (saída negativa) acompanhando `type` (`DEBIT`/`CREDIT`).
- `financas/pluggy_api.py`: transações passam a usar `/v2/transactions` com cursor
  (`next`), no lugar do `/transactions` paginado por página (depreciado). Contas
  seguem no `/accounts?itemId`, por página.
- `financas/importacao_pluggy.py` (novo): mapeamento para `Movimento` — `id` vira
  `id_externo`; `date` vira `data`; `type` DEBIT/CREDIT vira despesa/receita;
  `abs(amount)` vira o valor; **só `POSTED` entra** (decisão do dono em 2026-11-10) e
  `PENDING` é pulado com motivo; descrição com `description` (reserva
  `descriptionRaw`); categoria `Não categorizado` do tipo; usuário técnico `Pluggy`;
  origem `pluggy`. O relatório conta as `category` da Pluggy para servir ao P2-15.
- `financas/management/commands/importar_pluggy.py` (novo): `--conta` (do app),
  `--pluggy-conta` (id; sem ele, usa a única conta `BANK` do item), `--desde`,
  `--ate`, `--dry-run`. Sai com erro quando alguma transação é recusada.
- `Movimento.Origem.PLUGGY` adicionado (`models.py` + migration `0006_origem_pluggy`).
  A migration **não foi aplicada** no banco real: o classificador de permissão exige
  um "pode" do dono nomeando a mudança no banco (P2-16).
- `.env.example`: `PLUGGY_ITEM_ID` documentado.
- Testes novos: `test_importacao_pluggy.py` (35) e `test_pluggy_api.py` ampliado; o
  comando é testado com o cliente trocado por dublê, sem rede.

**Arquivos:** `financas/models.py`, `financas/migrations/0006_origem_pluggy.py`,
`financas/pluggy_api.py`, `financas/importacao_pluggy.py`,
`financas/management/commands/importar_pluggy.py`, `financas/test_pluggy_api.py`,
`financas/test_importacao_pluggy.py`, `.env.example`, `PENDENCIAS.md`,
`docs-dev/painel.json`.

**Testes:** `.venv/bin/python manage.py test` → **213 testes, OK**.

**Aberto:** aplicar a migration 0006 (P2-16, do dono), credenciais e `itemId` da
Pluggy (P2-12, do dono), dry-run contra a conta real, mapeamento de categorias
(P2-15) e a conta "Inter" no app (P2-14). Nada commitado.

## 2026-11-09 — Cliente HTTP da Pluggy (P2-13, parte 1)

**Pedido do dono (2026-11-09):** continuar o P2-13 no que não depende de credencial.

**O que mudou:**
- `financas/pluggy_api.py` (novo): cliente da API com `POST /auth` (credenciais no corpo,
  chave no cabeçalho `X-API-KEY` e reaproveitada por 1h50), `GET /accounts?itemId=...` e
  `GET /transactions?accountId=...&from=...&to=...`, paginação por `page`/`pageSize`
  (500, o máximo que a API aceita) e `ErroPluggy` com status e mensagem da API. Caminhos e
  campos conferidos na documentação oficial em 2026-11-09: `/auth` → `apiKey`; contas com
  `id`, `type`, `balance`, `currencyCode`; transações com `id`, `description`, `amount`,
  `date`, `type` (DEBIT/CREDIT), `status` (PENDING/POSTED). O módulo não grava nada e não
  põe segredo em mensagem de erro (G13).
- `financas/test_pluggy_api.py` (novo, 15 testes): autenticação no corpo, `X-API-KEY` nas
  chamadas seguintes, cache e renovação da chave, paginação, filtros `from`/`to`, erro HTTP
  com status, erro de rede e segredo fora da mensagem. Nenhum teste chama a internet.

**Arquivos:** `financas/pluggy_api.py`, `financas/test_pluggy_api.py`, `PENDENCIAS.md`.

**Testes:** `.venv/bin/python manage.py test` → **178 testes, OK** (163 da base + 15 novos).

**Aberto:** a parte 2 do P2-13 (mapeamento para `Movimento` e comando `importar_pluggy`)
depende de: doc da transação (sinal do `amount` em conta bancária, semântica de
`from`/`to` e de `status`), decisão do dono sobre importar `PENDING` e a mudança de modelo
para `origem = pluggy` (G3). Nada commitado.

## 2026-11-09 — Inter descartado: a integração passa a ser Pluggy (Open Finance)

**Pedido do dono (2026-11-09):** importar saldo e extrato do banco para o app, sem exportar arquivo,
e limpar o que não serve.

**O que mudou:**
- Pesquisa dos bancos: BB, Itaú, Bradesco, Santander, Sicredi, Sicoob, C6, BTG e Cora exigem conta
  PJ/contrato/certificado; o C6 não libera API para conta MEI; Cora custa R$ 44,90/mês e BTG
  R$ 200/mês; Asaas e Efí são grátis, mas obrigam a mover a conta do MEI.
- **Decisão do dono:** a **Pluggy pelo Open Finance**, no modo pessoal gratuito (Meu Pluggy +
  conector 200). O dono conectou a conta **Itaú pelo CPF** e os dados apareceram — é o teste real
  do caminho gratuito. O Inter foi descartado: a API dele é exclusiva de PJ e não atende MEI
  (confirmado na ajuda oficial).
- Limpeza do Inter (aprovada pelo dono), 10 arquivos apagados: `financas/inter_api.py`,
  `financas/management/commands/conferir_saldo_inter.py`, `financas/test_api_inter.py` (esses três
  não estavam no git, sem volta), `financas/importacao_inter.py`, `financas/test_importacao.py`,
  `financas/management/commands/importar_inter.py`, `scripts/teste_inter.py`,
  `docs-dev/guias/INTER-PASSO-A-PASSO.md`, `docs-dev/a-codar/03-decisao-d4-escopo-inter.md` e
  `docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md` (recuperáveis pelo git).
- `AGENTS.md`: estado atual, regras 2 a 5 e as seções de integração/importação reescritas para a
  Pluggy. `.env.example`: seção `INTER_*` removida; placeholders comentados `PLUGGY_CLIENT_ID` e
  `PLUGGY_CLIENT_SECRET`.

**Arquivos:** os 10 apagados, `AGENTS.md`, `.env.example`, `PENDENCIAS.md`, `docs-dev/painel.json`,
`docs-dev/a-codar/briefing-descoberta.md`, `docs-dev/a-codar/01-plano-desenvolvimento.md`.
O `.env` real ainda tem as variáveis `INTER_*` (limpeza não executada, P4-7).

**Testes:** `.venv/bin/python manage.py test` → **163 testes, OK**. A suíte caiu de 230 porque saíram
os 67 testes do Inter (26 de `test_importacao` e 41 de `test_api_inter`); é a linha de base nova até
os testes da Pluggy entrarem.

**Aberto:** P2-12 (aplicação na Pluggy, do dono), P2-13 (mapeamento/importação), P2-14 (a conta
"Inter" no app, do dono), P4-7 (limpeza do `.env` e dos segredos do Inter). Nada foi commitado.

## 2026-11-09 — P2-3 fechado: diagnóstico do Inter com credencial e formato do token corrigido

**Pedido do dono (2026-11-09):** preencher as credenciais no `.env` e rodar o diagnóstico do sandbox.

**O que mudou:**
- O dono preencheu `INTER_CLIENT_ID` e `INTER_CLIENT_SECRET` no `.env`, direto do portal (36
  caracteres cada, formato UUID, sem espaço). Os valores nunca passaram por chat, documento ou log.
- O primeiro `scripts/teste_inter.py` falhou no token com HTTP 401 e a mensagem "no parameters or
  duplicate parameters or a missing required parameters". O formato foi testado: o sandbox **recusa
  as credenciais em cabeçalho** e **aceita no corpo do formulário** (`client_secret_post`); com as
  mesmas credenciais, query string e corpo deram 200. A credencial estava certa; o pedido é que
  estava no formato errado.
- `financas/inter_api.py` e `scripts/teste_inter.py`: `client_id` e `client_secret` movidos do
  cabeçalho para o corpo do `POST /oauth/v2/token`. O teste do token em `financas/test_api_inter.py`
  foi atualizado para travar o formato novo (e recusar credencial em cabeçalho).
- Diagnóstico com credencial: **TLS, token, saldo e extrato OK**. Simulação
  `importar_inter --api --dry-run --conta Inter`: **1.237 transações lidas, 1.237 seriam criadas,
  0 puladas, 0 erros**, nada gravado.
- Achados do sandbox: o **período é ignorado** (1.237 transações datadas de 2023 vieram para uma
  janela de um dia em 2026); `idTransacao` veio preenchido em todas; a estabilidade entre chamadas e
  o filtro `dataTransacao`/`dataInclusao` só se confirmam com dado real (P2-11).
- `PENDENCIAS.md`: P2-1, P2-2 e P2-3 fechados (saíram da lista); P2-11 atualizada.

**Arquivos:** `financas/inter_api.py`, `scripts/teste_inter.py`, `financas/test_api_inter.py`,
`AGENTS.md`, `PENDENCIAS.md`, `docs-dev/guias/INTER-PASSO-A-PASSO.md`, `docs-dev/painel.json`.
O `.env` mudou (fora do git).

**Testes:** `.venv/bin/python manage.py test` → **230 testes, OK** (linha de base: 230).

**Aberto:** P2-11 (ativação em produção, do dono). Nada foi commitado.

## 2026-11-09 — Importação direto da API do Inter (`--api`) e conferência de saldo

**Pedido do dono (2026-11-09):** continuar a integração com a API do Inter e fazer tudo o que não
depende dele. O que faltava era a camada entre o diagnóstico e o importador: o comando só sabia ler
um JSON salvo à mão.

**O que mudou:**
- `financas/inter_api.py` (novo): cliente da API com mTLS, token OAuth reaproveitado enquanto vale,
  `GET /banking/v2/saldo` e `GET /banking/v2/extrato/completo` com paginação tradicional
  (`pagina`/`tamanhoPagina`, 10.000 por página). Períodos maiores que 90 dias são fatidos em janelas
  contíguas; o header `x-conta-corrente` só vai quando `INTER_CONTA_CORRENTE` está preenchido.
  Erros viram `ErroInter` com status e `title`/`detail`; configuração ausente vira
  `ErroConfiguracaoInter`. O módulo não importa Django e não grava nada.
- Caminhos, parâmetros e envelope conferidos na **especificação OpenAPI oficial** em 2026-11-09 (até
  então só o host tinha sido conferido). O script `scripts/teste_inter.py` fica como está: ele é o
  diagnóstico do extrato simples; o importador usa o **extrato completo**, que é o que tem
  `idTransacao`.
- `importar_inter` ganhou `--api` (exclusivo com `--arquivo`), `--desde` e `--ate`. O período padrão
  é hoje nas duas pontas, que é a data de corte da primeira importação decidida no P2-8. `--desde` e
  `--ate` sem `--api` são recusados, para não serem ignorados em silêncio.
- `conferir_saldo_inter` (novo): compara `Conta.saldo` com o `disponivel` do `/saldo`, mostra a
  diferença e o `saldo_inicial` que faria os dois baterem. **Só leitura**: o ajuste continua sendo
  ação do dono (G3). Serve à conciliação da ativação (P2-8, item 5).
- `financas/test_api_inter.py` (novo, 41 testes): configuração, token (pedido, cache, renovação,
  recusa), saldo, extrato (parâmetros, paginação, janelas), erros e os dois comandos. Sessão falsa,
  sem rede, payload inventado.

**Arquivos:** `financas/inter_api.py` (novo), `financas/management/commands/importar_inter.py`,
`financas/management/commands/conferir_saldo_inter.py` (novo), `financas/test_api_inter.py` (novo),
`AGENTS.md`, `PENDENCIAS.md`, `docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md`,
`docs-dev/guias/INTER-PASSO-A-PASSO.md`, `docs-dev/painel.json`.

**Testes:** `.venv/bin/python manage.py test` → **230 testes, OK** (linha de base antes da mudança:
189, OK; 41 novos). `check` limpo; `makemigrations --check` sem drift.

**Fumaça (banco descartável de `/tmp`, dado inventado):** o modo `--arquivo` criou 2 movimentos e,
na segunda rodada, pulou os 2 como já importados. `--api` e `conferir_saldo_inter` sem `.env` param
com a lista das variáveis que faltam, antes de qualquer chamada. O `db.sqlite3` real não foi aberto.

**O que foi confirmado sem credencial:** em 2026-11-09, dentro da janela do sandbox, `GET` em
`/oauth/v2/token` respondeu 405 (é `POST`) e `/banking/v2/saldo`, `/banking/v2/extrato` e
`/banking/v2/extrato/completo` responderam 400 sem corpo — a rota existe; 404 significaria caminho
errado. Nenhum dado foi lido nem enviado.

**O que ainda não foi provado:** tudo o que depende de credencial: se o token sai, se o filtro
`dataInicio`/`dataFim` usa `dataTransacao` ou `dataInclusao` e se `idTransacao` vem sempre
preenchido (P2-3). Por isso a chamada real continua aberta.

**Aberto:** P2-1/P2-2 (integração e certificado, 👤), P2-3 (diagnóstico e `--dry-run` no sandbox),
P2-11 (ativação em produção, 👤). O padrão de período é hoje; se o dono quiser sobreposição de
alguns dias nas execuções seguintes, é uma linha no comando — decidir depois de saber qual data o
filtro usa (P2-3).

## 2026-11-08 — Bloco de gastos fixos recolhido atrás de um botão

**Pedido do dono (2026-11-08, testando o app):** a lista de gastos fixos empurrava "Abertos" para
baixo, e ele tinha que rolar muito para chegar ao "Paguei"/"Ignorar". Queria um botão que abrisse
só essa lista.

**O que mudou:**
- `templates/previstos.html`: a seção "Gastos fixos" (formulário de cadastro + lista) virou um
  `<details class="bloco-recolhivel">`, fechado por padrão. O `<summary>` é o botão: título à
  esquerda, total do mês à direita. Com isso o total da entrega anterior continua à vista sem
  abrir nada, e a linha `.total-mes` interna saiu (ficaria repetida).
- O bloco abre sozinho quando o formulário de cadastro volta com erro (`{% if form_fixo.errors %}
  open`); sem isso, o erro ficaria escondido atrás do botão.
- `app.css`: `.bloco-recolhivel` com o mesmo desenho de cartão neutro do resto da tela (borda,
  raio, sombra discreta), alvo de 44px, marcador nativo do `<details>` preservado (é a pista de
  que a linha abre). Sem peça visual nova em essência: é o cartão que já existe com cara de botão.
- `financas/test_gastos_fixos.py`: 2 testes novos (bloco fechado no GET; aberto quando o cadastro
  tem erro) e os 2 existentes ajustados para o total no `<summary>`.

**Arquivos:** `templates/previstos.html`, `financas/static/financas/app.css`,
`financas/test_gastos_fixos.py`.

**Testes:** `.venv/bin/python manage.py test` → **189 testes, OK** (linha de base antes da mudança:
187, OK). Sem migration.

**Verificação visual (banco descartável de `/tmp`, servidor em 8010, dado inventado):** a 500px o
resumo renderiza alinhado com os cartões da tela e o total cabe inteiro. O Edge headless do Windows
não aceita janela menor que 500px, então **375px/360px não foram renderizados**: por medida, o
conteúdo do resumo ocupa ~277px dos 335px disponíveis, com folga. Conferir no celular do dono.

**Sobre a ordenação de categorias da rodada anterior:** o pedido de ordem alfabética no seletor
**já estava atendido** pela outra sessão (`_opcoes_de_categoria` em `financas/forms.py`, entregue
23:13). Conferido no HTML servido: as opções saem Cartão, Mercado, Moradia, Saúde, Transporte.
Nada mudou aqui; se o dono ainda via a ordem antiga, era a página carregada antes da troca.

**Aberto:** nada desta entrega.

## 2026-11-08 — Total mensal dos gastos fixos na tela de previstos

**Pedido do dono (2026-11-08, testando o app):** ele quer saber quanto os gastos fixos somam por
mês. A primeira ideia era trocar o card "Previsto em aberto" da tela inicial por um "gasto previsto
x/y"; ao ver as opções, preferiu **manter o card como está** e ter o total na tela de gastos
previstos, "só para ter essa informação em algum lugar".

**O que mudou:**
- `financas/views.py` (view `previstos`): `total_fixos` soma `GastoFixo.valor` dos **ativos** — os
  que geram previsto. Inativo continua na lista como histórico do cadastro, mas não entra no total.
- `templates/previstos.html`: linha fechando a seção "Gastos fixos", com o mesmo `.total-mes` que
  Lançamentos e Relatório já usam (sem peça visual nova). Some quando não há gasto fixo cadastrado.
- Nada mudou na tela inicial: o card "Previsto em aberto" e a leitura `previsto_aberto` continuam.

**Arquivos:** `financas/views.py`, `templates/previstos.html`, `financas/test_gastos_fixos.py`
(3 testes novos: só ativos somam, sem fixo não aparece a linha, pagar o previsto não muda o total).

**Testes:** `.venv/bin/python manage.py test` → **187 testes, OK** (linha de base antes da mudança:
184, OK). Sem migration. Sem verificação visual nova: a linha reusa o `.total-mes` já conferido a
375/360/768/1280 e o rótulo ("Total dos fixos ativos") é mais curto que o de Lançamentos.

**Aberto:** nada desta entrega.

## 2026-11-08 — Categorias em ordem alfabética no seletor

**Pedido do dono (2026-11-08, testando o app):** com muitas categorias, achar a certa na lista do
lançamento ficou confuso; o palpite dele foi ordenar alfabeticamente.

**Causa:** a lista vinha na ordem do banco (`tipo`, `nome`): todas as despesas, depois todas as
receitas. E a comparação do SQLite é byte a byte, então `Água` e `Ótica` caíam **depois de `Z`** e
minúscula vinha depois de maiúscula. Não era ordem alfabética nem dentro de cada bloco.

**O que mudou:**
- `financas/forms.py`: os três seletores de categoria (lançamento novo e edição, gasto fixo e
  previsto avulso) passam por `_opcoes_de_categoria`, que ordena em Python por uma chave que
  **ignora acento e caixa** (`NFKD` + remoção dos diacríticos + `casefold`) e mantém
  "Escolha a categoria" no topo. O `queryset` filtrado continua o mesmo — a validação do POST segue
  recusando categoria inativa ou de tipo errado.
- A lista agora é uma só, A-Z, misturando despesa e receita; o rótulo de cada opção continua
  "Nome (despesa)" / "Nome (receita)", então o tipo não some. Lista curta, ordenar em Python não
  pesa.
- `financas/tests.py`: teste que fixa a ordem (`Água`, `alimentação`, `Aluguel`, …) e a opção vazia.

**Arquivos:** `financas/forms.py`, `financas/tests.py`.
**Testes:** `.venv/bin/python manage.py test` → **184 testes, OK** (linha de base antes da mudança:
183, OK). Sem migration. Sem verificação visual: é `<select>` nativo, mudou só a ordem das opções.
**Aberto:** nada desta entrega. Busca/filtro dentro do seletor não entrou (não foi pedido).

## 2026-11-08 — Descrição opcional no lançamento rápido

**Decisão do dono (2026-11-08, testando o app):** o lançamento tinha só categoria, então dois gastos
da mesma categoria ficavam indistinguíveis na lista. A descrição entra no formulário rápido como
**opcional** (quem lança rápido continua lançando em três campos) e com o rótulo **"Descrição"**,
igual a gastos fixos e previstos.

**O que mudou:**
- `MovimentoRapidoForm` passa a incluir `descricao` (o campo já existia no modelo, `blank=True`,
  `max_length=120`; é o mesmo preenchido pelo gasto fixo e pela importação do Inter). **Sem
  migration.**
- `templates/lancamentos.html` e `templates/editar_movimento.html`: campo depois da categoria, com
  a marca "(opcional)" no rótulo; a edição precisa exibir o campo, senão salvar apagaria a
  descrição existente.
- Mensagens de sucesso do lançar e do editar passam a nomear `descricao or categoria.nome`, o mesmo
  critério que a lista (`templates/lancamentos.html:44`) e o desfazer já usavam.
- `app.css`: regra neutra para `.campo-opcional` (texto de apoio, sem negrito).

**Arquivos:** `financas/forms.py`, `financas/views.py`, `financas/static/financas/app.css`,
`templates/lancamentos.html`, `templates/editar_movimento.html`,
`financas/test_uso_diario.py` (4 testes novos).

**Testes:** `.venv/bin/python manage.py test` → **183 testes, OK** (linha de base antes da mudança:
179, OK). Sem verificação visual nova: o campo reaproveita o `.campo` e o empilhamento já conferidos
a 375/360/768/1280 na revisão de UI do mesmo dia.

**Aberto:** nada desta entrega.

## 2026-11-08 — UI/UX revista: layout espaçado, navegação responsiva e leitura mais clara

**Decisão do dono (2026-11-08):** o sistema inteiro ganha uma revisão visual mantendo claro,
simples e neutro: mais respiro, hierarquia tipográfica, cartões com sombra discreta e uma navegação
que funciona no celular (barra inferior) e no desktop (topo). A regra de 2026-11-02 ("neutro claro,
cor só no número") continua valendo; a cor fica no dinheiro (verde/vermelho) e no ponto da marca.

**O que mudou:**
- `app.css` reescrito com tokens (`:root`) de cor, raio, sombra e espaçamento; tipografia com escala
  e rótulos em caixa alta pequena; listas em cartões com divisórias neutras.
- `base.html`: cabeçalho com marca (ponto + "Finanças") e Sair; no celular a navegação vira barra
  inferior fixa com o item ativo marcado por ponto; no desktop fica no topo, com fundo neutro no
  item ativo (sem filete colorido, G19).
- Tela inicial: saldo em destaque e gasto/previsto lado a lado no desktop; no celular, empilhados.
- Formulários: campos de 44px, botão de largura cheia no celular e largura natural no desktop;
  checkbox com o rótulo como alvo de 44px.
- Mensagens agora têm cor por tipo (`success`, `error`, `info`, `warning`) em vez de tudo verde.
- Estados vazios com contorno tracejado neutro; login centralizado; tema do PWA acompanha o fundo
  claro (`#f6f7f9` no meta e no manifesto).
- Anti-patterns conferidos (G19): sem faixa colorida em aresta, sem gradiente, sem chip de ícone,
  sem pílula grande, sombra discreta em lista.

**Arquivos:** `financas/static/financas/app.css` (reescrito), `templates/base.html`,
`templates/login.html`, `templates/previstos.html` (classe da nota do avulso),
`templates/editar_categoria.html` (classe do tipo), `financas/static/financas/manifest.webmanifest`.

**Testes:** `.venv/bin/python manage.py test` → **179 testes, OK** (sem teste novo; a revisão é
visual). `check` limpo; sem migration.

**Verificação visual (375, 360, 768 e 1280, banco descartável e login no servidor real):** sem
rolagem horizontal em nenhuma largura; navegação inferior no celular e topo no desktop; o alvo da
marca foi corrigido (estava com 26px; agora 44px); os únicos alvos medidos abaixo de 44px são os
checkboxes de 18-20px, cujo rótulo é o alvo real. O login foi conferido nas duas larguras. O
servidor real precisou ser reiniciado para largar o template antigo em cache; o dado não é afetado.

**Aberto:** nada desta entrega.

## 2026-11-08 — Tela de categorias: criar, editar e desativar sem admin

**Decisão do dono (2026-11-08):** a categoria é criada com nome, tipo, "entra no gasto do mês" e
ativa; na edição mudam nome, ativa e "entra no gasto"; o **tipo fica fixo** depois de criada, porque
mudar receita/despesa desalinharia os lançamentos antigos. Categoria não se apaga: desativa (sai dos
formulários, mantém o histórico).

**O que mudou:**
- Tela `/categorias/` com formulário de criação e listas separadas de despesas e receitas, mostrando
  "fora do gasto" e "inativa"; `/categorias/<pk>/editar/` edita nome, ativa e a flag.
- `CategoriaForm` e `CategoriaEdicaoForm`; a edição exclui o tipo e faz a checagem de nome duplicado
  no mesmo tipo (a restrição do banco continua como última defesa).
- Link "Categorias" na navegação; os avisos de "sem categoria" em Lançamentos e Previstos passam a
  apontar para a tela, não para o admin.
- Sem migration: o modelo `Categoria` já existia.

**Arquivos:** `financas/forms.py`, `financas/views.py`, `financas/urls.py`,
`templates/categorias.html` (novo), `templates/editar_categoria.html` (novo), `templates/base.html`,
`templates/lancamentos.html`, `templates/previstos.html`, `financas/test_categorias.py` (novo, 13
testes), `PENDENCIAS.md`, `docs-dev/painel.json`, `AGENTS.md`.

**Testes:** `.venv/bin/python manage.py test` → **179 testes, OK** (166 + 13 novos).

**Verificação visual (375px e 360px, banco descartável):** sem rolagem horizontal; navegação com o
link novo (a barra passa a ocupar duas linhas, com "Sair" na segunda, sem estouro); telas de
categorias e edição conferidas. Os únicos alvos medidos abaixo de 44px são os checkboxes de 20px,
cujo rótulo de 44px é o alvo real.

**Aberto:** nada desta entrega.

## 2026-11-08 — Gastos previstos viram gastos fixos mensais (cadastro + mês gerado)

**Decisões do dono (2026-11-08):** o previsto deixa de ser evento único. O gasto fixo é cadastrado
uma vez (descrição, valor, dia do vencimento, categoria) e cada mês gera o previsto daquele mês.
Editar o cadastro atualiza o previsto do mês corrente **se ele ainda estiver aberto**; mês pago ou
ignorado não muda; os próximos meses nascem com o valor novo. Desativar para de gerar os seguintes
(o mês corrente continua na lista até pagar ou ignorar). O previsto avulso continua como opção
secundária, porque evento único raro é lançado direto em Lançamentos.

**O que mudou:**
- `GastoFixo`: descrição, valor, dia do vencimento (1 a 31, com queda para o último dia do mês),
  categoria, conta, ativo e criado em. `PROTECT` em categoria/conta e no vínculo com o previsto;
  nada é apagado, desativa-se.
- `Previsto` ganhou `fixo` (nulo no avulso) e `competencia` (primeiro dia do mês gerado), com a
  restrição única `(fixo, competencia)`.
- `financas/gastos_fixos.py`: `garantir_previstos_do_mes()` (idempotente, cria o mês de referência
  para cada cadastro ativo) e `atualizar_previsto_do_mes()` (mês corrente aberto acompanha a
  edição). A home e a tela de previstos chamam a geração; a edição atualiza o mês aberto.
- Tela de previstos: seção "Gastos fixos" com formulário e lista (com Editar), "Abertos" com
  Paguei/Ignorar, "Ignorados" com Reabrir e o "Previsto avulso" dentro de um bloco recolhido.
- Admin: `GastoFixo` registrado; `Previsto` mostra o vínculo.

**Arquivos:** `financas/models.py`, `financas/gastos_fixos.py` (novo), `financas/forms.py`,
`financas/views.py`, `financas/urls.py`, `financas/admin.py`,
`financas/migrations/0005_previsto_competencia_gastofixo_previsto_fixo_and_more.py`,
`templates/previstos.html`, `templates/editar_gasto_fixo.html` (novo),
`financas/static/financas/app.css`, `financas/test_gastos_fixos.py` (novo, 16 testes),
`docs-dev/a-codar/01-plano-desenvolvimento.md`, `AGENTS.md`, `PENDENCIAS.md`,
`docs-dev/painel.json`.

**Testes:** `.venv/bin/python manage.py test` → **166 testes, OK** (150 + 16 novos). `check` limpo.

**Verificação visual (375px e 360px, banco descartável `/tmp/gestao-visual/db.sqlite3`):** sem
rolagem horizontal; foco visível; telas: previstos (formulário, lista fixa, abertos, ignorados e o
avulso recolhido) e edição do gasto fixo. A única medida abaixo de 44px é o próprio checkbox
(20×20), cujo alvo real é o rótulo de 44px que o envolve.

**Migration `0005` aplicada no banco real** (autorização do dono em 2026-11-08):
`.venv/bin/python manage.py migrate` → `financas.0005... OK`; `showmigrations` marca `[X] 0005`;
`financas_gastofixo` existe e `financas_previsto` tem `fixo_id` e `competencia`; `check` sem
problemas; nenhum dado apagado (a tabela de previstos estava vazia). O mês é gerado quando o app é
aberto; se um mês passar sem abrir, ele não é recriado para trás (um lançamento manual cobre o
caso). A geração é do mês corrente, não preenche meses futuros.

## 2026-11-08 — Uso diário: editar e desfazer lançamento, ignorar/reabrir previsto e navegar meses

**Decisões do dono (2026-11-08):** o desfazer de lançamento é **cancelar e relançar** e também
**editar direto** (data, valor e categoria); previsto ignorado **volta** para aberto pelo botão
`Reabrir`. A máquina de estados ficou: `Movimento` ativo → cancelado (com quem/quando; o desfazer
não se desfaz; corrigir é desfazer e lançar de novo); `Previsto` aberto → pago (um movimento;
desfazer o movimento reabre) ou aberto → ignorado (sem movimento; reabrir volta). Lançamento
importado do Inter não se edita nem se desfaz: o banco é a fonte. Lançamento vindo de previsto pago
não se edita, para não desalinhar `Previsto.valor` do `Movimento.valor`; o caminho é desfazer o
pagamento e lançar de novo.

**O que mudou:**
- `Movimento` ganhou `cancelado`, `cancelado_em` e `cancelado_por`, com a restrição
  `movimento_cancelado_tem_quem_e_quando`; `Conta.saldo` e todos os totais (tela inicial, gasto do
  mês, listas e relatório) ignoram movimento cancelado. O admin mostra o estado e não edita os
  campos de cancelamento.
- Lançamento rápido ganhou **Data** (nasce hoje, editável); o form aceita data vazia e a view
  completa com hoje, preservando a suíte antiga.
- **Editar** lançamento manual em tela própria (`/lancamentos/<pk>/editar/`), com data, valor e
  categoria; o tipo acompanha a categoria. **Desfazer** (`POST /lancamentos/<pk>/desfazer/`) é
  lógico e idempotente; se o lançamento veio de "Paguei", o previsto volta para aberto.
- **Ignorar** (`POST /previstos/<pk>/ignorar/`) tira o previsto do total em aberto sem criar
  movimento; **Reabrir** (`POST .../reabrir/`) devolve, com lista de ignorados na tela.
- Lançamentos e relatório aceitam `?mes=AAAA-MM` com navegação ‹ › e mês por extenso; mês inválido
  cai no corrente. Movimento desfeito não aparece na lista.
- Ações na tela seguem o alvo de toque de 44px; o CSS usa o mesmo vocabulário neutro da fase 2.
- `ValorBrasileiroField.prepare_value` exibe Decimal com vírgula no formulário de edição.
- A auto-revisão pegou um caso de borda: limpar a data na edição zerava o campo no ModelForm; a
  data original passou a ser guardada antes da validação, com teste próprio.

**Arquivos:** `financas/models.py`, `financas/forms.py`, `financas/views.py`, `financas/urls.py`,
`financas/admin.py`,
`financas/migrations/0004_movimento_cancelado_movimento_cancelado_em_and_more.py`,
`templates/lancamentos.html`, `templates/previstos.html`, `templates/relatorio.html`,
`templates/editar_movimento.html` (novo), `financas/static/financas/app.css`,
`financas/test_uso_diario.py` (novo, 25 testes), `PENDENCIAS.md`, `docs-dev/painel.json`.

**Testes:** `.venv/bin/python manage.py test` → **150 testes, OK** (125 da linha de base pós-rodada
+ 25 novos). `manage.py check` sem problemas.

**Verificação visual (375px e 360px, banco descartável `/tmp/gestao-visual/db.sqlite3`):** sem
rolagem horizontal (`scrollWidth = clientWidth`), nenhum alvo pequeno nas telas conferidas, foco
visível em todos os controles; telas: início, lançamentos, previstos (com ignorados), relatório
(com navegação), lançamentos de outro mês e edição. Dois defeitos achados e corrigidos: "Editar"
com 38,3px de largura e "Voltar para lançamentos" com 19px de altura.

**Migration `0004` aplicada no banco real** (autorização do dono em 2026-11-08):
`.venv/bin/python manage.py migrate` → `financas.0004... OK`; `showmigrations` marca `[X] 0004`;
as colunas `cancelado`, `cancelado_em` e `cancelado_por_id` existem em `financas_movimento`;
`manage.py check` sem problemas. Nenhum dado foi apagado; os movimentos existentes continuam
ativos (`cancelado=False`).

**Aberto:** nada desta entrega. A rodada paralela 2026-11-05-b estava em voo e foi encerrada antes
desta entrega; os arquivos da matriz dela não foram tocados, e a consolidação da rodada nos três
arquivos de rastro ainda não tinha sido feita quando escrevi esta entrada — quem consolidar depois
encaixa em cima (G21), sem reverter.

## 2026-11-05 — P2-10 fechado: migration 0003 aplicada e categorias padrão criadas

**O que mudou:** o dono autorizou a aplicação da migration `0003` no banco real. Ela adicionou
`Categoria.entra_no_gasto` e `Movimento.id_externo`, mais a restrição única
`(conta, id_externo)`. Depois, foram criadas as categorias padrão da importação: "Não
categorizado" (despesa), "Não categorizado" (receita) e "Investimento" (despesa, com
`entra_no_gasto=False`). Nenhum dado existente foi alterado: os movimentos antigos ficaram com
`id_externo` vazio e as categorias antigas com `entra_no_gasto=True`.
**Comando:** `.venv/bin/python manage.py migrate` → `financas.0003... OK`. As categorias foram
criadas por ORM (`get_or_create`), com o resultado `criada=True` nas três.
**Verificação:** `showmigrations` mostra `0003` como aplicada; `manage.py check` sem problemas;
`.venv/bin/python manage.py test` → **68 testes, OK**. O app no banco real voltou a responder com
o código novo.
**Arquivos:** nenhum de código nesta entrada; `PENDENCIAS.md` (P2-10 fechado) e
`docs-dev/rodada-2026-11-05-b/00-briefing.md` (T0 marcado como concluído).
**Aberto:** P2-1/P2-2 (integração e certificado), P2-3 (diagnóstico no sandbox). A rodada
paralela de 5 sessões parte de 68 testes verdes.

## 2026-11-05 — D4 e P2-8 fechados; modelo pronto para a importação do Inter

**Decisões do dono:** **D4** — a v1 lê só a conta **PJ (MEI)**: saldo e extrato. PF, cartão,
boleto de terceiro, posição de investimentos, pagamentos/Pix e Open Finance ficam fora, porque a
API direta não alcança. **P2-8** — importação na conta existente `69 450 604 Vinicius Di Franca
Alarc`; data `dataTransacao` (reserva `dataInclusao`); categoria "Não categorizado" e classificação
manual depois; `idTransacao` em `Movimento.id_externo` como chave antiduplicidade; autoria do
usuário técnico `Inter`; investimento, estorno e cashback importados com categoria própria, e
"Investimento" fora do gasto; a primeira importação começa na data da execução, para não duplicar
os Pix manuais que já estão na conta. Documento completo em
`docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md`.
**O que mudou no código:** `Movimento` ganhou `id_externo` (nulo no lançamento manual) com
restrição única `(conta, id_externo)`; `Categoria` ganhou `entra_no_gasto` (padrão `True`). A tela
inicial e o relatório passaram a filtrar `categoria__entra_no_gasto=True`; o rodapé do relatório
virou "Total de gastos do mês", porque "despesas" ficaria impreciso com investimento fora. O admin
expõe a flag e esconde o id externo do formulário.
**Arquivos:** `financas/models.py`, `financas/views.py`, `financas/admin.py`,
`templates/relatorio.html`, `financas/tests.py` (+6 testes),
`financas/migrations/0003_categoria_entra_no_gasto_movimento_id_externo_and_more.py`,
`PENDENCIAS.md`, `docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md`.
**Testes:** `.venv/bin/python manage.py test` → **68 testes, OK** (62 + 6). `manage.py check` sem
problemas; `makemigrations --check` sem drift.
**Não aplicado:** a migration `0003` está escrita e testada no banco de teste, mas não roda no
banco real sem o "pode" do dono (G3) — item P2-10. As categorias padrão também dependem disso.
**Aberto:** P2-1/P2-2 (criar integração e certificado), P2-3 (diagnóstico no sandbox), P2-10
(aplicar migration e criar categorias). O importador só começa depois desses.

## 2026-11-05 — P4-5 fechado: alvos de toque de 44px

**O que mudou:** os controles que a conferência visual a 375px (s2 do P4-4) apontou como pequenos
passaram ao alvo de 44×44: `.botao-primario` ganhou `min-height` (o "Paguei" compacto ia a 36px de
altura); os links da navegação e o "Sair" viraram `inline-flex` com `min-width`/`min-height` de
44px. O espaçamento entre os links da navegação caiu de 1rem para 0.5rem para os cinco alvos
continuarem numa linha só a 375px e a 360px. Nenhum template mudou; a aparência do texto é a mesma,
só a área clicável cresceu.
**Arquivos:** `financas/static/financas/app.css`.
**Testes:** `.venv/bin/python manage.py test` → 62 testes, **OK** antes e depois. `manage.py check`
sem problemas.
**Verificação:** medição por CDP com viewport real de 375px e cache do navegador desabilitado, nas
quatro telas autenticadas (`/`, `/lancamentos/`, `/previstos/`, `/relatorio/`). Antes, `/previstos/`
tinha 12 alvos pequenos: "Início" 35×28, "Lançamentos" 84×28, "Previstos" 57×30, "Relatório" 57×28,
"Sair" 24×20 e seis "Paguei" 67×36. Depois: **zero** alvos abaixo de 44×44 nas quatro telas, sem
rolagem horizontal (`scrollWidth = 375`) e sem elemento passando da borda. A 360px, também zero.
Evidência em `/tmp/gestao-visual/depois-{inicio,lancamentos,previstos,relatorio}.png` (fora do git).
**Fechado:** P4-5. A remoção do descartável da conferência continua em P4-6, aguardando autorização.

## 2026-11-05 — Rodada paralela (5 sessões)

Cinco itens do `PENDENCIAS.md` trabalhados em sessões paralelas no mesmo repositório, sem commit.
Cada sessão deixou o rastro em `docs-dev/rodada-2026-11-05/`; esta entrada consolida.

**s1 · P4-2 (auditor de referências).** `scripts/auditar-referencias.py` passou a auditar este
repositório: `RAIZES` com os 12 diretórios reais, `docs-dev/guias/*.md` acrescentado ao `ALVOS_DOC`
e correção do falso positivo em que um caminho relativo está ancorado numa base `~/...` citada na
mesma frase (os 3 caminhos do `AGENTS.md` e 3 do briefing). Modo padrão: exit 0, limpo. `--tudo`:
1 achado informativo (`regras/templates/` no briefing, linha 70), menção histórica que a regex não
pega — reportado, não corrigido. `indice_simbolos()` segue vazio (só indexa Java/TS; indexar Python
de `financas/` é melhoria futura). **Arquivos:** `scripts/auditar-referencias.py`. **Testes:** 62 → 62, OK.

**s2 · P4-4 (conferência visual a 375px).** `/previstos/` e `/relatorio/` conferidas a 375px com
SQLite descartável em `/tmp` e dado inventado (o `db.sqlite3` real não foi aberto): `scrollWidth =
375` nas duas, nenhum elemento passando da borda, contraste do valor de despesa 6,5:1 — **ok**, sem
defeito. Nenhum template/CSS alterado. **Arquivos:** `config/settings_visual.py` (novo, descartável,
pode ser removido), screenshots em `/tmp/gestao-visual/`. **Testes:** 62 → 62, OK. **Achado:** alvos
de toque abaixo de 44px ("Paguei" 67×36, nav 28–30px, "Sair" 24×20) — virou P4-5.

**s3 · P3-9 (segundo usuário e PWA, parte técnica).** Entrega HTTP do PWA conferida com o cliente de
teste: `/login/` 200, `/` anônimo 302, manifest 200 `application/manifest+json` com `display:
standalone`, `start_url` e `scope` `/`, ícones 200 medidos em 192×192 e 512×512. Segunda conta criada
com autorização do dono na sessão: usuário `Kethlen` (id 2, ativo, sem admin), **senha ainda não
definida** — ninguém entra até o dono definir. `OPERACAO.md` ganhou o que faltava para o celular
alcançar: IP em vez de localhost, `DJANGO_ALLOWED_HOSTS` no `.env` (hoje não existe `.env`, então o
celular leva `DisallowedHost`) e o firewall do Windows. Checklist de uma semana pronto. **Arquivos:**
`docs-dev/guias/OPERACAO.md`. **Testes:** 62 → 62, OK.

**s4 · P3-3 (dossiê da decisão D6).** Dossiê com 5 opções de exposição (rede de casa, Tailscale,
Cloudflare Tunnel, ngrok, VPS), com os três números do G20 e links datados; recomendação: rede de
casa na v1, Tailscale se quiser sair de casa agora, Cloudflare como plano B, VPS só se o PC não
puder ficar ligado. Nada criado. **Arquivo:** `docs-dev/a-codar/02-decisao-d6-onde-roda.md`.

**s5 · P2-6 (dossiê da decisão D4).** Delimitação com 17 fontes oficiais datadas: a API Banking é
exclusiva de PJ; cobre saldo, extrato (90 dias por consulta), extrato enriquecido, PDF e pagamentos;
ficam de fora conta PF, cartão de crédito, boleto de outra titularidade, investimentos e contas a
pagar; Open Finance não é caminho para app pessoal. A importação preenche `data`, `valor`, `tipo`,
`descricao` e `origem=inter`, mas não `categoria` (obrigatória), `criado_por` nem chave
antiduplicidade; o modelo não tem campo para id externo (próxima rodada). 10 perguntas do dono e 6
pontos só confirmáveis no sandbox. **Arquivo:** `docs-dev/a-codar/03-decisao-d4-escopo-inter.md`.

**Ficou aberto:** P4-4 aguarda o "conferi" do dono; P3-9 aguarda senha da `Kethlen`, `.env` com
`DJANGO_ALLOWED_HOSTS` (P2-9), instalação no celular e uma semana de uso; P3-3 e P2-6 aguardam
decisão do dono com os dossiês na mesa; novos itens P4-5 (alvos de toque) e P4-6 (remover o
descartável). Nada foi commitado.

## 2026-11-03 — Fase 7 iniciada: host do sandbox corrigido

**O que mudou:** `scripts/teste_inter.py` passou a usar o host oficial do sandbox,
`https://cdpj-sandbox.partners.uatinter.co`, conferido no portal do desenvolvedor do Inter.
O `.env.example` agora mostra exemplos de caminho absoluto do WSL para certificado e chave.
**Arquivos:** `scripts/teste_inter.py` (host e comentários), `.env.example`.
**Testes:** o script compila; os hosts de sandbox e produção respondem TLS (GET no token dá 405,
como esperado sem credencial). O script roda e para pedindo as variáveis do `.env`, que não existe.
**Aberto:** criar/preencher `.env` e certificado (P2-1/P2-2), confirmar se a conta é PJ e o
mapeamento da importação (P2-6/P2-8), rodar o diagnóstico (P2-3) e só depois desenhar a importação.

## 2026-11-03 — Fase 6 implementada: segundo login, logout e PWA

**Decisão do dono:** o app é do casal, com uma conta conjunta. As duas contas de login veem todos
os dados; o lançamento registra quem lançou em `criado_por`.
**O que mudou:** logout na navegação (POST), PWA com `manifest.webmanifest`, ícones 192 e 512,
`display: standalone`, `theme-color` e metatags de iOS. Nenhuma mudança de modelo: `criado_por` já
era gravado no lançamento rápido e no pagamento de previsto.
**Arquivos:** `financas/urls.py` (rota `logout`), `templates/base.html` (manifest, metatags,
logout), `financas/static/financas/manifest.webmanifest` (novo), `financas/static/financas/icone-192.png`
e `icone-512.png` (novos), `financas/static/financas/app.css`, `financas/tests.py` (+7 testes).
**Testes:** `.venv/bin/python manage.py test` → 62 testes, **OK**; `manage.py check` sem problemas;
`makemigrations --check` sem mudanças.
**Validação:** testes cobrem logout, autoria do lançamento e do pagamento, as duas contas vendo os
mesmos dados, manifesto com campos/ícones e as metatags no HTML. Smoke test confirmou manifesto e
ícones servidos com o tipo correto.
**Aberto:** P3-9, a verificação de uso real (criar o segundo usuário, instalar o PWA no celular e
usar uma semana). Service worker/offline não entrou: o plano pedia manifest, ícone e `display`.
Em Rede local por HTTP, a instalação pode depender do navegador; HTTPS é assunto da fase 8.

## 2026-11-03 — Fase 5 implementada e validada: relatório por categoria

**O que mudou:** tela nova `/relatorio/` e item "Relatório" na navegação. O relatório mostra as
despesas do mês corrente agrupadas por categoria, com total, percentual sobre o total de despesas
e ordem decrescente. O rodapé repete o total de despesas do mês. Receitas e meses anteriores ficam
fora. Ficou de fora, por não estar no plano: seletor de outro mês.
**Arquivos:** `financas/views.py` (view `relatorio`), `financas/urls.py`, `templates/relatorio.html`
(novo), `templates/base.html` (nav), `financas/templatetags/financas_extra.py` (filtro
`porcentagem`), `financas/static/financas/app.css`, `financas/tests.py` (+6 testes).
**Testes:** `.venv/bin/python manage.py test` → 55 testes, **OK**; `manage.py check` sem problemas;
`makemigrations --check` sem mudanças.
**Validação:** a soma dos totais por categoria é comparada com o total de despesas do mês em teste,
e o relatório exclui receitas e despesas de outro mês. Percentuais são calculados sobre o total de
despesas; com arredondamento de uma casa, a soma dos percentuais pode não fechar 100,0% em casos de
terços, mas a soma dos valores fecha exatamente.
**Aberto:** fase 6 (segundo login e PWA). Conferência visual de `/previstos/` e `/relatorio/` a
375px fica em P4-4, sem bloquear a fase.

## 2026-11-03 — Fase 4 implementada e validada: gastos previstos

**O que mudou:** tela nova `/previstos/` e item "Previstos" na navegação. O formulário cria um
gasto previsto com descrição, vencimento, valor e categoria de despesa; a conta é a padrão e o
tipo é sempre despesa. A lista mostra os previstos abertos por vencimento, cada um com o botão
"Paguei". Ao pagar, o sistema cria exatamente um movimento com a data real de hoje, na conta do
próprio previsto, e marca o previsto como pago. Não há desfazer na v1 (decisão do dono).
**Arquivos:** `financas/forms.py` (`PrevistoForm`), `financas/views.py` (`previstos` e
`pagar_previsto`), `financas/urls.py`, `templates/previstos.html` (novo), `templates/base.html`
(nav), `financas/static/financas/app.css`, `financas/tests.py` (+16 testes), `docs-dev/painel.json`,
`RETRABALHO.md` (novo).
**Testes:** `.venv/bin/python manage.py test` → 49 testes, **OK**; `manage.py check` sem problemas.
**Validação:** os dois critérios do plano são cobertos por teste: previsto pago sai do total em
aberto e entra no gasto do mês; previsto futuro aberto não entra no gasto do mês corrente.
**Correção na revisão:** o "Paguei" não deve depender da conta padrão atual. A primeira versão
filtrava o previsto pela conta padrão, então mudar a conta padrão deixava previstos antigos com
o botão da lista retornando 404. Agora o pagamento usa a conta do próprio previsto e funciona
mesmo sem conta padrão marcada.
**Aberto:** fase 5 (relatório por categoria). A conferência visual da tela nova a 375px fica como
P4-4, sem bloquear a fase.

## 2026-11-03 — Fase 3 implementada: lançamento rápido e lista do mês

**O que mudou:** tela nova `/lancamentos/` com formulário de valor + categoria e lista do mês
corrente agrupada por dia, mais navegação entre Início e Lançamentos. Decisões do dia: conta
padrão nova em `Conta` (só uma pode ser padrão) e total exibido = despesas do mês. O tipo do
movimento vem da categoria escolhida; o valor aceita vírgula ("30,50") e ponto ("30.50").
**Arquivos:** `financas/models.py` (campo `padrao` + constraint), `financas/migrations/0002_...`,
`financas/forms.py` (novo), `financas/views.py` (view `lancamentos`), `financas/urls.py`,
`templates/base.html` (navegação e mensagens), `templates/lancamentos.html` (novo),
`financas/static/financas/app.css`, `financas/admin.py`, `financas/tests.py` (+14 testes).
**Testes:** `.venv/bin/python manage.py test` → 33 testes, **OK**. `manage.py check` sem problemas.
Migração `financas.0002` aplicada no banco local com o "pode" do dono em 2026-11-03, dentro de
transação, sem erro.
**Verificação (P3-8):** em 2026-11-03 o dono marcou a conta padrão no admin e lançou 5 gastos reais
do dia pela tela nova, sem admin; a lista agrupada por dia e o total de despesas bateram. Fase 3
fechada. **Aberto:** fase 4 (gastos previstos com o botão "paguei").

## 2026-11-03 — Fase 2 verificada visualmente e fechada (P3-4 e P3-6)

**O que mudou:** o dono criou o superusuário (P3-4) e fez a conferência visual da tela inicial a
375px de largura, com dados de exemplo lançados pelo admin (P3-6). Os três números bateram com o
esperado: saldo, gasto do mês e previsto em aberto. A fase 2 fecha sem mudança de código.
**Arquivos:** `PENDENCIAS.md` (P3-4 e P3-6 removidos; estado da suíte corrigido para 19 testes),
`docs-dev/painel.json` (fase "Tela inicial" → feito), `AGENTS.md` (estado atual e linha de base).
**Testes:** `.venv/bin/python manage.py test` → 19 testes, **OK**; `manage.py check` sem problemas;
nenhuma migration pendente (rodados na revisão de hoje, antes da conferência visual).
**Aberto:** fase 3 (lançamento rápido). Decisões de conta padrão e local do formulário ainda em aberto.

## 2026-11-02 — Banco local do WSL criado (P3-5 fechado)

**O que mudou:** com o "pode" do dono (G3), o `migrate` criou o `db.sqlite3` local e aplicou
as 18 migrations (17 do Django + `financas.0001_initial`), incluindo as 4 tabelas do app.
Descoberto no caminho: o binário `sqlite3` não existe no WSL, então `manage.py dbshell` falha;
o app não é afetado (o Django usa o driver Python embutido) e nada foi instalado.
**Arquivos:** `PENDENCIAS.md` (P3-5 removido, P3-6 atualizado),
`docs-dev/guias/OPERACAO.md` (nota sobre o `dbshell`; comando "ver o que está rodando"
ainda era o do Windows, `findstr` → `ss`).
**Testes:** não se aplica, só ação de banco autorizada.

## 2026-11-02 — Tela inicial (fase 2 do plano) com os três números

**O que mudou:** a raiz do site virou a tela inicial, protegida por login: saldo, gasto do mês
e previsto em aberto, mobile-first. Leituras fechadas nesta sessão (registradas para a fase 4
não chutar): saldo = saldos iniciais + receitas − despesas de **todas as contas** (regra do
plano); gasto do mês = despesas do mês corrente; previsto em aberto = **só despesas** abertas
(decisão do dono). Estilo com cor só no número (saldo verde quando positivo, vermelho quando
negativo; gasto em vermelho; previsto em cinza), decidido com o dono — o projeto não tem doc
de design (G19). Login usa o `LoginView` do Django com rótulos e erro em pt-BR fixos no
template, porque o WSL não tem o locale pt_BR instalado. Os nomes de URL ganharam namespace
`financas:` (settings atualizado). Ficou de fora o logout: não está na spec da fase e volta
na fase 6.
**Arquivos:** `financas/views.py` (view `inicio`), `financas/urls.py` (novo), `config/urls.py`
(include do app), `templates/base.html`, `templates/inicio.html`, `templates/login.html`,
`financas/static/financas/app.css`, `financas/templatetags/financas_extra.py` (filtro
`dinheiro`), `financas/tests.py` (+11 testes), `PENDENCIAS.md` (P3-6),
`docs-dev/painel.json` (fase em andamento).
**Testes:** `.venv/bin/python manage.py test` → 19 testes, **OK** (8 da linha de base + 11 novos).
**Aberto:** verificação visual da fase (P3-6), que depende do banco local (P3-5) e do
superusuário (P3-4).

## 2026-11-01 — Projeto passa a rodar só no WSL, pelo Dev Valley com o DeepSeek

**O que mudou:** o dono decidiu trazer o projeto para o WSL e codar pelo Dev Valley, com o DeepSeek
(perfil pessoal do Claude Code, para não usar a licença do trabalho). Revoga a decisão "Zed no Windows"
(entrada abaixo). Clonado em `~/Documents/Projetos-pessoais/gestao-financeira`; `.venv` de Linux criado
sem pip (o WSL não tem `python3-venv`; dependência entra com `pip3 --python .venv/bin/python`). Novo
`CLAUDE.md` que importa o `AGENTS.md`; auditor de referências instalado (`scripts/auditar-referencias.py`,
`.claude/auditoria-regras.txt`). Regra 2 ganhou: o assistente lê e escreve código, nunca dado real
(`db.sqlite3`, extrato, `.env`).
**Arquivos:** `AGENTS.md` (ambiente, comandos, regras 2 e 5, fonte das regras), `CLAUDE.md` (novo),
`docs-dev/guias/OPERACAO.md` (WSL e `.venv/bin/python`), `PENDENCIAS.md` (comando do P3-4),
`financas/tests.py` e `scripts/teste_inter.py` (comando no comentário).
**Testes:** `.venv/bin/python manage.py test` → 8 testes, **OK** (no WSL).
**Aberto:** o banco local do WSL não existe ainda (`migrate` espera o dono, G3); ajustar `ALVOS`/`RAIZES`
do auditor e rodá-lo.

## 2026-11-01 — Modelo de dado e linha de base de testes

**O que mudou:** D2, D3 e D5 fechadas como propostas no plano, e o modelo da fase 1 escrito e aplicado.
Conta com `saldo` calculado por soma de movimentos, `Categoria` única por nome e tipo, `Movimento` com
valor positivo e sinal no `tipo`, e `Previsto` com a regra de que "pago" exige movimento. A suíte saiu
do zero para 8 testes.
**Arquivos:** `financas/models.py` (4 modelos), `financas/admin.py` (admin como tela provisória, com
`criado_por` vindo da sessão), `financas/migrations/0001_initial.py`, `financas/tests.py` (8 testes),
`PENDENCIAS.md` (D2, D3 e D5 fechadas; P3-4 aberto para o superusuário), `AGENTS.md` (estado e regra
de testes).
**Testes:** `.venv/Scripts/python manage.py test` → 8 testes, **OK**. `manage.py check` sem problemas.
`migrate` aplicou `financas.0001_initial` e as 4 tabelas existem no banco.
**Aberto:** criar o superusuário (P3-4) e a tela inicial (fase 2).

## 2026-11-01 — Esqueleto do Django rodando

**O que mudou:** D1 fechado em Django. Projeto `config` e app `financas` criados na raiz, SQLite com
as migrations do Django aplicadas, admin disponível. O modelo de dado segue vazio de propósito: ele
depende de D2, D3 e D5. Também entrou o `docs-dev/guias/OPERACAO.md` (G14), que passou a fazer sentido
porque agora existe servidor para subir.
**Arquivos:** `manage.py`, `config/settings.py` (segredo lido do `.env` ou de `.django-secret`, nunca
do código; `pt-br`, `America/Sao_Paulo`, login obrigatório), `config/urls.py`, `financas/`,
`requirements.txt` (`django~=5.2`, instalado 5.2.18), `.gitignore` (`.django-secret`),
`docs-dev/guias/OPERACAO.md`, `AGENTS.md` (stack e como rodar), `PENDENCIAS.md` (P2-4 fechado,
estado do sistema atualizado).
**Testes:** `manage.py check` sem nenhum problema; `manage.py migrate` aplicou 17 migrations do
Django. Não existe suíte própria ainda, e nenhum teste foi escrito nesta entrega.
**Aberto:** modelo de dado (D2, D3, D5), segundo login (D5) e a primeira tela.

## 2026-11-01 — Plano de desenvolvimento da v1

**O que mudou:** o projeto deixou de ter só uma fase de integração e passou a ter um plano de produto.
A decisão importante é de ordem: **o Inter saiu do caminho crítico**. O app nasce com lançamento
manual e a integração entra como fase 7, alimentando dados, não bloqueando o resto.
**Arquivos:** `docs-dev/a-codar/01-plano-desenvolvimento.md` (novo, 8 fases com verificação por fase,
modelo de dado proposto e as 4 decisões da fase 0), `docs-dev/painel.json` (plano novo), `PENDENCIAS.md`
(D1 e D2 com recomendação; itens do Inter marcados como pausados até a fase 7).
**Testes:** não se aplica, só documentação.
**Aberto:** as decisões da fase 0 (D1, D2, D3, D5), que travam o modelo de dados.

## 2026-11-01 — Investigação do portal Sandbox e do host da API

**O que mudou:** descoberto por que o `/sandbox` não abre e um problema maior, que travaria o teste de
qualquer jeito. Registrar não é corrigir: o script segue intocado, porque o host novo não foi conferido
na doc oficial (G1).
**Achados:** (1) o Sandbox só está disponível das 8h às 20h, de segunda a sexta, e exige login da
**Comunidade Inter**, não do Internet Banking PJ; (2) `cdpj-sandbox.partners.bancointer.com.br`, que o
script usa, **não resolve em DNS**; `cdpj-sandbox.partners.uatinter.co` resolve.
**Arquivos:** `PENDENCIAS.md` (P2-1 reescrito, P2-7 criado). Nenhum código alterado.
**Testes:** `nslookup`/`Resolve-DnsName` nos dois hosts do sandbox e no de produção; leitura das páginas
oficiais `/sandbox`, `/docs/sandbox/sobre-este-portal` e `/docs/sandbox/como-testar-aplicacao`.
**Aberto:** P2-7, confirmar o host na página Referências e só então corrigir `BASE_URLS`.

## 2026-11-01 — Decisão: Zed no Windows para projetos pessoais

**O que mudou:** fechada a dúvida de ambiente, e ela não é divergência. O WSL2 (Ubuntu 24.04)
existe para os projetos da CNR e para o Claude Code; os projetos pessoais, incluindo este, rodam
no Windows pelo Zed, com `.venv` local. O item P3-4 saiu do `PENDENCIAS.md`.
**Arquivos:** `AGENTS.md` (seção de ambiente reescrita como decisão), `PENDENCIAS.md` (P3-4 fechado).
**Testes:** não se aplica, mudança de documentação.
**Aberto:** nada novo.

## 2026-11-01 — Controle de contexto no padrão da casa

**O que mudou:** o projeto passou a ter rastro, não só um briefing: instruções do repositório,
memória, rastreador único de pendências e o painel de fases. O `BRIEFING.md` deixou a raiz e virou
`docs-dev/a-codar/briefing-descoberta.md`, que é o lugar de decisão fechada e ainda não codada (G7).
**Arquivos:** `AGENTS.md` (novo, instruções do projeto e resumo dos guardrails que incidem aqui),
`PROGRESS.md` (novo), `PENDENCIAS.md` (novo, D1–D6 e os bloqueios da fase 1), `docs-dev/painel.json`
(novo, fase 1 sem nenhuma etapa concluída), `docs-dev/a-codar/briefing-descoberta.md` (movido de
`BRIEFING.md` com `git mv`, sem perda de conteúdo além do cabeçalho, que aponta para os novos donos
do estado).
**Testes:** nenhum código executado; mudança só de documentação.
**Aberto:** `docs-dev/guias/OPERACAO.md` espera existir back ou front para subir (P4-1);
auditor de referências G12/G16 ainda não instalado (P4-2).

## 2026-11-01 — Sessão anterior: repositório, ambiente e teste de conexão

**O que mudou:** repositório privado criado e publicado; ambiente Python montado no projeto; script
de diagnóstico da API do Inter escrito. Nenhum código de aplicação ainda, e o script **nunca rodou**.
**Arquivos:** `.gitignore` (bloqueia `.env`, `*.pem`, `*.pfx`, `*.p12`, `*.key`, `certs/`, `secrets/`),
`.gitattributes` (LF), `requirements.txt` (`requests`, `python-dotenv`), `.env.example` (formato das
variáveis, sem valor), `scripts/teste_inter.py` (mTLS → token → saldo → extrato dos últimos 30 dias,
não grava nada em disco).
**Testes:** nada rodado. Falta o certificado, que só o dono baixa.
**Aberto:** ver `PENDENCIAS.md`, itens P2-1 a P2-3.

## 2026-11-01 — Descoberta do produto

**O que mudou:** fechado o entendimento de produto, com as decisões D1–D6 ainda em aberto.
**Arquivos:** `docs-dev/a-codar/briefing-descoberta.md` (registro completo da conversa, perguntas e
respostas originais).
**Testes:** não se aplica.
**Aberto:** D1–D6, registradas em `PENDENCIAS.md`.
