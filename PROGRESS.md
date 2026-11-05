# gestao-financeira — Progresso

> Memória oficial do projeto (guardrail G5). Toda mudança de código entra aqui, na mesma
> resposta que a produziu. Mais recente no topo.

## 2026-11-05 — P2-10 fechado: migration 0003 aplicada e categorias padrão criadas

**O que mudou:** o dono autorizou a aplicação da migration `0003` no banco real. Ela adicionou
`Categoria.entra_no_gasto` e `Movimento.id_externo`, mais a restrição única
`(conta, id_externo)`. Depois, foram criadas as categorias padrão da importação: "Não
categorizado" (despesa), "Não categorizado" (receita) e "Investimento" (despesa, com
`entra_no_gasto=False`). Nenhum dado existente foi alterado: os movimentos antigos ficaram com
`id_externo` vazio e as categorias antigas com `entra_no_gasto=True`.
**Comando:** `.venv/bin/python manage.py migrate` → `financas.0003... OK`. As categorias foram
criadas por ORM (`get_or_create`), com o resultado `criada=True` nas três.
**Verificação:** `showmigrations` mostra `0003` como aplicada; `manage.py check` sem problemas;
`.venv/bin/python manage.py test` → **68 testes, OK**. O app no banco real voltou a responder com
o código novo.
**Arquivos:** nenhum de código nesta entrada; `PENDENCIAS.md` (P2-10 fechado) e
`docs-dev/rodada-2026-11-05-b/00-briefing.md` (T0 marcado como concluído).
**Aberto:** P2-1/P2-2 (integração e certificado), P2-3 (diagnóstico no sandbox). A rodada
paralela de 5 sessões parte de 68 testes verdes.

## 2026-11-05 — D4 e P2-8 fechados; modelo pronto para a importação do Inter

**Decisões do dono:** **D4** — a v1 lê só a conta **PJ (MEI)**: saldo e extrato. PF, cartão,
boleto de terceiro, posição de investimentos, pagamentos/Pix e Open Finance ficam fora, porque a
API direta não alcança. **P2-8** — importação na conta existente `69 450 604 Vinicius Di Franca
Alarc`; data `dataTransacao` (reserva `dataInclusao`); categoria "Não categorizado" e classificação
manual depois; `idTransacao` em `Movimento.id_externo` como chave antiduplicidade; autoria do
usuário técnico `Inter`; investimento, estorno e cashback importados com categoria própria, e
"Investimento" fora do gasto; a primeira importação começa na data da execução, para não duplicar
os Pix manuais que já estão na conta. Documento completo em
`docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md`.
**O que mudou no código:** `Movimento` ganhou `id_externo` (nulo no lançamento manual) com
restrição única `(conta, id_externo)`; `Categoria` ganhou `entra_no_gasto` (padrão `True`). A tela
inicial e o relatório passaram a filtrar `categoria__entra_no_gasto=True`; o rodapé do relatório
virou "Total de gastos do mês", porque "despesas" ficaria impreciso com investimento fora. O admin
expõe a flag e esconde o id externo do formulário.
**Arquivos:** `financas/models.py`, `financas/views.py`, `financas/admin.py`,
`templates/relatorio.html`, `financas/tests.py` (+6 testes),
`financas/migrations/0003_categoria_entra_no_gasto_movimento_id_externo_and_more.py`,
`PENDENCIAS.md`, `docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md`.
**Testes:** `.venv/bin/python manage.py test` → **68 testes, OK** (62 + 6). `manage.py check` sem
problemas; `makemigrations --check` sem drift.
**Não aplicado:** a migration `0003` está escrita e testada no banco de teste, mas não roda no
banco real sem o "pode" do dono (G3) — item P2-10. As categorias padrão também dependem disso.
**Aberto:** P2-1/P2-2 (criar integração e certificado), P2-3 (diagnóstico no sandbox), P2-10
(aplicar migration e criar categorias). O importador só começa depois desses.

## 2026-11-05 — P4-5 fechado: alvos de toque de 44px

