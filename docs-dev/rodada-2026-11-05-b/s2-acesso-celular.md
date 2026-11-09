# T2 — Acesso pelo celular e operação (P2-9)

> Rodada 2026-11-05-b, sessão t2. `PROGRESS.md`, `PENDENCIAS.md` e `docs-dev/painel.json` não foram
> editados: a consolidação é do coordenador. Nada foi commitado.

## O que foi feito

1. **`scripts/preparar_acesso_celular.sh` (novo).** Descobre o primeiro IPv4 com `hostname -I`
   (ignora IPv6, loopback e `0.0.0.0`), mostra o endereço `http://<ip>:8000` e o bloco
   `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,<ip>`. Sem argumento só imprime. Com `--aplicar`,
   cria o `.env` (quando não existe, só com essa linha e permissão 600) ou atualiza a linha
   existente preservando as outras variáveis, sem duplicar host e sem repetir a linha. Não lê nem
   imprime nenhum valor do `.env` além da própria linha de hosts: `INTER_CLIENT_SECRET` e afins
   nunca aparecem na saída (G13).
2. **`financas/test_acesso_celular.py` (novo).** Três testes com `override_settings(ALLOWED_HOSTS=...)`
   e cliente de teste: login responde **200** pelo IP permitido (com porta), **400** por host fora
   da lista e **400** pelo IP quando ele não está no `ALLOWED_HOSTS` — que é exatamente o efeito do
   P2-9 antes do script.
3. **`docs-dev/guias/OPERACAO.md`.** Seções novas "Preparar o `.env` pelo celular (um comando)" e
   "Checklist de 5 minutos no primeiro celular"; o passo 2 de "O que digitar no celular", os
   pré-requisitos e a linha de `DisallowedHost` da tabela de erros agora apontam para o script. A
   observação de que o `.env` é do dono e fica fora do git está na seção nova (G13).
4. **`config/settings.py` não mudou.** Não há lacuna: `ALLOWED_HOSTS` já vem de
   `DJANGO_ALLOWED_HOSTS` com padrão `localhost,127.0.0.1`, e o POST do celular em HTTP passa na
   checagem de origem do CSRF por ser mesma origem (`http://<ip>:8000`). Mudar seria escopo
   inventado.

## Arquivos

| Arquivo | Situação |
| --- | --- |
| `scripts/preparar_acesso_celular.sh` | novo, executável |
| `financas/test_acesso_celular.py` | novo |
| `docs-dev/guias/OPERACAO.md` | editado (seções do celular) |
| `docs-dev/rodada-2026-11-05-b/s2-acesso-celular.md` | novo (este relatório) |

`config/settings.py` ficou intocado, como o briefing previa.

## Testes

| Momento | Comando | Resultado |
| --- | --- | --- |
| Linha de base, no início da sessão | `.venv/bin/python manage.py test` | **68 testes, OK** |
| Só o arquivo novo | `.venv/bin/python manage.py test financas.test_acesso_celular -v 2` | **3 testes, OK** |
| Suíte completa no fim | `.venv/bin/python manage.py test` | **125 testes, OK** |

O salto de 68 para 125 **não é meu**: as sessões paralelas já deixaram na árvore
`financas/test_importacao.py` (T1), `financas/test_seguranca.py` (T3) e
`financas/test_acessibilidade.py` (T5). Meus 3 testes são os de `test_acesso_celular.py`. A suíte
inteira estava verde nos dois momentos; nenhuma falha nova.

## Evidência do script

Testado num diretório temporário, fora do repositório (`/tmp/t2-celular-teste/`): o script foi
copiado para `/tmp/t2-celular-teste/scripts/` e o `.env` de teste tinha dados inventados, inclusive
um `INTER_CLIENT_SECRET` falso. Resultado: **29 conferências, 29 ok**. O que foi coberto:

1. sem `.env` e sem argumento: imprime o bloco exato com o IP e o endereço do celular, avisa que o
   `.env` não existe e **não cria** o arquivo;
2. sem `.env` e com `--aplicar`: cria o `.env`, permissão 600, uma única linha de configuração;
3. `.env` com outras variáveis: a saída não imprime o segredo nem os outros valores; depois de
   `--aplicar`, a variável e o segredo continuam intactos e a linha do celular entra;
4. `--aplicar` de novo: continua uma única linha e a saída diz "Nada a fazer" (idempotente);
5. linha existente `localhost,127.0.0.1`: ganha o IP sem repetir `localhost`, outras linhas
   preservadas;
6. linha existente com outro host (`meu-pc.local`): host preservado, IP acrescentado;
7. arquivo sem newline no fim: não cola uma linha na outra;
8. `--help` sai com 0; argumento desconhecido sai com 2;
9. sem IPv4 (um `hostname` falso que só devolve IPv6): erro claro ("não encontrei IPv4"), sai com
   1 e não toca no `.env`.

O harness pegou um defeito na primeira versão: quando o `.env` não tinha a linha, o valor saía só
com o IP, sem `localhost,127.0.0.1`. Corrigido antes da entrega; os 29 voltaram verdes.

## O que o dono ainda precisa rodar (P2-9 continua 👤)

1. Na raiz do projeto: `scripts/preparar_acesso_celular.sh --aplicar`.
2. Subir: `.venv/bin/python manage.py runserver 0.0.0.0:8000` (ou pelo comando de sempre).
3. Responder **sim** ao aviso do firewall do Windows, se aparecer.
4. No celular, na mesma rede Wi-Fi, abrir `http://<ip>:8000` (o script imprime o endereço) e
   entrar com uma das duas contas.
5. Opcional: instalar o PWA (`OPERACAO.md`).

O checklist completo está em `docs-dev/guias/OPERACAO.md`, seção "Checklist de 5 minutos no primeiro
celular".

## Ficou de fora, e por quê

- **Não criei nem alterei o `.env` real e não rodei `--aplicar` nele.** O `.env` é do dono (G13) e
  o briefing proíbe escrevê-lo sem ele; o script existe para o dono rodar.
- **Não subi servidor** (o briefing manda usar o cliente de teste) e não testei em celular real,
  firewall ou rede de casa: são ações do dono, e o resultado depende da rede dele.
- **Não editei `.env.example`** (fora da minha lista de arquivos). Fica a sugestão para o
  coordenador: acrescentar `DJANGO_ALLOWED_HOSTS` a ele, para o modelo também mostrar a variável.
- **Rede espelhada com Docker:** o `hostname -I` desta máquina devolve, depois do IP da rede de casa,
  os endereços das pontes do Docker (`172.x`). O script usa o primeiro IPv4 e lista os outros na
  saída; se algum dia o primeiro for uma ponte, é só ajustar a linha do `.env` à mão — a observação
  está no `OPERACAO.md`.
- **Não mexi em `templates/`, CSS, models, `financas/tests.py`** (proibido pelo briefing).
