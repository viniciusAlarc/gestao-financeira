# Deploy no PythonAnywhere (plano gratuito) — MVP a dois

> **Decisão de 2026-11-17 (D6 revista pela P3-3).** O app sai do WSL e passa a ter endereço
> público, para as duas pessoas usarem de qualquer lugar. Custo recorrente: R$ 0.
> O passo a passo é deste documento; o que mudou fica no `PROGRESS.md` e o que está aberto no
> `PENDENCIAS.md`.

## O que a decisão entrega

- Endereço: `https://viniciusapps.pythonanywhere.com` (o username vira o endereço).
- O app fica no ar sem depender do PC de casa.
- HTTPS e instalação do PWA no celular.
- O banco `db.sqlite3` mora no disco da conta, que é persistente.

## Limitações aceitas

| Limitação | Efeito | O que fazer |
|---|---|---|
| Web app expira a cada mês (contas novas) | O app fica fora do ar até renovar | O PythonAnywhere avisa por e-mail; renovar é um clique na aba **Web** |
| 100 s de CPU por dia | Para duas pessoas, sobra; tarefa pesada não roda | Nada no MVP |
| 512 MB de disco | Suficiente para o projeto e o banco | Conferir o uso na aba **Files** |
| Sem SSH de entrada | Deploy e manutenção pelo console do navegador | Usar a aba **Consoles** |
| Chamadas externas só para a allowlist | `api.pluggy.ai` está na lista; outras APIs podem não estar | A Pluggy pode rodar no free; outras integrações dependem da lista |
| Sem backup automático | O banco é cópia única no servidor | Baixar o `db.sqlite3` toda semana |

## Pré-requisitos (o dono faz)

1. Criar a conta em <https://www.pythonanywhere.com/registration/register/beginner/>.
   O username vira a URL; não use nome completo nem dado pessoal. Sugestão: `financas-<apelido>`.
2. Confirmar o e-mail (é por ele que chega o aviso de expiração).
3. Decidir o banco (opção A ou B, abaixo), que é ação G3.

## Passo 1 — código no servidor

Aba **Consoles** → **Bash**. O console abre em `/home/viniciusapps`.

```bash
git clone https://github.com/viniciusAlarc/gestao-financeira.git
cd gestao-financeira
```

O repositório é público, então não pede credencial. Se o clone falhar por acesso externo, o plano B
é gerar um zip do projeto no PC e subir pela aba **Files**.

## Passo 2 — virtualenv e dependências

```bash
mkvirtualenv --python=/usr/bin/python3.12 financas-venv
pip install -r requirements.txt
```

Se `python3.12` não existir, rodar `ls /usr/bin/python3*` e escolher 3.11 ou 3.10 (o Django 5.2
exige 3.10+). A versão escolhida aqui tem de ser a mesma do web app, no passo 5.

## Passo 3 — `.env` do servidor

Aba **Files**, criar `/home/viniciusapps/gestao-financeira/.env` com exatamente:

```dotenv
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=viniciusapps.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://viniciusapps.pythonanywhere.com
```

**Não** colocar `DJANGO_SECRET_KEY`: no primeiro comando o app gera o `.django-secret` na pasta do
projeto, que já está no `.gitignore`. Nenhum segredo passa pelo terminal (G13).

## Passo 4 — banco e estáticos

No console, na pasta do projeto:

```bash
workon financas-venv
```

### Banco: escolher uma opção (G3)

> **Escolha do dono em 2026-11-17: opção A (banco novo).** O banco do PC não é tocado; o servidor
> começa vazio e recebe a conta padrão, as categorias e a segunda conta pelo admin.

**A) Começar limpo** (sem os lançamentos atuais):

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Depois, criar a segunda conta pelo admin (`/admin/`) ou pelo shell.

**B) Subir os dados atuais** (o histórico que já existe no PC):

1. No PC, parar o servidor local (`Ctrl+C`).
2. Na aba **Files** do PythonAnywhere, subir o `db.sqlite3` do projeto para
   `/home/viniciusapps/gestao-financeira/`, substituindo o arquivo vazio.
3. No console, **não rodar `migrate`**: o banco real está nas migrations 0001 a 0005, e a 0006
   (novo valor `pluggy` em `Movimento.origem`) ainda espera o "pode" do P2-16.
4. Conferir e coletar os estáticos:

```bash
python manage.py showmigrations
python manage.py collectstatic --noinput
```

5. Senha da segunda conta (a conta já existe no banco):

```bash
python manage.py changepassword NOME_DA_CONTA
```

O comando pede a senha sem exibi-la; ela não vai para documento nem para o histórico do shell (G13).

## Passo 5 — web app

Aba **Web** → **Add a new web app** → **Manual Configuration** → Python 3.12 (a mesma versão do
passo 2).

Preencher:

| Campo | Valor |
|---|---|
| Virtualenv | `/home/viniciusapps/.virtualenvs/financas-venv` |
| Source code | `/home/viniciusapps/gestao-financeira` |
| Working directory | `/home/viniciusapps/gestao-financeira` |

Na seção **Code**, abrir o arquivo WSGI (algo como
`/var/www/viniciusapps_pythonanywhere_com_wsgi.py`) e deixar assim:

```python
import os
import sys

path = "/home/viniciusapps/gestao-financeira"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Na seção **Static files**:

| Campo | Valor |
|---|---|
| URL | `/static/` |
| Directory | `/home/viniciusapps/gestao-financeira/staticfiles` |

Na seção **Security**, ligar **Force HTTPS**. Quem redireciona é o proxy do PythonAnywhere, inclusive
os arquivos estáticos; o Django já está preparado para reconhecer o HTTPS
(`SECURE_PROXY_SSL_HEADER` no `settings.py`).

Clicar em **Reload**.

## Passo 6 — verificação

1. Abrir `https://viniciusapps.pythonanywhere.com` no celular: a tela de login deve aparecer com o CSS.
2. Entrar com a conta do dono e conferir a tela **Início** (saldo, gasto do mês, previsto em aberto).
3. Entrar com a segunda conta, lançar um gasto de teste e conferir que a autoria aparece.
4. Instalar o PWA: Android/Chrome no menu de três pontos; iPhone/Safari em Compartilhar →
   Adicionar à Tela de Início.
5. Se algo falhar, abrir a aba **Web** → **Error log**. As causas mais comuns são caminho errado no
   WSGI, `.env` ausente e `ALLOWED_HOSTS` sem o subdomínio.

## Atualizações (daqui para frente)

No console:

```bash
cd ~/gestao-financeira
git pull
pip install -r requirements.txt   # só quando mudar dependência
python manage.py migrate          # só com o "pode" do dono quando houver migration nova
python manage.py collectstatic --noinput
```

E **Reload** na aba Web. O PythonAnywhere não recarrega sozinho.

## Importação automática (GitHub Actions)

O endpoint `POST /tarefas/importar-pluggy/` dispara o `importar_pluggy` para a conta de
`IMPORT_CONTA`, limitado aos últimos 7 dias (a Pluggy relê 4 a 7 dias; o `id_externo` evita
duplicata). Ele exige o header `X-Import-Token` igual a `IMPORT_TOKEN` do `.env`. O workflow
`.github/workflows/importar-pluggy.yml` roda duas vezes por dia (10:00 e 19:00 UTC, 07:00 e 16:00
em Brasília) e pode ser disparado à mão em **Actions → Importar Pluggy → Run workflow**.

- No `.env` do servidor: `IMPORT_TOKEN` (valor aleatório, não versionado) e `IMPORT_CONTA` (nome
  exato da conta no app).
- No GitHub: **Settings → Secrets and variables → Actions** → novo secret `IMPORT_TOKEN` com o
  mesmo valor.
- O MeuPluggy atualiza a cada 24h; rodar mais de uma vez por dia não traz dados novos.

O endpoint responde `403` sem o token e `500` se a conta não estiver configurada. O comando é
idempotente: os movimentos já importados são pulados.

## Backup (obrigatório a partir de agora)

O banco passa a ser cópia única no servidor. Uma vez por semana:

1. aba **Files** → `/home/viniciusapps/gestao-financeira/db.sqlite3` → **Download**;
2. guardar no PC com a data no nome.

Sem cópia baixada, a perda do disco da conta é a perda do histórico. O plano grátis não tem tarefa
agendada; a rotina é manual.

## O que este documento não decide

- A saída do plano grátis: só quando a Pluggy (fase 7) for usada no servidor ou quando a renovação
  mensal incomodar. As alternativas estão no dossiê D6 (`02-decisao-d6-onde-roda.md`).

## O que ainda depende do dono

- criar a segunda conta de login no admin, se ainda não existir (P3-9);
- renovar o web app mensalmente (P3-10);
- baixar o backup semanalmente (P3-12).
