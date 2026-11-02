# gestao-financeira — Pendências

> Rastreador **único** (guardrail G6). Se está aberto, está aqui.
> Se não está aqui, não está aberto. Item resolvido sai da lista (o registro fica no `PROGRESS.md`).

**Dono:** 👤 decisão do usuário · 💻 código · 🖥️ servidor/infra

## 🧭 Estado do sistema

| Peça             | Onde está                  | Estado                          |
| ---------------- | -------------------------- | ------------------------------- |
| Backend Django   | `manage.py`, `config/`     | rodando, com os 4 modelos       |
| Banco            | `db.sqlite3` (fora do git) | 4 tabelas de `financas` criadas |
| Modelo de dado   | `financas/models.py`       | pronto                          |
| Suíte de testes  | `financas/tests.py`        | 8 testes, todos passando        |
| Tela / PWA       | `financas/`, `templates/`  | não existe                      |
| Integração Inter | `scripts/teste_inter.py`   | nunca executado, **pausado**    |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID   | Dono | Item                                                                                                                                                                                                                                                                         | Aberto em  |
| ---- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P2-1 | 👤   | Criar a integração no **portal Sandbox** e baixar e ativar certificado e chaves. O sandbox se cria ali, com **login da Comunidade Inter**. O portal só responde das **8h às 20h, de segunda a sexta**. **Pausado** até a fase 7 do plano.                                    | 2026-11-01 |
| P2-2 | 👤   | Converter para PEM se o arquivo vier em `.pfx`, e preencher o `.env` a partir do `.env.example`. Os valores ficam fora do git (G13).                                                                                                                                         | 2026-11-01 |
| P2-3 | 💻   | Rodar `scripts/teste_inter.py` contra o sandbox e conferir os três caminhos (`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`). Vieram da doc pública e nunca foram verificados. **Pausado** até a fase 7 do plano.                                             | 2026-11-01 |
| P2-6 | 👤   | **D4 — escopo da integração.** A API de Empresas cobre a PJ. Conta PF, cartão e boleto de outra titularidade podem exigir Open Finance: não prometer "tudo" antes de confirmar.                                                                                              | 2026-11-01 |
| P2-7 | 💻   | **Host do sandbox não existe.** `cdpj-sandbox.partners.bancointer.com.br`, usado em `scripts/teste_inter.py`, não resolve em DNS (NXDOMAIN em 01/11/2026). O candidato é `cdpj-sandbox.partners.uatinter.co`, que resolve, mas **não foi confirmado** na página Referências. | 2026-11-01 |

## P3 — Médio

| ID   | Dono | Item                                                                                                                                                     | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P3-3 | 👤   | **D6 — onde o backend roda.** Só rede local, túnel ou VPS. Se houver custo recorrente, entra o G20 (custo estimado antes de criar).                      | 2026-11-01 |
| P3-4 | 👤   | Criar o primeiro superusuário, que só o dono pode fazer por causa da senha: `.venv/bin/python manage.py createsuperuser`. Sem ele, o admin não abre. | 2026-11-01 |
| P3-5 | 👤   | Banco local do WSL ainda não existe (o `db.sqlite3` do Windows não veio no clone). Criar com `.venv/bin/python manage.py migrate` quando o dono autorizar (G3); depois o P3-4. | 2026-11-01 |

## P4 — Baixo / melhoria

| ID   | Dono | Item                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P4-2 | 💻   | Instalar `scripts/auditar-referencias.py` (G12/G16) e ajustar `ALVOS`/`RAIZES` a este repositório. Faz sentido quando a pasta `docs-dev/` crescer. | 2026-11-01 |
| P4-3 | 💻   | `RETRABALHO.md` (G17) só nasce quando houver retrabalho a registrar.                                                                               | 2026-11-01 |
