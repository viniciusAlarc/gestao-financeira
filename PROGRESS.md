# gestao-financeira — Progresso

> Memória oficial do projeto (guardrail G5). Toda mudança de código entra aqui, na mesma
> resposta que a produziu. Mais recente no topo.

## 2026-11-01 — Modelo de dado e linha de base de testes

**O que mudou:** D2, D3 e D5 fechadas como propostas no plano, e o modelo da fase 1 escrito e aplicado.
Conta com `saldo` calculado por soma de movimentos, `Categoria` única por nome e tipo, `Movimento` com
valor positivo e sinal no `tipo`, e `Previsto` com a regra de que "pago" exige movimento. A suíte saiu
do zero para 8 testes.
**Arquivos:** `financas/models.py` (4 modelos), `financas/admin.py` (admin como tela provisória, com
`criado_por` vindo da sessão), `financas/migrations/0001_initial.py`, `financas/tests.py` (8 testes),
`PENDENCIAS.md` (D2, D3 e D5 fechadas; P3-4 aberto para o superusuário), `AGENTS.md` (estado e regra
de testes).
**Testes:** `.venv/Scripts/python manage.py test` → 8 testes, **OK**. `manage.py check` sem problemas.
`migrate` aplicou `financas.0001_initial` e as 4 tabelas existem no banco.
**Aberto:** criar o superusuário (P3-4) e a tela inicial (fase 2).

## 2026-11-01 — Esqueleto do Django rodando

**O que mudou:** D1 fechado em Django. Projeto `config` e app `financas` criados na raiz, SQLite com
as migrations do Django aplicadas, admin disponível. O modelo de dado segue vazio de propósito: ele
depende de D2, D3 e D5. Também entrou o `docs-dev/guias/OPERACAO.md` (G14), que passou a fazer sentido
porque agora existe servidor para subir.
**Arquivos:** `manage.py`, `config/settings.py` (segredo lido do `.env` ou de `.django-secret`, nunca
do código; `pt-br`, `America/Sao_Paulo`, login obrigatório), `config/urls.py`, `financas/`,
`requirements.txt` (`django~=5.2`, instalado 5.2.18), `.gitignore` (`.django-secret`),
`docs-dev/guias/OPERACAO.md`, `AGENTS.md` (stack e como rodar), `PENDENCIAS.md` (P2-4 fechado,
estado do sistema atualizado).
**Testes:** `manage.py check` sem nenhum problema; `manage.py migrate` aplicou 17 migrations do
Django. Não existe suíte própria ainda, e nenhum teste foi escrito nesta entrega.
**Aberto:** modelo de dado (D2, D3, D5), segundo login (D5) e a primeira tela.

## 2026-11-01 — Plano de desenvolvimento da v1

**O que mudou:** o projeto deixou de ter só uma fase de integração e passou a ter um plano de produto.
A decisão importante é de ordem: **o Inter saiu do caminho crítico**. O app nasce com lançamento
manual e a integração entra como fase 7, alimentando dados, não bloqueando o resto.
**Arquivos:** `docs-dev/a-codar/01-plano-desenvolvimento.md` (novo, 8 fases com verificação por fase,
modelo de dado proposto e as 4 decisões da fase 0), `docs-dev/painel.json` (plano novo), `PENDENCIAS.md`
(D1 e D2 com recomendação; itens do Inter marcados como pausados até a fase 7).
**Testes:** não se aplica, só documentação.
**Aberto:** as decisões da fase 0 (D1, D2, D3, D5), que travam o modelo de dados.

## 2026-11-01 — Investigação do portal Sandbox e do host da API

