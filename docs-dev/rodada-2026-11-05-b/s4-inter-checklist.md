# s4 · T4 — Checklist operacional do Inter (P2-1/P2-2/P2-3)

> Sessão t4 da rodada 2026-11-05-b. **Não** editou `PROGRESS.md`, `PENDENCIAS.md` nem o painel
> (consolidação é do coordenador). Nenhum commit.

## 1. O que foi feito

Criei `docs-dev/guias/INTER-PASSO-A-PASSO.md`, um passo a passo para o dono executar sozinho, de
cima a baixo, a criação da integração no **sandbox** e o diagnóstico da fase 7. Ele cobre:

- janela do portal (8h–20h, segunda a sexta) e login com a conta da comunidade (Comunidade Inter),
  deixando claro que **não** é o login do Internet Banking PJ;
- criação da integração no sandbox, com os rótulos oficiais ("Nova integração", "Acessar", "Criar
  integração", "Minhas Integrações", "Detalhar integração"), status "Novo" → "Ativo" e a validade
  de **30 dias** do certificado de sandbox;
- download de chave, certificado e credenciais, com o aviso de que as credenciais nascem no
  download e, em produção, aparecem **uma única vez**;
- armazenamento fora do repositório (`segredos/inter` na home), `chmod 700`/`600`, conversão
  `.pfx` → PEM com `openssl`, conversão DER → PEM se preciso, e a conferência de que o par
  certificado/chave bate (hash da chave pública);
- preenchimento do `.env` com os **nomes** das seis variáveis e nenhum valor de segredo;
- leitura das etapas do `scripts/teste_inter.py` (TLS, token, saldo, extrato), o que cada uma prova,
  como é a saída de sucesso e o que o sucesso **não** prova;
- tabela de erros com 401, 403, 405 sem credencial, 404, 400, 429, 503, timeout/rede e falha de
  certificado, cada um com causa provável e ação;
- o que nunca colar em chat/documento (G13) e a regra de que a saída do script contém dado
  financeiro;
- checklist final com caixas, incluindo **"registrar a data do primeiro extrato"** e **"rodar a
  P2-3"**.

Deixei explícito, no corpo e na seção de fontes, que os três caminhos usados pelo script
(`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`) vieram da documentação pública e
**nunca foram exercitados com credencial**. O texto diz que o script é o diagnóstico, não uma
promessa, e que o sandbox devolve **dado fictício**.

## 2. Achado que muda uma linha do briefing

O briefing pedia "criar a integração, com permissão **somente `extrato.read`** (não marcar
pagamento/Pix)". A documentação oficial do sandbox diz, literalmente:

> "Para o ambiente Sandbox não será necessário selecionar os escopos desejados, a integração será
> criada com os escopos listados."
> (`https://developers.inter.co/docs/sandbox/como-criar-uma-aplicacao`, consultada em 2026-11-08)

Ou seja: **no sandbox não existe a tela de escolha de escopo**. O guia não inventa uma caixa que não
existe: ele diz isso com a citação e coloca a regra de menor privilégio onde ela realmente decide,
na **integração de produção** (marcar somente `extrato.read`, nada de pagamento nem webhook). O app
já pede só `extrato.read` no token, e a referência do Banking confirma esse escopo para `/saldo`,
`/extrato` e `/extrato/completo`.

## 3. Fontes consultadas (todas em 2026-11-08)

Só documentação pública, sem login e sem credencial:

- `https://developers.inter.co/docs/sandbox` (janela 8h–20h, segunda a sexta; dados fictícios);
- `https://developers.inter.co/docs/sandbox/como-criar-uma-aplicacao` (passos do sandbox, escopos
  não selecionáveis, status "Novo"/"Ativo", certificado de 30 dias);
- `https://developers.inter.co/docs/sandbox/sobre-este-portal` (homologação com dados fictícios);
- `https://developers.inter.co/docs/introducao/como-criar-uma-aplicacao` (fluxo de produção,
  escolha de permissões, análise, credenciais exibidas uma vez);
- `https://developers.inter.co/docs/introducao/como-renovar-uma-integracao` (1 ano em produção,
  `.crt`/`.key`, renovação);
- `https://developers.inter.co/references/token` (`client_credentials`, `scope`, token de 60 min,
  respostas 200/400/403/404/503);
