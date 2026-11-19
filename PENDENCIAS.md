# gestao-financeira — Pendências

> Rastreador **único** (guardrail G6). Se está aberto, está aqui.
> Se não está aqui, não está aberto. Item resolvido sai da lista (o registro fica no `PROGRESS.md`).

**Dono:** 👤 decisão do usuário · 💻 código · 🖥️ servidor/infra

## 🧭 Estado do sistema

| Peça             | Onde está                  | Estado                          |
| ---------------- | -------------------------- | ------------------------------- |
| Backend Django   | `manage.py`, `config/`     | rodando, com os 4 modelos       |
| Banco            | `db.sqlite3` (fora do git) | PC: migrations 0001 a 0005; servidor: 0001 a 0006 |
| Modelo de dado   | `financas/models.py`       | pronto, com `id_externo` e `entra_no_gasto` |
| Suíte de testes  | `financas/tests.py` + arquivos por assunto | 214 testes, todos passando |
| Tela inicial     | `financas/views.py`, `templates/` | pronta; visual revisto em 08/11 (375/360/768/1280) |
| Lançamentos      | `financas/views.py`, `templates/lancamentos.html` | implementado; data editável, editar/desfazer e navegação de mês (08/11) |
| Gastos previstos | `financas/views.py`, `templates/previstos.html` | cadastro fixo mensal que gera o previsto do mês; avulso secundário (08/11) |
| Relatório        | `financas/views.py`, `templates/relatorio.html` | implementado; navegação de mês (08/11) |
| Categorias       | `financas/views.py`, `templates/categorias.html` | criar, editar e desativar; tipo fixo e "fora do gasto" (08/11) |
| UI/UX            | `financas/static/financas/app.css`, `templates/base.html` | revisão de 08/11: navegação responsiva, layout espaçado, mensagens por tipo |
| Segundo login    | admin do Django            | no servidor, criar a segunda conta no admin (P3-9) |
| PWA              | `financas/static/financas/` | manifest e ícones conferidos na entrega HTTP; instalação no celular pendente (P3-9) |
| Integração bancária | `financas/pluggy_api.py`, `importacao_pluggy.py`, `importar_pluggy` | importação real, idempotência e fuso OK em 2026-11-18 (P2-13 fechado); rotina automática validada em 2026-11-19 (P2-21 fechado); mapa completo de categorias implementado, falta o deploy e a recategorização (P2-15 em fechamento) |
| Produção          | PythonAnywhere (conta `viniciusapps`) | **no ar** em https://viniciusapps.pythonanywhere.com; conta, categorias e gastos fixos importados em 2026-11-17; falta o uso real (P3-9) |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID   | Dono | Item                                                                                                                                                                                                                                                                         | Aberto em  |
| ---- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P2-9 | 👤   | **Celular sem acesso por falta de `.env`.** O `.env` já existe (criado em 2026-11-09), mas sem `DJANGO_ALLOWED_HOSTS` com o IP da máquina o celular leva `DisallowedHost`. Passo a passo em `docs-dev/guias/OPERACAO.md`. | 2026-11-05 |
| P2-14 | 👤   | **A conta "Inter" no banco do PC.** Existe uma `Conta` chamada "Inter" no banco real do PC; renomear para "Itaú" ou criar outra é mudança de dado (G3). No servidor, a conta importada está com o nome escolhido; isso não bloqueia a importação no servidor. | 2026-11-09 |
| P2-15 | 👤   | **Categorias automáticas.** Mapa completo (23 categorias do histórico) implementado em 2026-11-19; "Compras" e "Rendimentos" foram criadas no app. Falta o deploy e a recategorização do histórico (backup antes). | 2026-11-10 |
| P2-16 | 👤   | **Aplicar a migration 0006 no banco do PC** (novo valor `pluggy` em `Movimento.origem`). O arquivo está escrito; o classificador de permissão exige um "pode" do dono nomeando a mudança no banco. Comando: `.venv/bin/python manage.py migrate financas`. No servidor, a 0006 já está aplicada. | 2026-11-10 |

## P3 — Médio

| ID   | Dono | Item                                                                                                                                                     | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P3-9 | 👤   | **Verificação da fase 6 no servidor.** Criar a segunda conta no admin (se ainda não existir), instalar o PWA nos dois celulares e usar por uma semana com as duas pessoas lançando em https://viniciusapps.pythonanywhere.com. O checklist antigo (`docs-dev/rodada-2026-11-05/s3-p3-9.md`) é do banco local e serve de referência. | 2026-11-03 |
| P3-10 | 👤  | **Renovação mensal do web app.** O plano grátis do PythonAnywhere expira a cada mês; quando o e-mail avisar, renovar na aba **Web**. Sem isso, o app fica fora do ar até o clique (os arquivos não são apagados). | 2026-11-17 |
| P3-12 | 👤  | **Backup semanal do banco.** Baixar o `db.sqlite3` pela aba **Files** toda semana e guardar no PC com a data. O plano grátis não tem tarefa agendada nem backup automático. | 2026-11-17 |

## P4 — Baixo / melhoria

| ID   | Dono | Item                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P4-4 | 👤   | **Conferência visual a 375px.** Aguardando o "conferi" do dono; a verificação técnica da rodada de 05/11 deu as duas telas ok, sem defeito (evidência em `docs-dev/rodada-2026-11-05/s2-p4-4.md`). | 2026-11-03 |
| P4-6 | 👤   | **Remover o descartável da conferência visual.** `config/settings_visual.py` (novo, não versionado) e `/tmp/gestao-visual/` — autorizar a remoção. | 2026-11-05 |
