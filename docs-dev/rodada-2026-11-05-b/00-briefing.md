# Rodada paralela 2026-11-05-b — 5 sessões

> Preparado por Fred em 2026-11-05, para o dono distribuir uma seção por sessão.
> **Regra de ouro:** cada arquivo tem **um dono**. O que não está na coluna da sessão é leitura.
> Nenhuma sessão commita, faz stash/reset/checkout ou toca no banco real.

## T0 — Pré-requisito (concluído em 2026-11-05 pelo coordenador)

- **P2-10 fechado:** a migration `0003` foi aplicada no `db.sqlite3` real e as categorias
  "Não categorizado" (despesa e receita) e "Investimento" (`entra_no_gasto=False`) foram criadas.
- `showmigrations` confirma a `0003`; a suíte está em **68 testes verdes**.
- As cinco sessões **não** aplicam migration e **não** abrem o banco real.

## Regras para as 5 sessões

1. Ler `AGENTS.md`, `PENDENCIAS.md`, `PROGRESS.md` e o(s) documento(s) da sua tarefa.
2. Só criar/editar os arquivos da sua coluna na matriz. Arquivo compartilhado é leitura.
3. **Não editar** `PROGRESS.md`, `PENDENCIAS.md` nem `docs-dev/painel.json`: o coordenador
   consolida no fim. O rastro de cada sessão vai em `docs-dev/rodada-2026-11-05-b/sN-*.md`.
4. Não abrir `db.sqlite3`, `.env`, extrato nem dump (regra 2 do `AGENTS.md`). Não imprimir
   segredo em terminal, log ou resposta (G13).
5. Não rodar `migrate` no banco real, não criar recurso pago, não instalar nada fora do repo
   sem o ok do dono.
6. Não commitar, não fazer stash/reset/checkout e não reverter arquivo de outra sessão. Arquivo
   que mudou depois da sua leitura é trabalho dela: encaixe (G21).
7. Testes novos em arquivo próprio (`financas/test_*.py`). **Não editar `financas/tests.py`**,
   que é compartilhado.
8. Rodar `.venv/bin/python manage.py test` antes e depois; reportar o número real. A suíte pode
   ficar transitoriamente vermelha por causa de outra sessão: reporte, não conserte o arquivo dela.
9. Só a T5 sobe servidor (porta 8010, banco descartável). As outras usam o cliente de teste.
10. Relatório final em `sN-*.md`: o que fez, arquivos, testes antes/depois, evidência, o que
    ficou de fora e por quê.

**Linha de base:** 68 testes, todos OK em 2026-11-05. Migration `0003` aplicada no banco real e
categorias padrão criadas (T0 acima). A árvore tem as mudanças do P4-5 e da fase 7 (D4/P2-8)
**ainda sem commit**; elas são a base da rodada, não trabalho de outra sessão. Nenhuma sessão deve
revertê-las.

## Matriz de donos de arquivo

| Tarefa | Cria / edita | Lê (não edita) |
| --- | --- | --- |
| **T1** Importador | `financas/importacao_inter.py` (novo), `financas/management/**` (novo), `financas/test_importacao.py` (novo), `s1-importador.md` | `financas/models.py`, `financas/admin.py`, `docs-dev/a-codar/03-*`, `04-*` |
| **T2** Celular | `scripts/preparar_acesso_celular.sh` (novo), `config/settings.py` (só se houver lacuna real), `docs-dev/guias/OPERACAO.md`, `financas/test_acesso_celular.py` (novo), `s2-acesso-celular.md` | `.env.example`, `AGENTS.md`, `PENDENCIAS.md` |
| **T3** Segurança | `financas/test_seguranca.py` (novo), `s3-seguranca.md` | `config/settings.py`, `config/urls.py`, `financas/views.py`, `financas/urls.py`, `financas/models.py`, `templates/`, `AGENTS.md` |
| **T4** Checklist Inter | `docs-dev/guias/INTER-PASSO-A-PASSO.md` (novo), `s4-inter-checklist.md` | `scripts/teste_inter.py`, `.env.example`, `03-*`, `04-*`, `OPERACAO.md` |
| **T5** Acessibilidade | `templates/*.html`, `financas/static/financas/app.css`, `financas/test_acessibilidade.py` (novo), `s5-acessibilidade.md` | `financas/views.py`, `s2-p4-4.md`, `config/settings_visual.py` (só usar) |

Compartilhados só de leitura (todos): `financas/tests.py`, `PENDENCIAS.md`, `PROGRESS.md`,
`docs-dev/painel.json`.

---

## T1 — Importador do Inter (núcleo, sem credencial)

**Objetivo:** transformar um payload do `/extrato/completo` (documentado, ainda não exercitado)
em `Movimento`, de forma idempotente, com um comando que lê um JSON de arquivo e um `--dry-run`.

**Contexto obrigatório:** `docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md` (decisão completa)
e `03-decisao-d4-escopo-inter.md` (campos do extrato). Não chamar a API; não usar credencial.

**Entregáveis:**
1. `financas/importacao_inter.py` com uma função/serviço `importar_extrato(transacoes, conta,
   usuario=None, dry_run=False)` que:
   - usa `dataTransacao` e, se vazia, `dataInclusao`;
   - converte `valor` para `Decimal` positivo; o sinal vem de `tipoOperacao` (`D` = despesa,
     `C` = receita); qualquer outro valor é erro daquela transação, não silêncio;
   - grava `origem=inter`, `conta` recebida, `id_externo=idTransacao`; transação sem
     `idTransacao` deve ser **recusada e reportada** (não inventar chave composta);
   - categoria: `tipoTransacao=INVESTIMENTO` → "Investimento" (despesa, `entra_no_gasto=False`);
     `ESTORNO`/`CASHBACK` → categoria própria do tipo; o resto → "Não categorizado" do tipo;
   - `descricao` = `titulo` + `descricao`, truncada em 120;
   - pula transação cujo `(conta, id_externo)` já existe (idempotência) e duplicata dentro do
     próprio payload;
   - usuário técnico `Inter` criado com `set_unusable_password()`, sem staff/superuser;
   - `dry_run=True` não escreve nada (nem categoria, nem usuário, nem movimento);
   - devolve um relatório com criados, pulados e erros.
2. `financas/management/commands/importar_inter.py` com `--arquivo` (JSON), `--conta` (nome
   exato) e `--dry-run`; imprime o resumo e sai com código 1 se houver erro.
   Criar os `__init__.py` das pastas novas.
3. `financas/test_importacao.py` com payload inventado: criação, idempotência (importar duas
   vezes), `dry_run` sem escrita, fallback de data, investimento fora do gasto, truncamento,
   D/C e usuário técnico sem senha utilizável.
4. `docs-dev/rodada-2026-11-05-b/s1-importador.md`.

**Não faça:** chamar a API, editar `models.py`/`views.py`/`settings.py`/`tests.py`, usar dado
real, inventar endpoint ou campo, criar migration. O schema do extrato é o documentado; o
sandbox ainda vai confirmar sinal do valor e estabilidade do `idTransacao` (P2-3).

**Aceite:** suíte completa verde com os testes novos; `--dry-run` comprovadamente não grava;
duas importações do mesmo payload deixam um movimento por `idTransacao`.

---

## T2 — Acesso pelo celular e operação (P2-9)

**Objetivo:** deixar o acesso da rede de casa a um comando, sem escrever segredo no repositório,
e fechar a documentação do primeiro uso no celular.

**Contexto:** `docs-dev/guias/OPERACAO.md` já explica IP, `DJANGO_ALLOWED_HOSTS`, firewall e
instalação do PWA. `config/settings.py` já lê `DJANGO_ALLOWED_HOSTS` do `.env` com padrão
`localhost,127.0.0.1`. O que falta é tirar o trabalho manual e provar o comportamento.

