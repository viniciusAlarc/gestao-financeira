# gestao-financeira — Progresso

> Memória oficial do projeto (guardrail G5). Toda mudança de código entra aqui, na mesma
> resposta que a produziu. Mais recente no topo.

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
