# s3 · Segurança e privacidade antes do uso real (T3)

> Rodada 2026-11-05-b · sessão t3 · executado em 2026-11-08.
> Objetivo do briefing: revisar o app como ele vai ser usado (duas pessoas, rede de casa, HTTP),
> provar por teste o que é crítico e recomendar o resto — **sem corrigir código de app**.

## O que foi feito

1. Li `AGENTS.md`, `PENDENCIAS.md`, `PROGRESS.md`, `config/settings.py`, `config/urls.py`,
   `financas/urls.py`, `financas/views.py`, `financas/admin.py`, `financas/forms.py`,
   `financas/models.py`, os 6 templates e `config/settings_visual.py`.
2. Criei `financas/test_seguranca.py` com **22 testes** de regressão para: login obrigatório,
   escrita só por POST com CSRF, admin só para staff, Host fora de `ALLOWED_HOSTS` e o baseline
   de cabeçalhos/cookies que o Django já entrega.
3. Varri os arquivos versionados atrás de segredo (`git ls-files`, `git grep` de chave privada,
   `.env.example`) e medi as permissões de `.django-secret` e `db.sqlite3` com `stat`.
4. Não editei código de app, não subi servidor, não abri `db.sqlite3` nem `.env` (regra 2 do
   `AGENTS.md`), não instalei nada, não mexi em banco.

**Arquivos desta sessão:**

- `financas/test_seguranca.py` (novo, 22 testes)
- `docs-dev/rodada-2026-11-05-b/s3-seguranca.md` (este relatório)

## Testes antes e depois

| Momento | Comando | Resultado |
| --- | --- | --- |
| Linha de base (início da sessão) | `.venv/bin/python manage.py test` | **68, OK** |
| Depois, suíte completa | `.venv/bin/python manage.py test` | **125, OK** |
| Só o arquivo novo | `.venv/bin/python manage.py test financas.test_seguranca` | **22, OK** |

O total de 125 inclui os testes novos das outras sessões da rodada (T1 importador 26, T5
acessibilidade 6, T2 celular 3), que apareceram no diretório enquanto eu trabalhava (G21): por
isso o número não é 68 + 22. Nenhuma falha, nenhuma falha pré-existente. Os 22 testes meus
passam também isolados, sem depender de arquivo de outra sessão.

## O que os 22 testes provam

| Garantia | Teste | Evidência no código |
| --- | --- | --- |
| `inicio`, `lancamentos`, `previstos`, `relatorio` exigem login | `LoginObrigatorioTests` | `financas/views.py:26,73,129,213` |
| `pagar_previsto` exige login e POST anônimo **não paga** | idem | `financas/views.py:171-173` |
| `login` é a única porta pública | idem | `financas/urls.py:20-26` |
| Erro de login não revela se o usuário existe | idem | `templates/login.html:10` |
| `pagar_previsto` recusa GET (405) e POST sem CSRF (403), sem efeito | `EscritaSoPorPostComCsrfTests` | `views.py:172`; `templates/previstos.html:43-44` |
| `pagar_previsto` com token da sessão paga exatamente 1 vez | idem | `views.py:192-204` |
| `logout` recusa GET (405) e POST sem CSRF (403), mantendo a sessão | idem | `financas/urls.py:27`; `templates/base.html:24-25` |
| `logout` com token encerra a sessão | idem | idem |
| O login também exige CSRF (anti "login CSRF") | idem | `templates/login.html:8` |
| Admin recusa anônimo e usuário comum (sem staff) e aceita staff | `AdminExigeStaffTests` | `config/urls.py:8` (admin padrão) |
| Host fora de `ALLOWED_HOSTS` recebe 400; permitido abre | `HostForaDaListaTests` | `config/settings.py:35-39` |
| `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` | `CabecalhosECookiesTests` | `settings.py:54-62` + defaults do Django 5.2 |
| Cookie de sessão `HttpOnly` + `SameSite=Lax`; cookie CSRF `SameSite=Lax` | idem | idem |

Os testes usam dado inventado e o banco que o Django cria para a suíte; o `db.sqlite3` real não
foi aberto. `pagar_previsto` e `logout` foram exercitados com `Client(enforce_csrf_checks=True)`,
porque o cliente de teste normal ignora CSRF e esconderia a falta do token.

## Achados

Classificação: **crítico** (expõe dado ou bloqueia e exige parar), **alto** (corrigir antes do uso
real), **médio** (decisão consciente ou prazo curto), **baixo** (melhoria barata).

**Crítico: nenhum.** Não há segredo em arquivo versionado, nenhuma tela de dado aberta sem login e
nenhuma escrita por GET. Nada aqui justificou parar a rodada, como o briefing previa para achado
crítico.

| # | Nível | Achado | Bloqueia o uso real? |
| --- | --- | --- | --- |
| A1 | **Alto** | `DEBUG` vale `1` quando não há `.env`, e é assim que o app vai subir para o celular | **Sim, e é barato: uma linha no `.env`** |
| A2 | **Médio** | HTTP puro na rede de casa: sessão e senha sem camada de TLS | Não dentro de casa; **sim se sair da rede** |
| M1 | **Médio** | `config/settings_visual.py` está **versionado** (o `PENDENCIAS` diz que não) e loga todo visitante como usuário automático | Não; remoção já é o P4-6 |
| M2 | **Médio** | Sem limite de tentativas de login (nem no `/admin/`) | Não; fica para depois, por decisão do briefing |
| B1 | **Baixo** | `.django-secret` e `db.sqlite3` com permissão `644` | Não |
| B2 | **Baixo** | O `.env` futuro (`INTER_CLIENT_SECRET`) nasce `644` pelo mesmo motivo | Não; resolver junto com a P2-2 |
| B3 | **Baixo** | Sessão dura 2 semanas por padrão e não expira ao fechar o navegador | Não |

### A1 · `DEBUG` ligado por padrão (Alto) — **o único que bloqueia**

**Onde:** `config/settings.py:33` — `DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"`.
**Evidência:** hoje não existe `.env` (confirmado por `test -e .env`), então `DEBUG=True` em toda
execução. O comando documentado em `docs-dev/guias/OPERACAO.md:10` é
`runserver 0.0.0.0:8000`, e o passo a passo do celular (T2/`P2-9`) escreve no `.env` **só**
`DJANGO_ALLOWED_HOSTS`, sem `DJANGO_DEBUG`. Com `DEBUG=True`, qualquer erro devolve a página
técnica do Django: código-fonte das views, configuração da instalação, SQL executado e variáveis
locais do quadro onde estourou. O próprio 400 de `DisallowedHost` (provado em
`test_host_desconhecido_recebe_400`) é uma página técnica quando `DEBUG=True` — ou seja, quem
abrir o IP da casa antes de o `ALLOWED_HOSTS` estar certo vê essa página. O valor de segredo em si
não aparece: o Django filtra `SECRET_KEY`/`PASSWORD` na listagem de settings, e o `.env` do Inter
não entra em `settings` (só em `os.environ`). O risco é revelar código e configuração, não a chave.
**Recomendação:** antes da semana de uso real (P3-9), acrescentar `DJANGO_DEBUG=0` ao `.env` —
e incluir essa linha no script/checklist do T2, senão o passo a passo "funciona" com a exposição
ligada. Atenção operacional: com `DEBUG=False`, o `runserver` **para de servir o CSS, os ícones e o
manifest** (não há WhiteNoise). Até a fase 8 (HTTPS/serviço de estático), subir com
`runserver 0.0.0.0:8000 --insecure`, que serve o estático sem ligar o modo de depuração. Trocar
por WhiteNoise é dependência nova e decisão do dono (G1/G20).

### A2 · HTTP puro na rede de casa (Médio; sobe a Alto fora de casa)

**Onde:** `config/settings.py` não define nenhuma `SECURE_*`, `SESSION_COOKIE_SECURE` nem
`CSRF_COOKIE_SECURE`; os padrões do Django 5.2 são `False`
(`django/conf/global_settings.py:490,574,666,670`). O formulário de login posta usuário e senha
por HTTP (`templates/login.html:7-17`) e o cookie de sessão não tem `Secure` (os testes provam
`HttpOnly` e `SameSite=Lax`, que ajudam, mas não criptografam o tráfego).
**Evidência:** `docs-dev/guias/OPERACAO.md:10` sobe em HTTP; HTTPS é a fase 8; o dossiê D6
(`docs-dev/a-codar/02-decisao-d6-onde-roda.md`) recomenda rede de casa na v1 e Tailscale para sair.
Em WPA2, quem tem a senha do Wi-Fi consegue capturar o tráfego da rede — o caso realista é
"dispositivo de visitante ou da casa comprometido", não a internet.
**Recomendação:** manter a v1 **dentro da rede de casa**, sem port-forward no roteador (nada de
expor a 8000 na internet). Para usar fora de casa, Tailscale antes de qualquer coisa — é a
recomendação do D6. Quando o HTTPS chegar (fase 8), ligar `SECURE_SSL_REDIRECT`,
`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` e HSTS juntos, senão o login quebra.
**Se o app sair da rede de casa hoje, este item vira Alto** e bloqueia.

### M1 · `config/settings_visual.py` versionado, com login automático (Médio)

**Onde:** `config/settings_visual.py:35-36` (`DEBUG = True`, `ALLOWED_HOSTS = ["*"]`) e
`:155-166` (`VisualFerramentaMiddleware` troca `request.user` pelo usuário `visual` em **toda**
requisição). O banco é descartável em `/tmp` (`:25-33`), então não há dado real nele.
**Evidência:** o arquivo **está versionado** — `git log -- config/settings_visual.py` aponta o
commit `bdb90b6` (2026-11-05), e `git ls-files` o lista. O `PENDENCIAS.md:51` (P4-6) diz
"(novo, não versionado)": essa parte está errada hoje (G12). Ele **não** é o settings padrão
(`config/settings.py` não o referencia), então o risco exige alguém subir de propósito com
`--settings config.settings_visual`; nesse caso, qualquer aparelho da rede entra sem senha. Nada
aqui justifica urgência, mas é uma armadilha que o commit tornou permanente.
**Recomendação:** fechar o P4-6 removendo de verdade — `git rm config/settings_visual.py` mais
apagar o arquivo e `/tmp/gestao-visual/`, com o "pode" do dono (G3). Se a T5 ainda precisar dele
até o fim da rodada, remover logo depois e corrigir o texto do P4-6 para "versionado, a remover".
Se ficar, um aviso no topo do arquivo ("não subir em `0.0.0.0`") é o mínimo.

### M2 · Sem limite de tentativas de login (Médio; fica como futuro)

**Onde:** `financas/urls.py:20-26` usa o `LoginView` padrão; o `/admin/` (`config/urls.py:8`) usa
o login do admin. Não há throttle, captcha nem bloqueio por tentativa. Os validadores de senha
(`config/settings.py:94-101`) só agem na **escolha** da senha, não em tentativa online.
**Evidência:** `requirements.txt` só tem Django; nenhum app de rate limit instalado. O Django não
tem limite embutido.
**Recomendação:** registrar como futuro (o briefing pede para não implementar agora).
Candidato natural na fase 8/9: `django-axes` (dependência nova, decisão do dono) ou middleware
próprio com contador por IP/usuário. Até lá, as duas contas com senha forte; o `/admin/` compartilha
a mesma superfície de força bruta.

### B1 · `.django-secret` e `db.sqlite3` com permissão 644 (Baixo)

**Onde:** `config/settings.py:25-28` cria o `.django-secret` com a umask padrão, sem `0o600`.
**Evidência medida:** `stat -c '%a %n'` → `644 .django-secret` e `644 db.sqlite3`. Leitura por
qualquer conta/processo do WSL (e por processo do Windows via `\\wsl.localhost`). Em máquina de um
usuário só, o ganho é marginal, mas o custo também é.
**Recomendação:** `chmod 600 .django-secret db.sqlite3` (ação do dono, G3); e, na geração do
arquivo, abrir com `os.open(caminho, os.O_CREAT | os.O_WRONLY, 0o600)` para não voltar a 644.

### B2 · `.env` futuro com o segredo do Inter nasce 644 (Baixo)

**Onde:** ainda não existe `.env`; `.env.example` mostra `INTER_CLIENT_SECRET`
(`.env.example:8`). Quando a P2-2 preencher, o arquivo nasce com a umask padrão.
**Recomendação:** `chmod 600 .env` na mesma hora em que o segredo entra (G13), e incluir isso no
passo a passo do Inter (T4/P2-2). Vale também para o arquivo de certificado/chave, que já está
documentado para ficar fora do repositório.

### B3 · Sessão de 2 semanas (Baixo, informativo)

**Onde:** `config/settings.py` não define `SESSION_COOKIE_AGE`; o padrão do Django 5.2 é
14 dias (`django/conf/global_settings.py:486`), e o cookie não expira ao fechar o navegador.
**Leitura:** para dois celulares pessoais, é conforto, não defeito. Se um aparelho for
compartilhado, vale `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` ou idade menor. Não bloqueia nada.

