# gestao-financeira — Progresso

> Memória oficial do projeto (guardrail G5). Toda mudança de código entra aqui, na mesma
> resposta que a produziu. Mais recente no topo.

## 2026-11-02 — Banco local do WSL criado (P3-5 fechado)

**O que mudou:** com o "pode" do dono (G3), o `migrate` criou o `db.sqlite3` local e aplicou
as 18 migrations (17 do Django + `financas.0001_initial`), incluindo as 4 tabelas do app.
Descoberto no caminho: o binário `sqlite3` não existe no WSL, então `manage.py dbshell` falha;
o app não é afetado (o Django usa o driver Python embutido) e nada foi instalado.
**Arquivos:** `PENDENCIAS.md` (P3-5 removido, P3-6 atualizado),
`docs-dev/guias/OPERACAO.md` (nota sobre o `dbshell`; comando "ver o que está rodando"
ainda era o do Windows, `findstr` → `ss`).
**Testes:** não se aplica, só ação de banco autorizada.

## 2026-11-02 — Tela inicial (fase 2 do plano) com os três números

**O que mudou:** a raiz do site virou a tela inicial, protegida por login: saldo, gasto do mês
e previsto em aberto, mobile-first. Leituras fechadas nesta sessão (registradas para a fase 4
não chutar): saldo = saldos iniciais + receitas − despesas de **todas as contas** (regra do
plano); gasto do mês = despesas do mês corrente; previsto em aberto = **só despesas** abertas
(decisão do dono). Estilo com cor só no número (saldo verde quando positivo, vermelho quando
negativo; gasto em vermelho; previsto em cinza), decidido com o dono — o projeto não tem doc
de design (G19). Login usa o `LoginView` do Django com rótulos e erro em pt-BR fixos no
template, porque o WSL não tem o locale pt_BR instalado. Os nomes de URL ganharam namespace
`financas:` (settings atualizado). Ficou de fora o logout: não está na spec da fase e volta
na fase 6.
**Arquivos:** `financas/views.py` (view `inicio`), `financas/urls.py` (novo), `config/urls.py`
(include do app), `templates/base.html`, `templates/inicio.html`, `templates/login.html`,
`financas/static/financas/app.css`, `financas/templatetags/financas_extra.py` (filtro
`dinheiro`), `financas/tests.py` (+11 testes), `PENDENCIAS.md` (P3-6),
`docs-dev/painel.json` (fase em andamento).
**Testes:** `.venv/bin/python manage.py test` → 19 testes, **OK** (8 da linha de base + 11 novos).
**Aberto:** verificação visual da fase (P3-6), que depende do banco local (P3-5) e do
superusuário (P3-4).

## 2026-11-01 — Projeto passa a rodar só no WSL, pelo Dev Valley com o DeepSeek

**O que mudou:** o dono decidiu trazer o projeto para o WSL e codar pelo Dev Valley, com o DeepSeek
(perfil pessoal do Claude Code, para não usar a licença do trabalho). Revoga a decisão "Zed no Windows"
(entrada abaixo). Clonado em `~/Documents/Projetos-pessoais/gestao-financeira`; `.venv` de Linux criado
sem pip (o WSL não tem `python3-venv`; dependência entra com `pip3 --python .venv/bin/python`). Novo
`CLAUDE.md` que importa o `AGENTS.md`; auditor de referências instalado (`scripts/auditar-referencias.py`,
`.claude/auditoria-regras.txt`). Regra 2 ganhou: o assistente lê e escreve código, nunca dado real
(`db.sqlite3`, extrato, `.env`).
**Arquivos:** `AGENTS.md` (ambiente, comandos, regras 2 e 5, fonte das regras), `CLAUDE.md` (novo),
`docs-dev/guias/OPERACAO.md` (WSL e `.venv/bin/python`), `PENDENCIAS.md` (comando do P3-4),
`financas/tests.py` e `scripts/teste_inter.py` (comando no comentário).
**Testes:** `.venv/bin/python manage.py test` → 8 testes, **OK** (no WSL).
**Aberto:** o banco local do WSL não existe ainda (`migrate` espera o dono, G3); ajustar `ALVOS`/`RAIZES`
do auditor e rodá-lo.

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