**O que mudou:** descoberto por que o `/sandbox` não abre e um problema maior, que travaria o teste de
qualquer jeito. Registrar não é corrigir: o script segue intocado, porque o host novo não foi conferido
na doc oficial (G1).
**Achados:** (1) o Sandbox só está disponível das 8h às 20h, de segunda a sexta, e exige login da
**Comunidade Inter**, não do Internet Banking PJ; (2) `cdpj-sandbox.partners.bancointer.com.br`, que o
script usa, **não resolve em DNS**; `cdpj-sandbox.partners.uatinter.co` resolve.
**Arquivos:** `PENDENCIAS.md` (P2-1 reescrito, P2-7 criado). Nenhum código alterado.
**Testes:** `nslookup`/`Resolve-DnsName` nos dois hosts do sandbox e no de produção; leitura das páginas
oficiais `/sandbox`, `/docs/sandbox/sobre-este-portal` e `/docs/sandbox/como-testar-aplicacao`.
**Aberto:** P2-7, confirmar o host na página Referências e só então corrigir `BASE_URLS`.

## 2026-11-01 — Decisão: Zed no Windows para projetos pessoais

**O que mudou:** fechada a dúvida de ambiente, e ela não é divergência. O WSL2 (Ubuntu 24.04)
existe para os projetos da CNR e para o Claude Code; os projetos pessoais, incluindo este, rodam
no Windows pelo Zed, com `.venv` local. O item P3-4 saiu do `PENDENCIAS.md`.
**Arquivos:** `AGENTS.md` (seção de ambiente reescrita como decisão), `PENDENCIAS.md` (P3-4 fechado).
**Testes:** não se aplica, mudança de documentação.
**Aberto:** nada novo.

## 2026-11-01 — Controle de contexto no padrão da casa

**O que mudou:** o projeto passou a ter rastro, não só um briefing: instruções do repositório,
memória, rastreador único de pendências e o painel de fases. O `BRIEFING.md` deixou a raiz e virou
`docs-dev/a-codar/briefing-descoberta.md`, que é o lugar de decisão fechada e ainda não codada (G7).
**Arquivos:** `AGENTS.md` (novo, instruções do projeto e resumo dos guardrails que incidem aqui),
`PROGRESS.md` (novo), `PENDENCIAS.md` (novo, D1–D6 e os bloqueios da fase 1), `docs-dev/painel.json`
(novo, fase 1 sem nenhuma etapa concluída), `docs-dev/a-codar/briefing-descoberta.md` (movido de
`BRIEFING.md` com `git mv`, sem perda de conteúdo além do cabeçalho, que aponta para os novos donos
do estado).
**Testes:** nenhum código executado; mudança só de documentação.
**Aberto:** `docs-dev/guias/OPERACAO.md` espera existir back ou front para subir (P4-1);
auditor de referências G12/G16 ainda não instalado (P4-2).

## 2026-11-01 — Sessão anterior: repositório, ambiente e teste de conexão

**O que mudou:** repositório privado criado e publicado; ambiente Python montado no projeto; script
de diagnóstico da API do Inter escrito. Nenhum código de aplicação ainda, e o script **nunca rodou**.
**Arquivos:** `.gitignore` (bloqueia `.env`, `*.pem`, `*.pfx`, `*.p12`, `*.key`, `certs/`, `secrets/`),
`.gitattributes` (LF), `requirements.txt` (`requests`, `python-dotenv`), `.env.example` (formato das
variáveis, sem valor), `scripts/teste_inter.py` (mTLS → token → saldo → extrato dos últimos 30 dias,
não grava nada em disco).
**Testes:** nada rodado. Falta o certificado, que só o dono baixa.
**Aberto:** ver `PENDENCIAS.md`, itens P2-1 a P2-3.

## 2026-11-01 — Descoberta do produto

**O que mudou:** fechado o entendimento de produto, com as decisões D1–D6 ainda em aberto.
**Arquivos:** `docs-dev/a-codar/briefing-descoberta.md` (registro completo da conversa, perguntas e
respostas originais).
**Testes:** não se aplica.
**Aberto:** D1–D6, registradas em `PENDENCIAS.md`.