**O que mudou:** os controles que a conferência visual a 375px (s2 do P4-4) apontou como pequenos
passaram ao alvo de 44×44: `.botao-primario` ganhou `min-height` (o "Paguei" compacto ia a 36px de
altura); os links da navegação e o "Sair" viraram `inline-flex` com `min-width`/`min-height` de
44px. O espaçamento entre os links da navegação caiu de 1rem para 0.5rem para os cinco alvos
continuarem numa linha só a 375px e a 360px. Nenhum template mudou; a aparência do texto é a mesma,
só a área clicável cresceu.
**Arquivos:** `financas/static/financas/app.css`.
**Testes:** `.venv/bin/python manage.py test` → 62 testes, **OK** antes e depois. `manage.py check`
sem problemas.
**Verificação:** medição por CDP com viewport real de 375px e cache do navegador desabilitado, nas
quatro telas autenticadas (`/`, `/lancamentos/`, `/previstos/`, `/relatorio/`). Antes, `/previstos/`
tinha 12 alvos pequenos: "Início" 35×28, "Lançamentos" 84×28, "Previstos" 57×30, "Relatório" 57×28,
"Sair" 24×20 e seis "Paguei" 67×36. Depois: **zero** alvos abaixo de 44×44 nas quatro telas, sem
rolagem horizontal (`scrollWidth = 375`) e sem elemento passando da borda. A 360px, também zero.
Evidência em `/tmp/gestao-visual/depois-{inicio,lancamentos,previstos,relatorio}.png` (fora do git).
**Fechado:** P4-5. A remoção do descartável da conferência continua em P4-6, aguardando autorização.

## 2026-11-05 — Rodada paralela (5 sessões)

Cinco itens do `PENDENCIAS.md` trabalhados em sessões paralelas no mesmo repositório, sem commit.
Cada sessão deixou o rastro em `docs-dev/rodada-2026-11-05/`; esta entrada consolida.

**s1 · P4-2 (auditor de referências).** `scripts/auditar-referencias.py` passou a auditar este
repositório: `RAIZES` com os 12 diretórios reais, `docs-dev/guias/*.md` acrescentado ao `ALVOS_DOC`
e correção do falso positivo em que um caminho relativo está ancorado numa base `~/...` citada na
mesma frase (os 3 caminhos do `AGENTS.md` e 3 do briefing). Modo padrão: exit 0, limpo. `--tudo`:
1 achado informativo (`regras/templates/` no briefing, linha 70), menção histórica que a regex não
pega — reportado, não corrigido. `indice_simbolos()` segue vazio (só indexa Java/TS; indexar Python
de `financas/` é melhoria futura). **Arquivos:** `scripts/auditar-referencias.py`. **Testes:** 62 → 62, OK.

**s2 · P4-4 (conferência visual a 375px).** `/previstos/` e `/relatorio/` conferidas a 375px com
SQLite descartável em `/tmp` e dado inventado (o `db.sqlite3` real não foi aberto): `scrollWidth =
375` nas duas, nenhum elemento passando da borda, contraste do valor de despesa 6,5:1 — **ok**, sem
defeito. Nenhum template/CSS alterado. **Arquivos:** `config/settings_visual.py` (novo, descartável,
pode ser removido), screenshots em `/tmp/gestao-visual/`. **Testes:** 62 → 62, OK. **Achado:** alvos
de toque abaixo de 44px ("Paguei" 67×36, nav 28–30px, "Sair" 24×20) — virou P4-5.

**s3 · P3-9 (segundo usuário e PWA, parte técnica).** Entrega HTTP do PWA conferida com o cliente de
teste: `/login/` 200, `/` anônimo 302, manifest 200 `application/manifest+json` com `display:
standalone`, `start_url` e `scope` `/`, ícones 200 medidos em 192×192 e 512×512. Segunda conta criada
com autorização do dono na sessão: usuário `Kethlen` (id 2, ativo, sem admin), **senha ainda não
definida** — ninguém entra até o dono definir. `OPERACAO.md` ganhou o que faltava para o celular
alcançar: IP em vez de localhost, `DJANGO_ALLOWED_HOSTS` no `.env` (hoje não existe `.env`, então o
celular leva `DisallowedHost`) e o firewall do Windows. Checklist de uma semana pronto. **Arquivos:**
`docs-dev/guias/OPERACAO.md`. **Testes:** 62 → 62, OK.

**s4 · P3-3 (dossiê da decisão D6).** Dossiê com 5 opções de exposição (rede de casa, Tailscale,
Cloudflare Tunnel, ngrok, VPS), com os três números do G20 e links datados; recomendação: rede de
casa na v1, Tailscale se quiser sair de casa agora, Cloudflare como plano B, VPS só se o PC não
puder ficar ligado. Nada criado. **Arquivo:** `docs-dev/a-codar/02-decisao-d6-onde-roda.md`.

**s5 · P2-6 (dossiê da decisão D4).** Delimitação com 17 fontes oficiais datadas: a API Banking é
exclusiva de PJ; cobre saldo, extrato (90 dias por consulta), extrato enriquecido, PDF e pagamentos;
ficam de fora conta PF, cartão de crédito, boleto de outra titularidade, investimentos e contas a
pagar; Open Finance não é caminho para app pessoal. A importação preenche `data`, `valor`, `tipo`,
`descricao` e `origem=inter`, mas não `categoria` (obrigatória), `criado_por` nem chave
antiduplicidade; o modelo não tem campo para id externo (próxima rodada). 10 perguntas do dono e 6
pontos só confirmáveis no sandbox. **Arquivo:** `docs-dev/a-codar/03-decisao-d4-escopo-inter.md`.

**Ficou aberto:** P4-4 aguarda o "conferi" do dono; P3-9 aguarda senha da `Kethlen`, `.env` com
`DJANGO_ALLOWED_HOSTS` (P2-9), instalação no celular e uma semana de uso; P3-3 e P2-6 aguardam
decisão do dono com os dossiês na mesa; novos itens P4-5 (alvos de toque) e P4-6 (remover o
descartável). Nada foi commitado.

## 2026-11-03 — Fase 7 iniciada: host do sandbox corrigido

**O que mudou:** `scripts/teste_inter.py` passou a usar o host oficial do sandbox,
`https://cdpj-sandbox.partners.uatinter.co`, conferido no portal do desenvolvedor do Inter.
O `.env.example` agora mostra exemplos de caminho absoluto do WSL para certificado e chave.
**Arquivos:** `scripts/teste_inter.py` (host e comentários), `.env.example`.
**Testes:** o script compila; os hosts de sandbox e produção respondem TLS (GET no token dá 405,
como esperado sem credencial). O script roda e para pedindo as variáveis do `.env`, que não existe.
**Aberto:** criar/preencher `.env` e certificado (P2-1/P2-2), confirmar se a conta é PJ e o
mapeamento da importação (P2-6/P2-8), rodar o diagnóstico (P2-3) e só depois desenhar a importação.

## 2026-11-03 — Fase 6 implementada: segundo login, logout e PWA

**Decisão do dono:** o app é do casal, com uma conta conjunta. As duas contas de login veem todos
os dados; o lançamento registra quem lançou em `criado_por`.
**O que mudou:** logout na navegação (POST), PWA com `manifest.webmanifest`, ícones 192 e 512,
`display: standalone`, `theme-color` e metatags de iOS. Nenhuma mudança de modelo: `criado_por` já
era gravado no lançamento rápido e no pagamento de previsto.
**Arquivos:** `financas/urls.py` (rota `logout`), `templates/base.html` (manifest, metatags,
logout), `financas/static/financas/manifest.webmanifest` (novo), `financas/static/financas/icone-192.png`
e `icone-512.png` (novos), `financas/static/financas/app.css`, `financas/tests.py` (+7 testes).
**Testes:** `.venv/bin/python manage.py test` → 62 testes, **OK**; `manage.py check` sem problemas;
`makemigrations --check` sem mudanças.
**Validação:** testes cobrem logout, autoria do lançamento e do pagamento, as duas contas vendo os
mesmos dados, manifesto com campos/ícones e as metatags no HTML. Smoke test confirmou manifesto e
ícones servidos com o tipo correto.
**Aberto:** P3-9, a verificação de uso real (criar o segundo usuário, instalar o PWA no celular e
usar uma semana). Service worker/offline não entrou: o plano pedia manifest, ícone e `display`.
Em Rede local por HTTP, a instalação pode depender do navegador; HTTPS é assunto da fase 8.

## 2026-11-03 — Fase 5 implementada e validada: relatório por categoria

**O que mudou:** tela nova `/relatorio/` e item "Relatório" na navegação. O relatório mostra as
despesas do mês corrente agrupadas por categoria, com total, percentual sobre o total de despesas
e ordem decrescente. O rodapé repete o total de despesas do mês. Receitas e meses anteriores ficam
fora. Ficou de fora, por não estar no plano: seletor de outro mês.
**Arquivos:** `financas/views.py` (view `relatorio`), `financas/urls.py`, `templates/relatorio.html`
(novo), `templates/base.html` (nav), `financas/templatetags/financas_extra.py` (filtro
`porcentagem`), `financas/static/financas/app.css`, `financas/tests.py` (+6 testes).
**Testes:** `.venv/bin/python manage.py test` → 55 testes, **OK**; `manage.py check` sem problemas;
`makemigrations --check` sem mudanças.
**Validação:** a soma dos totais por categoria é comparada com o total de despesas do mês em teste,
e o relatório exclui receitas e despesas de outro mês. Percentuais são calculados sobre o total de
despesas; com arredondamento de uma casa, a soma dos percentuais pode não fechar 100,0% em casos de
terços, mas a soma dos valores fecha exatamente.
**Aberto:** fase 6 (segundo login e PWA). Conferência visual de `/previstos/` e `/relatorio/` a
375px fica em P4-4, sem bloquear a fase.

