# gestao-financeira — Pendências

> Rastreador **único** (guardrail G6). Se está aberto, está aqui.
> Se não está aqui, não está aberto. Item resolvido sai da lista (o registro fica no `PROGRESS.md`).

**Dono:** 👤 decisão do usuário · 💻 código · 🖥️ servidor/infra

## 🧭 Estado do sistema

| Peça             | Onde está                  | Estado                          |
| ---------------- | -------------------------- | ------------------------------- |
| Backend Django   | `manage.py`, `config/`     | rodando, com os modelos de finanças e da rotina |
| Banco            | `db.sqlite3` (fora do git) | PC: 0001 a 0008 aplicadas (25/11); servidor: 0001 a 0006 (0007 e 0008 pendentes, P2-22 e P2-23) |
| Modelo de dado   | `financas/models.py`       | pronto, com `id_externo` e `entra_no_gasto`; `Tarefa` e `ConclusaoTarefa` da rotina (22/11); `EntradaFixa` da renda fixa (22/11) |
| Suíte de testes  | `financas/tests.py` + arquivos por assunto | 288 testes passando em 25/11 (linha de base da rotina: 233) |
| Tela inicial     | `financas/views.py`, `templates/inicio.html` | pronta; bloco "Fixo do mês" (entra, sai, sobra) e previsto em aberto só do mês corrente (22/11); visual de 08/11 |
| Lançamentos      | `financas/views.py`, `templates/lancamentos.html` | implementado; data editável, editar/desfazer e navegação de mês (08/11) |
| Gastos previstos | `financas/views.py`, `templates/previstos.html` | lista única do mês com navegação, check "Pago" e entradas fixas na mesma lista (22/11); cadastro fixo mensal e avulso secundário (08/11) |
| Relatório        | `financas/views.py`, `templates/relatorio.html` | implementado; navegação de mês (08/11) |
| Categorias       | `financas/views.py`, `templates/categorias.html` | criar, editar e desativar; tipo fixo e "fora do gasto" (08/11) |
| Rotina           | `financas/views.py`, `templates/rotina.html` | tarefas por pessoa, check diário com histórico e leitura da rotina do outro perfil (22/11); 0007 aplicada no PC em 25/11; falta publicar e aplicar no servidor (P2-22) |
| UI/UX            | `financas/static/financas/app.css`, `templates/base.html` | direção A "Papel e tinta" implementada em 2026-11-25 (tokens, serifa, cinco abas + "Mais" no celular, início, lançamentos e previstos); falta conferir no celular (P3-16) |
| Segundo login    | admin do Django            | no servidor; uso a dois em andamento (P3-9 encerrada em 2026-11-20) |
| PWA              | `financas/static/financas/` | manifest e ícones conferidos; tema `#f3eee4` da direção A (25/11); instalação no celular faz parte do uso a dois (P3-9 encerrada em 2026-11-20) |
| Integração bancária | `financas/pluggy_api.py`, `importacao_pluggy.py`, `importar_pluggy` | importação real, idempotência e fuso OK em 2026-11-18 (P2-13 fechado); rotina automática validada em 2026-11-19 (P2-21 fechado); categorização e recategorização do histórico concluídas em 2026-11-19 (P2-15 fechado) |
| Produção          | PythonAnywhere (conta `viniciusapps`) | **no ar** em https://viniciusapps.pythonanywhere.com; conta, categorias e gastos fixos importados em 2026-11-17; uso real a dois em andamento (P3-9 encerrada em 2026-11-20) |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID    | Dono | Item        | Aberto em |
| ----- | ---- | ----------- | --------- |
| P2-22 | 🖥️   | Publicar a rotina no servidor: `git pull`, `migrate`, `collectstatic` e Reload. (No PC, a 0007 foi aplicada em 2026-11-25.) Espera o "pode" (G3) | 2026-11-25 |
| P2-23 | 🖥️   | Aplicar a migration 0008 (entrada fixa) no servidor, no mesmo `migrate`/`git pull` e com o "pode" (G3). (No PC, aplicada em 2026-11-25.) | 2026-11-25 |

## P3 — Médio

| ID    | Dono | Item        | Aberto em |
| ----- | ---- | ----------- | --------- |
| P3-13 | 👤   | Conferir no celular a aba Rotina (criar, marcar e desmarcar o check, ver a rotina do outro) e a barra de seis abas a 360 e 375px | 2026-11-25 |
| P3-16 | 👤   | Conferir no celular a direção A (início, lançamentos, previstos com estados, barra de cinco abas + "Mais") a 360 e 375px, e o tema novo do PWA | 2026-11-25 |

## P4 — Baixo / melhoria

| ID    | Dono | Item        | Aberto em |
| ----- | ---- | ----------- | --------- |
| P4-8  | 👤   | Generalizar `GastoFixo` e `EntradaFixa` num só modelo (decisão futura registrada na t3, não agora) | 2026-11-25 |
| P4-9  | 👤   | Self-host da fonte Fraunces (SIL OFL 1.1) para os títulos; o app usa a serifa do sistema como a amostra | 2026-11-25 |
