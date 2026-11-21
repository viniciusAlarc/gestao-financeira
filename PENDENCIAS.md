# gestao-financeira — Pendências

> Rastreador **único** (guardrail G6). Se está aberto, está aqui.
> Se não está aqui, não está aberto. Item resolvido sai da lista (o registro fica no `PROGRESS.md`).

**Dono:** 👤 decisão do usuário · 💻 código · 🖥️ servidor/infra

## 🧭 Estado do sistema

| Peça             | Onde está                  | Estado                          |
| ---------------- | -------------------------- | ------------------------------- |
| Backend Django   | `manage.py`, `config/`     | rodando, com os 4 modelos       |
| Banco            | `db.sqlite3` (fora do git) | PC e servidor: migrations 0001 a 0006 |
| Modelo de dado   | `financas/models.py`       | pronto, com `id_externo` e `entra_no_gasto` |
| Suíte de testes  | `financas/tests.py` + arquivos por assunto | 233 testes passando em 20/11 (linha de base commitada: 232) |
| Tela inicial     | `financas/views.py`, `templates/` | pronta; visual revisto em 08/11 (375/360/768/1280) |
| Lançamentos      | `financas/views.py`, `templates/lancamentos.html` | implementado; data editável, editar/desfazer e navegação de mês (08/11) |
| Gastos previstos | `financas/views.py`, `templates/previstos.html` | cadastro fixo mensal que gera o previsto do mês; avulso secundário (08/11) |
| Relatório        | `financas/views.py`, `templates/relatorio.html` | implementado; navegação de mês (08/11) |
| Categorias       | `financas/views.py`, `templates/categorias.html` | criar, editar e desativar; tipo fixo e "fora do gasto" (08/11) |
| UI/UX            | `financas/static/financas/app.css`, `templates/base.html` | revisão de 08/11: navegação responsiva, layout espaçado, mensagens por tipo |
| Segundo login    | admin do Django            | no servidor; uso a dois em andamento (P3-9 encerrada em 2026-11-20) |
| PWA              | `financas/static/financas/` | manifest e ícones conferidos; instalação no celular faz parte do uso a dois (P3-9 encerrada em 2026-11-20) |
| Integração bancária | `financas/pluggy_api.py`, `importacao_pluggy.py`, `importar_pluggy` | importação real, idempotência e fuso OK em 2026-11-18 (P2-13 fechado); rotina automática validada em 2026-11-19 (P2-21 fechado); categorização e recategorização do histórico concluídas em 2026-11-19 (P2-15 fechado) |
| Produção          | PythonAnywhere (conta `viniciusapps`) | **no ar** em https://viniciusapps.pythonanywhere.com; conta, categorias e gastos fixos importados em 2026-11-17; uso real a dois em andamento (P3-9 encerrada em 2026-11-20) |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID   | Dono | Item        | Aberto em |
| ---- | ---- | ----------- | --------- |
| —    | —    | nada aberto | —         |

## P3 — Médio

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P4 — Baixo / melhoria

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |
