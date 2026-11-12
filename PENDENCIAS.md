# gestao-financeira — Pendências

> Rastreador **único** (guardrail G6). Se está aberto, está aqui.
> Se não está aqui, não está aberto. Item resolvido sai da lista (o registro fica no `PROGRESS.md`).

**Dono:** 👤 decisão do usuário · 💻 código · 🖥️ servidor/infra

## 🧭 Estado do sistema

| Peça             | Onde está                  | Estado                          |
| ---------------- | -------------------------- | ------------------------------- |
| Backend Django   | `manage.py`, `config/`     | rodando, com os 4 modelos       |
| Banco            | `db.sqlite3` (fora do git) | 5 tabelas de `financas` criadas; migrations 0001 a 0005 aplicadas |
| Modelo de dado   | `financas/models.py`       | pronto, com `id_externo` e `entra_no_gasto` |
| Suíte de testes  | `financas/tests.py` + arquivos por assunto | 213 testes, todos passando |
| Tela inicial     | `financas/views.py`, `templates/` | pronta; visual revisto em 08/11 (375/360/768/1280) |
| Lançamentos      | `financas/views.py`, `templates/lancamentos.html` | implementado; data editável, editar/desfazer e navegação de mês (08/11) |
| Gastos previstos | `financas/views.py`, `templates/previstos.html` | cadastro fixo mensal que gera o previsto do mês; avulso secundário (08/11) |
| Relatório        | `financas/views.py`, `templates/relatorio.html` | implementado; navegação de mês (08/11) |
| Categorias       | `financas/views.py`, `templates/categorias.html` | criar, editar e desativar; tipo fixo e "fora do gasto" (08/11) |
| UI/UX            | `financas/static/financas/app.css`, `templates/base.html` | revisão de 08/11: navegação responsiva, layout espaçado, mensagens por tipo |
| Segundo login    | admin do Django            | conta `Kethlen` criada; falta a senha (P3-9) |
| PWA              | `financas/static/financas/` | manifest e ícones conferidos na entrega HTTP; instalação no celular pendente (P3-9) |
| Integração bancária | `financas/pluggy_api.py`, `importacao_pluggy.py`, `importar_pluggy` | cliente, importador e comando prontos e testados; falta rodar com credencial e `itemId` (P2-12) |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID   | Dono | Item                                                                                                                                                                                                                                                                         | Aberto em  |
| ---- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P2-9 | 👤   | **Celular sem acesso por falta de `.env`.** O `.env` já existe (criado em 2026-11-09), mas sem `DJANGO_ALLOWED_HOSTS` com o IP da máquina o celular leva `DisallowedHost`. Passo a passo em `docs-dev/guias/OPERACAO.md`. | 2026-11-05 |
| P2-12 | 👤   | **Aplicação na Pluggy.** Criar a aplicação no dashboard da Pluggy, habilitar o conector do **Meu Pluggy** (200) e obter `client_id`, `client_secret` e o `itemId` da conexão do Itaú; preencher no `.env` (G13). Sem isso não há como ler saldo nem extrato. | 2026-11-09 |
| P2-13 | 💻   | **Verificação real da importação da Pluggy.** Código pronto e testado (cliente, importador e `importar_pluggy`, 50 testes novos). Falta rodar `--dry-run` contra a conta real, depois do P2-12, conferir o primeiro extrato e o fuso do campo `date` (UTC x GMT-3). | 2026-11-09 |
| P2-14 | 👤   | **A conta "Inter" no app.** Existe uma `Conta` chamada "Inter" no banco real; renomear para "Itaú" ou criar outra é mudança de dado (G3). Decidir o que fazer antes da primeira importação. | 2026-11-09 |
| P2-15 | 👤   | **Categorias da Pluggy.** Todo movimento importado cai em "Não categorizado"; o campo `category` da Pluggy não é mapeado. O `importar_pluggy --dry-run` mostra a contagem por categoria para servir à decisão. | 2026-11-10 |
| P2-16 | 👤   | **Aplicar a migration 0006 no banco real** (novo valor `pluggy` em `Movimento.origem`). O arquivo está escrito; o classificador de permissão exige um "pode" do dono nomeando a mudança no banco. Comando: `.venv/bin/python manage.py migrate financas`. | 2026-11-10 |

## P3 — Médio

| ID   | Dono | Item                                                                                                                                                     | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P3-3 | 👤   | **D6 — onde o backend roda.** Aguardando decisão do dono; dossiê com 5 opções e os três números do G20 em `docs-dev/a-codar/02-decisao-d6-onde-roda.md` (recomendação: rede de casa na v1; Tailscale para sair de casa). Nada criado. | 2026-11-01 |
| P3-9 | 👤   | **Verificação da fase 6.** Conta `Kethlen` criada em 05/11 (sem senha — o dono define no admin ou com `manage.py changepassword Kethlen`). Falta: `.env` com `DJANGO_ALLOWED_HOSTS` (P2-9), instalar o PWA nos dois celulares e usar por uma semana com as duas pessoas lançando. Data alvo: 2026-11-12. Checklist em `docs-dev/rodada-2026-11-05/s3-p3-9.md`. | 2026-11-03 |

## P4 — Baixo / melhoria

| ID   | Dono | Item                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P4-4 | 👤   | **Conferência visual a 375px.** Aguardando o "conferi" do dono; a verificação técnica da rodada de 05/11 deu as duas telas ok, sem defeito (evidência em `docs-dev/rodada-2026-11-05/s2-p4-4.md`). | 2026-11-03 |
| P4-6 | 👤   | **Remover o descartável da conferência visual.** `config/settings_visual.py` (novo, não versionado) e `/tmp/gestao-visual/` — autorizar a remoção. | 2026-11-05 |