## 2026-11-03 — Fase 4 implementada e validada: gastos previstos

**O que mudou:** tela nova `/previstos/` e item "Previstos" na navegação. O formulário cria um
gasto previsto com descrição, vencimento, valor e categoria de despesa; a conta é a padrão e o
tipo é sempre despesa. A lista mostra os previstos abertos por vencimento, cada um com o botão
"Paguei". Ao pagar, o sistema cria exatamente um movimento com a data real de hoje, na conta do
próprio previsto, e marca o previsto como pago. Não há desfazer na v1 (decisão do dono).
**Arquivos:** `financas/forms.py` (`PrevistoForm`), `financas/views.py` (`previstos` e
`pagar_previsto`), `financas/urls.py`, `templates/previstos.html` (novo), `templates/base.html`
(nav), `financas/static/financas/app.css`, `financas/tests.py` (+16 testes), `docs-dev/painel.json`,
`RETRABALHO.md` (novo).
**Testes:** `.venv/bin/python manage.py test` → 49 testes, **OK**; `manage.py check` sem problemas.
**Validação:** os dois critérios do plano são cobertos por teste: previsto pago sai do total em
aberto e entra no gasto do mês; previsto futuro aberto não entra no gasto do mês corrente.
**Correção na revisão:** o "Paguei" não deve depender da conta padrão atual. A primeira versão
filtrava o previsto pela conta padrão, então mudar a conta padrão deixava previstos antigos com
o botão da lista retornando 404. Agora o pagamento usa a conta do próprio previsto e funciona
mesmo sem conta padrão marcada.
**Aberto:** fase 5 (relatório por categoria). A conferência visual da tela nova a 375px fica como
P4-4, sem bloquear a fase.

## 2026-11-03 — Fase 3 implementada: lançamento rápido e lista do mês

**O que mudou:** tela nova `/lancamentos/` com formulário de valor + categoria e lista do mês
corrente agrupada por dia, mais navegação entre Início e Lançamentos. Decisões do dia: conta
padrão nova em `Conta` (só uma pode ser padrão) e total exibido = despesas do mês. O tipo do
movimento vem da categoria escolhida; o valor aceita vírgula ("30,50") e ponto ("30.50").
**Arquivos:** `financas/models.py` (campo `padrao` + constraint), `financas/migrations/0002_...`,
`financas/forms.py` (novo), `financas/views.py` (view `lancamentos`), `financas/urls.py`,
`templates/base.html` (navegação e mensagens), `templates/lancamentos.html` (novo),
`financas/static/financas/app.css`, `financas/admin.py`, `financas/tests.py` (+14 testes).
**Testes:** `.venv/bin/python manage.py test` → 33 testes, **OK**. `manage.py check` sem problemas.
Migração `financas.0002` aplicada no banco local com o "pode" do dono em 2026-11-03, dentro de
transação, sem erro.
**Verificação (P3-8):** em 2026-11-03 o dono marcou a conta padrão no admin e lançou 5 gastos reais
do dia pela tela nova, sem admin; a lista agrupada por dia e o total de despesas bateram. Fase 3
fechada. **Aberto:** fase 4 (gastos previstos com o botão "paguei").

## 2026-11-03 — Fase 2 verificada visualmente e fechada (P3-4 e P3-6)

**O que mudou:** o dono criou o superusuário (P3-4) e fez a conferência visual da tela inicial a
375px de largura, com dados de exemplo lançados pelo admin (P3-6). Os três números bateram com o
esperado: saldo, gasto do mês e previsto em aberto. A fase 2 fecha sem mudança de código.
**Arquivos:** `PENDENCIAS.md` (P3-4 e P3-6 removidos; estado da suíte corrigido para 19 testes),
`docs-dev/painel.json` (fase "Tela inicial" → feito), `AGENTS.md` (estado atual e linha de base).
**Testes:** `.venv/bin/python manage.py test` → 19 testes, **OK**; `manage.py check` sem problemas;
nenhuma migration pendente (rodados na revisão de hoje, antes da conferência visual).
**Aberto:** fase 3 (lançamento rápido). Decisões de conta padrão e local do formulário ainda em aberto.

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