**Entregáveis:**
1. `scripts/preparar_acesso_celular.sh` (novo): descobre o primeiro IPv4 com `hostname -I`,
   mostra o bloco exato para o `.env` (`DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,<ip>`) e avisa
   se o `.env` não existe. Por padrão só **imprime**; com `--aplicar`, acrescenta a linha sem
   apagar as outras variáveis e sem imprimir valor de segredo. Não criar `.env` com segredo.
2. `financas/test_acesso_celular.py` (novo): com `override_settings(ALLOWED_HOSTS=[...])`, o
   cliente com `HTTP_HOST` permitido abre o login (200) e o host fora da lista recebe 400.
3. Atualizar `docs-dev/guias/OPERACAO.md` com o uso do script, o checklist de 5 minutos e a
   observação de que o `.env` é do dono (G13).
4. `s2-acesso-celular.md` com os testes e o que o dono ainda precisa rodar.

**Não faça:** editar templates, CSS, models, `tests.py`; escrever o `.env` real sem o dono;
subir servidor (use o cliente de teste). Se `config/settings.py` não precisar mudar, não mude.

**Aceite:** script testado em diretório temporário; testes novos verdes; `OPERACAO.md` com o
passo a passo que o dono consegue seguir sem mim.

---

## T3 — Segurança e privacidade antes do uso real

**Objetivo:** revisar o app como ele vai ser usado (duas pessoas, rede de casa, HTTP) e deixar
testes de regressão para o que é crítico. **Não corrigir código de app nesta tarefa:** achar,
provar e recomendar.

**Contexto:** `AGENTS.md` (regras 1 e 2), guardrails G9 e G13, `config/settings.py`,
`config/urls.py`, `financas/urls.py`, `financas/views.py`, `templates/`. Não abrir `db.sqlite3`
nem `.env`.

**Entregáveis:**
1. `financas/test_seguranca.py` (novo) cobrindo, no mínimo:
   - todas as views do app exigem login (`inicio`, `lancamentos`, `previstos`, `relatorio`,
     `pagar_previsto`); `login` é pública;
   - `pagar_previsto` e `logout` recusam GET e exigem CSRF (cliente com
     `enforce_csrf_checks=True`);
   - admin exige staff (anônimo e usuário comum não entram);
   - host fora de `ALLOWED_HOSTS` recebe 400.
2. `s3-seguranca.md` com achados classificados (crítico/alto/médio/baixo), cada um com
   `arquivo:linha`, evidência e recomendação. Olhar especialmente:
   - `DEBUG` padrão `1` (stack trace exposto na rede de casa);
   - permissão do `.django-secret` (hoje 644) e do `db.sqlite3`;
   - `config/settings_visual.py` (untracked) entra como usuário automático — risco se alguém
     subir com ele; hoje é descartável e está no P4-6;
   - cookies de sessão/CSRF, `SECURE_*`, `X_FRAME_OPTIONS`;
   - ausência de limite de tentativas de login (registrar como futuro, não implementar);
   - nada de segredo em arquivo versionado (varrer com `git ls-files`/`grep`).
3. Lista curta do que **bloqueia** o uso real e do que pode esperar.

**Não faça:** editar `settings.py`, views, templates ou `tests.py`; rodar servidor; abrir banco
real; instalar dependência. Se achar algo crítico, pare e reporte.

**Aceite:** testes novos verdes; relatório com evidência e recomendação acionável; nenhum
segredo copiado para o relatório.

---

## T4 — Checklist operacional do Inter para o dono (P2-1/P2-2/P2-3)

**Objetivo:** transformar o dossiê em um passo a passo que o dono executa sozinho no portal,
sem ida e volta, e que deixa claro o que é sucesso e o que é erro esperado.

**Contexto obrigatório:** `docs-dev/a-codar/03-decisao-d4-escopo-inter.md`,
`04-decisao-d4-p2-8-importacao.md`, `scripts/teste_inter.py`, `.env.example`,
`docs-dev/guias/OPERACAO.md`. Não editar nenhum deles.

