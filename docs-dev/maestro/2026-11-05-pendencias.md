# Rodada: P4-2, P4-4, P3-9, P3-3 e P2-6 (pendências do repositório)

2026-11-05 · 5 sessões · 10:14:42 → 11:04:53 · 50 min 11 s

> O cartão foi aprovado às 10:54; as sessões rodaram de 10:54:06 a 11:04:53. A duração total inclui
> a espera pela aprovação, conforme a regra (início = pedido ao porão).

| Tarefa | Sessão | Tempo | O que fez | Arquivos | Testes |
|---|---|---|---|---|---|
| P4-2 · auditor de referências | s1 (Íris) | 4 min 18 s | `RAIZES` com os 12 diretórios reais; `docs-dev/guias/*.md` no `ALVOS_DOC`; corrigiu o falso positivo de base `~/...` na mesma frase; 1 menção histórica reportada e não corrigida | `scripts/auditar-referencias.py` | 62 → 62, OK; auditor exit 0 limpo / exit 0 com 1 achado informativo no `--tudo` |
| P4-4 · conferência visual a 375px | s2 (Ana) | 5 min 22 s | As duas telas ok, sem defeito: `scrollWidth = 375`, nada estourando a borda, contraste 6,5:1; nenhum template/CSS alterado | `config/settings_visual.py` (novo, descartável); screenshots em `/tmp/gestao-visual/` | 62 → 62, OK |
| P3-9 · segundo usuário e PWA (técnica) | s3 | 5 min 08 s | PWA conferido na entrega HTTP (manifest, ícones 192/512 medidos, standalone); conta `Kethlen` criada pelo ORM com autorização do dono (sem senha); `OPERACAO.md` com IP, `.env`/`DJANGO_ALLOWED_HOSTS` e firewall; checklist de uma semana | `docs-dev/guias/OPERACAO.md` | 62 → 62, OK |
| P3-3 · dossiê D6 (onde roda) | s4 | 10 min 39 s | 5 opções com os três números do G20 e links datados; recomendação rede de casa na v1, Tailscale para sair de casa, Cloudflare como plano B, VPS só se preciso; nada criado | `docs-dev/a-codar/02-decisao-d6-onde-roda.md` | nenhum (pesquisa) |
| P2-6 · dossiê D4 (escopo Inter) | s5 | 9 min 46 s | 17 fontes oficiais datadas; API Banking exclusiva de PJ, cobertura e exclusões; Open Finance não serve a app pessoal; mapeamento do `Movimento` e lacunas do modelo | `docs-dev/a-codar/03-decisao-d4-escopo-inter.md` | nenhum (pesquisa) |

**Ficou de fora / pendências:**

- **P4-4** aguarda o "conferi" do dono (a verificação técnica deu ok).
- **P3-9** segue aberta: definir a senha de `Kethlen`, criar o `.env` com `DJANGO_ALLOWED_HOSTS`
  (P2-9), instalar o PWA nos dois celulares e usar uma semana (data alvo 2026-11-12).
- **P3-3** e **P2-6** aguardam decisão do dono; os dossiês estão na mesa.
- **Novos itens:** P2-9 (`.env`/`ALLOWED_HOSTS`), P4-5 (alvos de toque), P4-6 (remover o
  `settings_visual.py` descartável).
- **Melhoria futura (fora do P4-2):** indexar classes Python de `financas/` no `indice_simbolos()`.

**Painel:** não tocado — nenhuma fase avançou de estado (fase 6 aguarda o uso real; fase 7 aguarda
certificado).
**Commits:** pelo pombal, a fazer.
