# Operação local — subir, derrubar e reiniciar

> Como o app sobe nesta máquina: WSL (Ubuntu 24.04), só ele (decisão de 2026-11-01). A tabela abaixo é lida
> pela Fábrica de agentes (G14, `~/Documents/IA/guardrails-ia/operacao.md`); o resto é para gente.

## Subir (lido pela Fábrica de agentes)

| Lado  | Pasta | Comando                                                 | Porta |
| ----- | ----- | ------------------------------------------------------- | ----- |
| back  | `.`   | `.venv/bin/python manage.py runserver 0.0.0.0:8000` | 8000  |
| front |       |                                                         |       |

O `0.0.0.0` é o que permite abrir no celular pela rede de casa. Sem ele o servidor só responde em
`localhost` e o celular não alcança.

## Pré-requisitos

- `.venv` na raiz com `requirements.txt` instalado:
  `pip3 --python .venv/bin/python install -r requirements.txt` (o `.venv` não tem pip próprio).
- Para o app não é obrigatório nenhum segredo: a `SECRET_KEY` sai do `.env` (`DJANGO_SECRET_KEY`) ou
  do arquivo `.django-secret`, gerado no primeiro start e ignorado pelo git. Nenhum valor de segredo
  aparece neste documento (G13).
- `ALLOWED_HOSTS` vem de `DJANGO_ALLOWED_HOSTS` no `.env`; sem ela vale `localhost,127.0.0.1`.
  Para abrir no celular, incluir o IP da máquina na rede: `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.x.x`.
- `.env` com as variáveis do Inter só é necessário na fase 7.

## Ver o que está rodando

```bash
ss -ltnp | grep :8000
```

## Desligar e subir de novo

`Ctrl+C` no terminal do servidor e rodar o comando da tabela outra vez.

## Quando alguma coisa não sobe

| Sintoma                              | Causa provável                  | O que resolve                                                        |
| ------------------------------------ | ------------------------------- | -------------------------------------------------------------------- |
| `DisallowedHost` ao abrir pelo celular | IP da máquina fora do `ALLOWED_HOSTS` | acrescentar o IP no `.env` e reiniciar                        |
| `no such table`                      | migrations não aplicadas        | `.venv/bin/python manage.py migrate`                             |
| Login em laço, sem entrar            | nenhum usuário criado           | `.venv/bin/python manage.py createsuperuser`                     |
| `You appear not to have the 'sqlite3' program installed` no `dbshell` | binário `sqlite3` ausente no WSL | usar o driver Python: `.venv/bin/python -c "import sqlite3, pathlib; print(pathlib.Path('db.sqlite3').stat().st_size)"` — ou qualquer leitura via ORM. Não instalar o binário sem o ok do dono |
