# Operação local — subir, derrubar e reiniciar

> Como o app sobe nesta máquina: WSL (Ubuntu 24.04), só ele (decisão de 2026-11-01). A tabela abaixo é lida
> pela Fábrica de agentes (G14, `~/Documents/IA/guardrails-ia/operacao.md`); o resto é para gente.

## Subir (lido pela Fábrica de agentes)

| Lado  | Pasta | Comando                                                 | Porta |
| ----- | ----- | ------------------------------------------------------- | ----- |
| back  | `.`   | `.venv/bin/python manage.py runserver 0.0.0.0:8000` | 8000  |
| back (produção) | `~/gestao-financeira` no PythonAnywhere | aba **Web** → **Reload** | 443 |
| front |       |                                                         |       |

O `0.0.0.0` é o que permite abrir no celular pela rede de casa. Sem ele o servidor só responde em
`localhost` e o celular não alcança.

## Produção (PythonAnywhere)

O app publicado roda no PythonAnywhere, plano gratuito, em `https://viniciusapps.pythonanywhere.com`.
O passo a passo completo (conta, WSGI, estáticos, banco e backup) está em
`docs-dev/a-codar/03-deploy-pythonanywhere.md`. Para publicar uma atualização: `git pull`,
`collectstatic` quando mudar estático, `migrate` só com o "pode" do dono e **Reload** na aba Web.

## O que digitar no celular

Escutar em `0.0.0.0` não basta: no celular, `localhost` é o próprio celular. O endereço é
`http://<ip-da-máquina>:8000`.

1. Descobrir o IP da máquina, no WSL: `hostname -I` (usar o primeiro valor IPv4). Esta máquina está
   em **rede espelhada** (`networkingMode=mirrored` no `.wslconfig` do Windows), então esse IP é o
   mesmo que o Windows usa na rede de casa; não precisa de encaminhamento de porta.
2. Esse IP precisa estar em `DJANGO_ALLOWED_HOSTS`, senão o Django responde `DisallowedHost`. O
   script da seção "Preparar o `.env` pelo celular" faz isso e mostra o IP: rode
   `scripts/preparar_acesso_celular.sh --aplicar`. Manualmente, é acrescentar ao `.env` a linha
   `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.x.x`, trocando o exemplo pelo IP do passo 1.
3. Subir com o comando da tabela e abrir no celular o endereço do passo 1 com a porta 8000.
4. Celular e máquina na mesma rede Wi-Fi.

Se o celular não abrir com o `ALLOWED_HOSTS` certo, o suspeito é o **firewall do Windows**, que fica
na frente do que roda no WSL: na primeira vez que o servidor sobe, o Windows pergunta se permite o
Python na rede privada (responder que sim). Se a pergunta não apareceu, conferir a permissão é ação
do dono no Windows.

## Preparar o `.env` pelo celular (um comando)

O `.env` é **do dono**: fica fora do git (`.gitignore`) e é onde os segredos da Pluggy vão morar na
fase 7. O script abaixo só cuida da linha do celular: **não cria nem imprime segredo** e não mostra
nenhum outro valor do arquivo (G13).

Na raiz do projeto:

```bash
scripts/preparar_acesso_celular.sh            # só mostra o IP e o bloco para colar
scripts/preparar_acesso_celular.sh --aplicar  # grava ou atualiza a linha no .env
```

O que ele faz:

1. descobre o primeiro IPv4 com `hostname -I` e mostra o endereço `http://<ip>:8000`;
2. mostra o bloco `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,<ip>`;
3. avisa se o `.env` ainda não existe;
4. com `--aplicar`, acrescenta a linha sem apagar as outras variáveis. Se o `.env` não existir, cria
   um novo só com essa linha (sem segredo, permissão 600). Rodar de novo não duplica nada: se o IP
   já está lá, ele não mexe no arquivo.

Depois de aplicar, **reinicie o servidor** (`Ctrl+C` e subir de novo): o Django lê o `.env` no start.

> Em rede espelhada o `hostname -I` também lista as pontes de container do Docker (`172.x`). O script
> usa o primeiro IPv4 e mostra os outros; se o celular não abrir, confira se o IP gravado é o da rede
> de casa (o mesmo que o Windows usa) e, se preciso, edite a linha do `.env` à mão.

## Checklist de 5 minutos no primeiro celular

1. Na raiz do projeto: `scripts/preparar_acesso_celular.sh --aplicar`.
2. Subir o servidor com o comando da tabela do topo (`0.0.0.0:8000`).
3. No Windows, responder **sim** ao aviso do firewall para o Python na rede privada (só na primeira
   vez que o servidor sobe).
4. No celular, na mesma rede Wi-Fi, abrir `http://<ip>:8000` (o script imprime o endereço).
5. Entrar com uma das duas contas e conferir a tela **Início** com saldo, gasto do mês e previsto em
   aberto.
6. Opcional: instalar o PWA (seção abaixo).

Se algo falhar no caminho, a tabela "Quando alguma coisa não sobe" tem os sintomas.

## Pré-requisitos

- `.venv` na raiz com `requirements.txt` instalado:
  `pip3 --python .venv/bin/python install -r requirements.txt` (o `.venv` não tem pip próprio).
- Para o app não é obrigatório nenhum segredo: a `SECRET_KEY` sai do `.env` (`DJANGO_SECRET_KEY`) ou
  do arquivo `.django-secret`, gerado no primeiro start e ignorado pelo git. Nenhum valor de segredo
  aparece neste documento (G13).
- `ALLOWED_HOSTS` vem de `DJANGO_ALLOWED_HOSTS` no `.env`; sem ela vale `localhost,127.0.0.1`.
  Para o celular alcançar, o script e o passo a passo estão em "Preparar o `.env` pelo celular" e
  "Checklist de 5 minutos no primeiro celular".
- `.env` com as variáveis da Pluggy só é necessário na fase 7.

## Instalar o PWA no celular

O app está preparado com `manifest.webmanifest` e ícones em `financas/static/financas/`.

- Android/Chrome: menu de três pontos → "Instalar aplicativo" (ou "Adicionar à tela inicial").
- iPhone/Safari: Compartilhar → "Adicionar à Tela de Início".

Em rede local por HTTP, alguns navegadores só oferecem a instalação com HTTPS. Se o celular não
mostrar a opção, isso é limitação do navegador/rede, não defeito do app. Em produção
(PythonAnywhere) o endereço é HTTPS e a instalação funciona.

## Ver o que está rodando

```bash
ss -ltnp | grep :8000
```

## Desligar e subir de novo

`Ctrl+C` no terminal do servidor e rodar o comando da tabela outra vez.

## Quando alguma coisa não sobe

| Sintoma                              | Causa provável                  | O que resolve                                                        |
| ------------------------------------ | ------------------------------- | -------------------------------------------------------------------- |
| `DisallowedHost` ao abrir pelo celular | IP da máquina fora do `ALLOWED_HOSTS` (ou `.env` ausente) | `scripts/preparar_acesso_celular.sh --aplicar` e reiniciar o servidor |
| `no such table`                      | migrations não aplicadas        | `.venv/bin/python manage.py migrate`                             |
| Login em laço, sem entrar            | nenhum usuário criado           | `.venv/bin/python manage.py createsuperuser`                     |
| `You appear not to have the 'sqlite3' program installed` no `dbshell` | binário `sqlite3` ausente no WSL | usar o driver Python: `.venv/bin/python -c "import sqlite3, pathlib; print(pathlib.Path('db.sqlite3').stat().st_size)"` — ou qualquer leitura via ORM. Não instalar o binário sem o ok do dono |