**Entregável:** `docs-dev/guias/INTER-PASSO-A-PASSO.md` (novo), com:
- janela do portal (8h–20h, segunda a sexta) e login da Comunidade Inter;
- criar a integração, com permissão **somente `extrato.read`** (não marcar pagamento/Pix);
- baixar certificado e chave, converter `.pfx` para PEM, `chmod 600`, caminhos no WSL e nomes
  das variáveis do `.env` (sem valor);
- rodar `scripts/teste_inter.py` e ler cada etapa: TLS, token, saldo, extrato; tabela de erros
  comuns (401, 403, 405 sem credencial, timeout, certificado inválido);
- o que **não** colar em chat/documento (G13);
- checklist final com caixas, incluindo "registrar a data do primeiro extrato" e "rodar a P2-3".
- Deixar explícito que os três caminhos do script vieram da doc pública e **não** foram
  exercitados; o script é o diagnóstico, não uma promessa.

**Não faça:** editar código, script, `.env.example` ou docs existentes; inventar endpoint;
escrever valor de segredo; prometer que o sandbox devolve dado real.

**Aceite:** um dono que nunca abriu o portal consegue seguir a página de cima a baixo e sabe
exatamente o que fazer quando cada etapa falhar.

---

## T5 — Acessibilidade e teclado nas telas

**Objetivo:** fechar o que a conferência visual de 375px (P4-4) não cobriu: foco de teclado,
leitor de tela e associação de erro ao campo. O alvo de toque já foi resolvido no P4-5.

**Contexto:** `templates/base.html`, `templates/login.html`, `templates/lancamentos.html`,
`templates/previstos.html`, `templates/relatorio.html`, `templates/inicio.html`,
`financas/static/financas/app.css`, `docs-dev/rodada-2026-11-05/s2-p4-4.md` e
`04-decisao-d4-p2-8-importacao.md` (só para não quebrar os rótulos novos).

**Entregáveis:**
1. Correções confirmadas nos templates/CSS:
   - `aria-current="page"` no link ativo da navegação;
   - erro de formulário associado ao campo (`id` no `<p class="erro">`, `aria-describedby` e
     `aria-invalid` no input), com `role="alert"` no erro;
   - `role="status"` na lista de mensagens;
   - `:focus-visible` visível para links, botões e campos (inclusive no botão escuro);
   - qualquer rótulo/associação que o teste de teclado revelar.
2. `financas/test_acessibilidade.py` (novo): link ativo com `aria-current` e só ele; POST
   inválido devolve `aria-invalid="true"` e `aria-describedby` apontando para o erro.
3. Verificação a 375px e 360px com o script CDP da rodada anterior, no banco descartável:
   sem rolagem horizontal, alvos ≥44px, foco visível. Se o `/tmp/gestao-visual/db.sqlite3`
   estiver sem a migration 0003, rodar `migrate --settings config.settings_visual` (é o banco
   descartável, não o real).
4. `s5-acessibilidade.md` com antes/depois e o que não foi possível verificar.

**Não faça:** mexer em views/models/settings/`tests.py`; editar ou remover
`config/settings_visual.py` (é o descartável do P4-6); tocar no banco real; trocar o desenho
visual por conta própria (G19).

**Aceite:** testes verdes; navegação por Tab mostra foco em todos os controles; erro de campo
anunciado e ligado ao input; tela continua sem estouro a 375/360.

---

## Fechamento da rodada (coordenador)

- Cada sessão entrega seu `sN-*.md`; ninguém edita `PROGRESS.md`, `PENDENCIAS.md` ou o painel.
- O coordenador roda a suíte final, consolida o rastro (G5/G6/G14), confere a matriz de
  arquivos e leva o diff para o pombal/commit.
- O que não fechar vira item no `PENDENCIAS.md`, com dono explícito.