## G9 · Autorização por escopo: por que não há achado

Este app **não tem recurso por usuário**: a decisão D5 é conta conjunta, e as duas contas veem
tudo de propósito. Não existe, portanto, o caso "id de outro dono" que o G9 trata. O único campo
por pessoa é `Movimento.criado_por`, e ele é gravado da sessão, nunca aceito como campo de input:
`financas/views.py:93` e `:200` (`criado_por=request.user`) e `financas/admin.py:48-54`
(`criado_por` fora do formulário, preenchido por `save_model`). A única rota que recebe `pk` é
`pagar_previsto`, e ela busca por `pk` + `tipo=despesa` (`financas/views.py:181-186`); qualquer
previsto pode ser pago por qualquer uma das duas contas — é a regra do produto, não vazamento.
Fica registrado aqui para o checklist do G11 não ficar em aberto por engano.

## Segredos em arquivo versionado (varredura)

| Verificação | Evidência | Resultado |
| --- | --- | --- |
| Nome de segredo/banco em `git ls-files` | `git ls-files \| grep -Ei '\.env$\|secret\|sqlite\|\.pem$\|\.key$'` | só `.env.example` (modelo sem valor) |
| Chave privada em arquivo versionado | `git grep -lE 'BEGIN (RSA \|EC \|OPENSSH )?PRIVATE KEY'` | nenhuma |
| `.env.example` preenchido | `grep -nE '^[A-Z_]+=.+'` | só `INTER_AMBIENTE=sandbox` (modo, não segredo) |
| `.env`, `.django-secret`, `db.sqlite3` fora do git | `git check-ignore -v` | os três ignorados por `.gitignore:2,35,32` |
| Nenhum segredo copiado para este relatório | revisão do texto | nenhum valor; só nomes de variável |

## Bloqueia o uso real × pode esperar

**Bloqueia (resolver antes da semana de uso, P3-9):**

1. **A1 — `DJANGO_DEBUG=0` no `.env`**, junto com o `DJANGO_ALLOWED_HOSTS` que a T2 já escreve.
   Sem isso, o app sobe na rede com a página técnica do Django ligada. Subir com `--insecure`
   para o estático continuar aparecendo é a contrapartida operacional.
2. **A2 — limite de exposição:** só rede de casa, sem port-forward. Se a decisão for usar fora de
   casa, Tailscale (D6) antes de qualquer coisa.

**Pode esperar:**

- **M1** remoção do `settings_visual.py` — já é o P4-6, fazer no fechamento da rodada.
- **M2** limite de tentativas de login — futuro, dependência a decidir com o dono.
- **B1/B2** permissões 600 — no mesmo dia em que o `.env` for criado (P2-2/T2), é um comando.
- **B3** duração da sessão — só se o celular for compartilhado.

## O que ficou de fora e por quê

- **`manage.py check --deploy`**: não está na lista de comandos liberados da rodada e não rodei.
  As mesmas configurações que ele denunciaria (`DEBUG`, `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS) foram conferidas por leitura no
  `settings.py` e pelos testes de cabeçalho/cookie.
- **HTTPS de verdade**: não existe ainda (fase 8). Testar TLS seria testar o que não foi construído.
- **Força bruta de login**: não implementada por decisão do briefing ("registrar como futuro").
  O achado descreve o buraco; não há teste de regressão porque não há proteção para regredir.
- **Runtime do `settings_visual.py`**: só a T5 pode subir servidor nesta rodada; aqui foi leitura
  de código e do histórico do git.
- **`db.sqlite3` e `.env`**: não abertos (regra 2 do `AGENTS.md` / G13); as permissões foram
  medidas com `stat`, sem ler conteúdo.
- **Teste cross-escopo do G9**: não se aplica — não há recurso por usuário (D5), explicado acima.
- **Código de app**: intocado, como o briefing pediu. Toda recomendação acima é para o dono
  decidir e para uma sessão de correção depois da rodada.

## Observação de convivência (G21)

A T5 editou `templates/base.html`, `login.html`, `lancamentos.html` e `previstos.html` durante a
minha sessão. As referências de linha acima já são do estado **depois** dessas edições; os
`{% csrf_token %}` e os formulários POST que os meus testes exercitam continuam nos mesmos lugares
conceituais (`base.html:24-25`, `previstos.html:43-44`, `login.html:7-8`). A suíte completa passou
depois das edições dela (125 testes, OK), então não houve quebra de contrato entre as sessões.
