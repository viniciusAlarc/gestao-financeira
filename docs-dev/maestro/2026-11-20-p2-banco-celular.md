# Rodada: p2 banco celular

**Aprovada:** nenhum comando de teste quebrou (gate rodado pela vila antes e depois).

20/11/2026 · 1 sessão · 16:11 → 16:24 · 13 min 31 s

| Tarefa | Sessão | Tempo | O que fez | Arquivos | Testes | Aceite |
|---|---|---|---|---|---|---|
| t1 | Gina | 8 min 58 s | Gravei `DJANGO_ALLOWED_HOSTS` com o IP da rede de casa no `.env` (P2-9), apliquei a migration 0006 no banco do PC (P2-16) e renomeei a conta "Inter" para "Itaú" com a decisão do dono (P2-14). Os três itens saíram do `PENDENCIAS.md`; `PROGRESS.md` e `AGENTS.md` ficaram com a informação certa. Suíte: 233 antes e depois. | `PROGRESS.md`, `PENDENCIAS.md`, `AGENTS.md` | 233/233 → 233/233 | sim: item por item — P2-9: o `--aplicar` rodou com "pode" e a saída do script confirmou "Atualizei a linha DJANGO_ALLOWED_HOSTS no .env; as outras variáveis não foram tocadas: DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.10.15" (teste no celular é do dono). P2-16: `.venv/bin/python manage.py migrate financas` aplicou a 0006 e `showmigrations financas` mostra `[X] 0006_origem_pluggy` (servidor não tocado). P2-14: decisão do dono registrada em 2026-11-20 (renomear "Inter" → "Itaú") e comando ORM aplicado com "pode", saída "contas renomeadas: 1"; conferência na tela é do dono. |

Tempo = da sessão aberta pela vila até a devolutiva; início = o clique no cartão, fim = o fim do gate.

**Ficou de fora / pendências:** t1: a cópia de segurança `cp db.sqlite3 db.sqlite3.bak-2026-11-20` — o Bash da rodada bloqueia `cp` e o dono optou por seguir sem backup (a 0006 só muda `choices`, não altera dado). Nada mais.
**Roteiro de testes:** não se aplica: nenhuma tarefa mexeu em tela
**Commits:** pelo pombal, a fazer.

## Verificação

| Comando | Antes | Depois | Resultado |
|---|---|---|---|
| `.venv/bin/python manage.py test` | passou, 2 min 30 s | passou, 2 min 3 s | passou |

Antes = linha de base, rodada pela vila antes de abrir as sessões; depois = com todas as tarefas prontas. Saída de cada comando em `~/.claude/maestro/rodadas/20261120-1609-p2-banco-celular/gate/`.

## Custo e ganho

- Tempo de parede (clique → fim do gate): 13 min 31 s
- Linha de base: 2 min 30 s · gate final: 2 min 3 s
- Soma dos tempos das tarefas: 8 min 58 s
- Estimativa em sessão única: 35 min · diferença: a rodada levou 21 min a menos que a estimativa

| Tarefa | Entrada | Saída | Cache criado | Cache lido |
|---|---|---|---|---|
| t1 | 42.560 | 15.013 | 0 | 1.072.896 |
| **Total** | 42.560 | 15.013 | 0 | 1.072.896 |

A estimativa foi declarada antes da rodada; não é medição.

Montado pela vila com as devolutivas das sessões (`~/.claude/maestro/rodadas/20261120-1609-p2-banco-celular/devolutivas/`).
