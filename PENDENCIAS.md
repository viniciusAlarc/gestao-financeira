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
| Suíte de testes  | `financas/tests.py`        | 62 testes, todos passando       |
| Tela inicial     | `financas/views.py`, `templates/` | pronta e verificada a 375px |
| Lançamentos      | `financas/views.py`, `templates/lancamentos.html` | implementado e verificado |
| Gastos previstos | `financas/views.py`, `templates/previstos.html` | implementado e validado por testes |
| Relatório        | `financas/views.py`, `templates/relatorio.html` | implementado e validado por testes |
| Segundo login    | admin do Django            | a criar pelo dono (P3-9)        |
| PWA              | `financas/static/financas/` | manifest e ícones prontos; instalação no celular pendente (P3-9) |
| Integração Inter | `scripts/teste_inter.py`   | host corrigido; aguardando `.env` e certificado |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID   | Dono | Item                                                                                                                                                                                                                                                                         | Aberto em  |
| ---- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P2-1 | 👤   | Criar a integração no **portal Sandbox** e baixar e ativar certificado e chaves. O sandbox se cria ali, com **login da Comunidade Inter**. O portal só responde das **8h às 20h, de segunda a sexta**. **Pausado** até a fase 7 do plano.                                    | 2026-11-01 |
| P2-2 | 👤   | Converter para PEM se o arquivo vier em `.pfx`, e preencher o `.env` a partir do `.env.example`. Os valores ficam fora do git (G13).                                                                                                                                         | 2026-11-01 |
| P2-3 | 💻   | Rodar `scripts/teste_inter.py` contra o sandbox e conferir os três caminhos (`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`). Vieram da doc pública e nunca foram verificados. Rodar quando `.env` e certificado estiverem prontos. | 2026-11-01 |
| P2-6 | 👤   | **D4 — escopo da integração.** A API de Empresas cobre a PJ. Conta PF, cartão e boleto de outra titularidade podem exigir Open Finance: não prometer "tudo" antes de confirmar.                                                                                              | 2026-11-01 |
| P2-8 | 👤   | **Mapeamento da importação do Inter.** Confirmar se a conta é PJ, qual `Conta` do app recebe os movimentos, quais categorias usar e qual chave evita duplicação. | 2026-11-03 |

## P3 — Médio

| ID   | Dono | Item                                                                                                                                                     | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P3-3 | 👤   | **D6 — onde o backend roda.** Só rede local, túnel ou VPS. Se houver custo recorrente, entra o G20 (custo estimado antes de criar).                      | 2026-11-01 |
| P3-9 | 👤   | **Verificação da fase 6.** Criar o segundo usuário no admin, instalar o PWA no celular e usar por uma semana com as duas pessoas lançando. | 2026-11-03 |

## P4 — Baixo / melhoria

| ID   | Dono | Item                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P4-2 | 💻   | Instalar `scripts/auditar-referencias.py` (G12/G16) e ajustar `ALVOS`/`RAIZES` a este repositório. Faz sentido quando a pasta `docs-dev/` crescer. | 2026-11-01 |
| P4-4 | 👤   | Conferência visual das telas `/previstos/` e `/relatorio/` a 375px no navegador. O comportamento já está coberto por testes; é só a conferência de layout. | 2026-11-03 |
