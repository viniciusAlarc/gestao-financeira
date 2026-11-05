# Prompt para o maestro — rodada 2026-11-05-b

Você é o maestro da rodada **2026-11-05-b** do projeto `gestao-financeira`.
Abra **5 sessões em paralelo**, uma por tarefa do briefing:
`/home/vinicius/Documents/Projetos-pessoais/gestao-financeira/docs-dev/rodada-2026-11-05-b/00-briefing.md`

## Antes de abrir

1. Leia o briefing inteiro. Ele tem as 5 tarefas (T1 a T5), a matriz de donos de arquivo e as
   regras comuns.
2. Confirme o pré-requisito T0: a migration `0003` **já foi aplicada** no banco real e as
   categorias "Não categorizado" (despesa e receita) e "Investimento" (fora do gasto) já existem.
   **Nenhuma sessão roda `migrate`.**
3. A linha de base é **68 testes verdes**. A árvore tem as mudanças do P4-5 e da fase 7 (D4/P2-8)
   **ainda sem commit**; elas são a base da rodada, não trabalho de outra sessão. Ninguém as
   reverte.

## Como abrir

- Uma sessão por tarefa, com a **seção inteira** da tarefa colada no prompt (não só o título).
- Cada sessão só pode criar/editar os arquivos da coluna dela na matriz. Arquivo compartilhado é
  leitura.
- Ninguém edita `PROGRESS.md`, `PENDENCIAS.md` nem `docs-dev/painel.json`: o rastro de cada uma
  vai em `docs-dev/rodada-2026-11-05-b/sN-*.md`.
- Ninguém commita, faz stash/reset/checkout, abre o `db.sqlite3` ou o `.env`, nem roda migration.
- Só a T5 sobe servidor (porta 8010, banco descartável).
- Se duas tarefas pedirem o mesmo arquivo, **pare e ajuste o escopo antes de abrir**. A matriz foi
  montada para não haver sobreposição.

## As 5 tarefas

| Sessão | Tarefa | Entrega | Arquivos da sessão |
| --- | --- | --- | --- |
| **T1** | Importador do Inter | módulo + comando + testes | `financas/importacao_inter.py`, `financas/management/**`, `financas/test_importacao.py` (todos novos) |
| **T2** | Acesso pelo celular (P2-9) | script + teste + guia | `scripts/preparar_acesso_celular.sh`, `config/settings.py` (só se necessário), `docs-dev/guias/OPERACAO.md`, `financas/test_acesso_celular.py` |
| **T3** | Segurança e privacidade | testes + relatório | `financas/test_seguranca.py` (novo; não corrige código) |
| **T4** | Checklist do Inter para o dono | guia novo | `docs-dev/guias/INTER-PASSO-A-PASSO.md` (novo) |
| **T5** | Acessibilidade e teclado | templates + CSS + teste | `templates/*.html`, `financas/static/financas/app.css`, `financas/test_acessibilidade.py` (novo) |

## No fim

Devolva em relatório curto:

1. as 5 sessões abertas e qual tarefa cada uma recebeu;
2. a confirmação de que nenhum arquivo da matriz ficou com dois donos;
3. o que cada uma entregou, com testes antes/depois;
4. a lista de arquivos alterados por sessão, para o coordenador consolidar o `PROGRESS.md`, o
   `PENDENCIAS.md` e o `docs-dev/painel.json`.

**Seu papel é coordenação, não escopo.** Não implemente as tarefas: abra, distribua, arbitre
conflitos e devolva o resultado.
