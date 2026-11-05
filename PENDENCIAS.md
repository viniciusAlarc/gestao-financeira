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
| Segundo login    | admin do Django            | conta `Kethlen` criada; falta a senha (P3-9) |
| PWA              | `financas/static/financas/` | manifest e ícones conferidos na entrega HTTP; instalação no celular pendente (P3-9) |
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
| P2-9 | 👤   | **Celular sem acesso por falta de `.env`.** Hoje o `.env` não existe; sem `DJANGO_ALLOWED_HOSTS` com o IP da máquina, o celular leva `DisallowedHost`. Passo a passo em `docs-dev/guias/OPERACAO.md`. | 2026-11-05 |

## P3 — Médio

| ID   | Dono | Item                                                                                                                                                     | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P3-3 | 👤   | **D6 — onde o backend roda.** Aguardando decisão do dono; dossiê com 5 opções e os três números do G20 em `docs-dev/a-codar/02-decisao-d6-onde-roda.md` (recomendação: rede de casa na v1; Tailscale para sair de casa). Nada criado. | 2026-11-01 |
| P3-9 | 👤   | **Verificação da fase 6.** Conta `Kethlen` criada em 05/11 (sem senha — o dono define no admin ou com `manage.py changepassword Kethlen`). Falta: `.env` com `DJANGO_ALLOWED_HOSTS` (P2-9), instalar o PWA nos dois celulares e usar por uma semana com as duas pessoas lançando. Data alvo: 2026-11-12. Checklist em `docs-dev/rodada-2026-11-05/s3-p3-9.md`. | 2026-11-03 |

## P4 — Baixo / melhoria

| ID   | Dono | Item                                                                                                                                               | Aberto em  |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| P4-4 | 👤   | **Conferência visual a 375px.** Aguardando o "conferi" do dono; a verificação técnica da rodada de 05/11 deu as duas telas ok, sem defeito (evidência em `docs-dev/rodada-2026-11-05/s2-p4-4.md`). | 2026-11-03 |
| P4-5 | 💻   | **Alvos de toque pequenos.** "Paguei" 67×36, links da navegação 28–30px e "Sair" 24×20 (abaixo do mínimo AA 24×24). Envolve `app.css` e `base.html` (telas compartilhadas). Evidência em `s2-p4-4.md`. | 2026-11-05 |
| P4-6 | 👤   | **Remover o descartável da conferência visual.** `config/settings_visual.py` (novo, não versionado) e `/tmp/gestao-visual/` — autorizar a remoção. | 2026-11-05 |