- `https://developers.inter.co/redocusaurus/swagger-banking-yaml.yaml` (escopo `extrato.read` em
  `/saldo` e `/extrato`; respostas 400/403/404/503; corpos de erro).

Do repositório: `scripts/teste_inter.py` (etapas e mensagens literais), `.env.example` (nomes das
variáveis e caminhos sugeridos), `PROGRESS.md` (registro de 2026-11-01 sobre a Comunidade Inter e de
2026-11-03 sobre o host e o 405 sem credencial), `03-decisao-d4-escopo-inter.md`,
`04-decisao-d4-p2-8-importacao.md` e `docs-dev/guias/OPERACAO.md` (lido, não editado).

## 4. Arquivos

| Arquivo | Situação |
| --- | --- |
| `docs-dev/guias/INTER-PASSO-A-PASSO.md` | **novo**, 443 linhas |
| `docs-dev/rodada-2026-11-05-b/s4-inter-checklist.md` | **novo**, este relatório |

Nenhum código, script, `.env.example` ou documento existente foi editado. `OPERACAO.md` foi só
lido; ele aparece modificado no `git status` por trabalho da T2, não por mim.

## 5. Testes

| Momento | Comando | Resultado |
| --- | --- | --- |
| Antes de começar | `.venv/bin/python manage.py test` | **68 testes, OK** |
| Depois de escrever | `.venv/bin/python manage.py test` | **125 testes, OK** |

A subida de 68 para 125 **não** é minha: a árvore recebeu os testes das outras sessões da rodada
(`financas/test_importacao.py`, `test_acesso_celular.py`, `test_seguranca.py`,
`test_acessibilidade.py`). Nenhum teste novo meu, porque a entrega é só documentação. A suíte está
verde nos dois momentos.

## 6. Evidência de que o guia segue o código, não a memória

- As mensagens literais do guia foram copiadas de `scripts/teste_inter.py`: `Faltam variáveis no
  .env: ...`, `INTER_AMBIENTE precisa ser 'sandbox' ou 'producao'.`, `INTER_CERT_PATH aponta para um
  arquivo que não existe: ...`, `Token recusado (HTTP ...)`, `Saldo falhou (HTTP ...)`, `Extrato
  falhou (HTTP ...)`, `Falha de SSL/mTLS: ...`, `Falha de rede: ...`.
- As quatro variáveis obrigatórias e a quinta opcional batem com `.env.example` e com
  `carregar_configuracao()`.
- O valor do cabeçalho `x-conta-corrente` só é enviado se `INTER_CONTA_CORRENTE` estiver preenchida,
  como o guia explica.
- Rodei a lógica do auditor de referências (`scripts/auditar-referencias.py`) sobre o guia novo, em
  memória: **zero achados** pelos critérios dele. Os caminhos `~/segredos/...` que ainda não existem
  foram escritos sem barra final e sem crase para não virarem falso positivo de "caminho morto".
- Nenhum valor de segredo aparece no guia: as variáveis estão com valor vazio e os caminhos são os
  do `.env.example`. O número da conta real não foi transcrito.

## 7. O que ficou de fora e por quê

1. **Executar o passo a passo.** Depende do login do dono no portal, dentro da janela 8h–20h. A
   sessão não tem credencial e não podia criar a integração. P2-1 e P2-2 continuam 👤.
2. **Rodar a P2-3 de verdade.** O guia ensina a rodar; a execução é do dono. Até lá, os três
   caminhos seguem **não exercitados** e o item continua 💻.
3. **Integração de produção.** Ficou só como seção de "depois do sandbox", com o caminho oficial e a
   regra de escopo. Criar integração de produção é ação irreversível do dono (G3) e não é o escopo
   desta tarefa.
4. **Formato exato do download do sandbox.** A doc diz "baixar a chave e o certificado", mas não
   fixa a extensão. O guia trata as duas formas (`.crt`/`.key` e `.pfx`) em vez de escolher uma e
   arriscar estar errado.
5. **Tela exata do portal.** O portal é uma SPA e a documentação descreve os passos em texto, não em
   imagem. O guia usa os rótulos oficiais e avisa que a posição pode mudar; se o portal mudar o
   texto, vale o portal.
