# gestao-financeira — Pendências

> Rastreador **único** (guardrail G6). Se está aberto, está aqui.
> Se não está aqui, não está aberto. Item resolvido sai da lista (o registro fica no `PROGRESS.md`).

**Dono:** 👤 decisão do usuário · 💻 código · 🖥️ servidor/infra

## 🧭 Estado do sistema

| Peça             | Onde está                | Estado                       |
| ---------------- | ------------------------ | ---------------------------- |
| Integração Inter | `scripts/teste_inter.py` | escrito, **nunca executado** |
| Backend          | —                        | não existe                   |
| Front / PWA      | —                        | não existe                   |
| Banco            | —                        | não existe                   |

## P1 — Crítico (bloqueia uso ou expõe dado)

| ID  | Dono | Item        | Aberto em |
| --- | ---- | ----------- | --------- |
| —   | —    | nada aberto | —         |

## P2 — Alto (retrabalho garantido se ignorado)

| ID   | Dono | Item                                                                                                                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P2-1 | 👤   | Criar a integração "Extrato e Saldos" no Internet Banking PJ e **baixar e ativar** certificado e chaves. Sem isso o script não roda e a fase 1 não começa.                                                                                         | 2026-11-01 |
| P2-2 | 👤   | Converter para PEM se o arquivo vier em `.pfx`, e preencher o `.env` a partir do `.env.example`. Os valores ficam fora do git (G13).                                                                                                               | 2026-11-01 |
| P2-3 | 💻   | Rodar `scripts/teste_inter.py` contra o sandbox e conferir os três caminhos (`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`). Vieram da doc pública e nunca foram verificados no ambiente real: 404 aqui é informação, não defeito. | 2026-11-01 |
| P2-4 | 👤   | **D1 — stack.** Python já está instalado e pesa a favor, mas a decisão é do dono e depende do resto do escopo.                                                                                                                                     | 2026-11-01 |
| P2-5 | 👤   | **D2 — o que é "gasto previsto".** Conta a pagar com data, gasto recorrente ou orçamento por categoria? São três features diferentes e muda o modelo de dados.                                                                                     | 2026-11-01 |
| P2-6 | 👤   | **D4 — escopo da integração.** A API de Empresas cobre a PJ. Conta PF, cartão e boleto de outra titularidade podem exigir Open Finance: não prometer "tudo" antes de confirmar.                                                                    | 2026-11-01 |

## P3 — Médio

| ID   | Dono | Item                                                                                                                                | Aberto em  |
| ---- | ---- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P3-1 | 👤   | **D3 — categorização.** Manual, por regra de descrição, ou as duas. Decidir antes da tela, porque define o modelo de dados.         | 2026-11-01 |
| P3-2 | 👤   | **D5 — duas pessoas.** Quem lança, quem só vê, e se cada uma tem login.                                                             | 2026-11-01 |
| P3-3 | 👤   | **D6 — onde o backend roda.** Só rede local, túnel ou VPS. Se houver custo recorrente, entra o G20 (custo estimado antes de criar). | 2026-11-01 |

## P4 — Baixo / melhoria

| ID   | Dono | Item                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P4-1 | 💻   | Criar `docs-dev/guias/OPERACAO.md` (G14) quando existir back ou front para subir. Hoje não há comando que fique em primeiro plano.                 | 2026-11-01 |
| P4-2 | 💻   | Instalar `scripts/auditar-referencias.py` (G12/G16) e ajustar `ALVOS`/`RAIZES` a este repositório. Faz sentido quando a pasta `docs-dev/` crescer. | 2026-11-01 |
| P4-3 | 💻   | `RETRABALHO.md` (G17) só nasce quando houver retrabalho a registrar.                                                                               | 2026-11-01 |
