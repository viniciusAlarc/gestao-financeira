# Inter no sandbox: passo a passo do dono

> **Para quem é:** o dono do projeto, sozinho, sem ida e volta. Foi escrito para ser seguido de
> cima a baixo, na ordem, num dia útil dentro da janela do portal.
> **Escrito em:** 2026-11-08. **Não edita código, script nem `.env.example`:** só descreve o que já
> existe e o que o portal oficial diz.
> **O que fecha:** P2-1 (criar a integração e o certificado), P2-2 (converter para PEM e preencher o
> `.env`) e P2-3 (rodar o diagnóstico contra o sandbox).
> **Tempo:** cerca de 20 minutos no portal e 5 minutos no WSL, mais o tempo de espera da integração
> ficar "Ativo".

## 1. O que você vai fazer, em quatro passos

1. **Entrar no sandbox** do portal do desenvolvedor do Inter, dentro da janela de funcionamento.
2. **Criar uma integração** de teste e baixar dela o certificado, a chave e as credenciais.
3. **Guardar os arquivos fora do repositório**, converter para o formato que o projeto usa (PEM) e
   preencher o `.env` com os nomes das variáveis, nunca com valor escrito em papel.
4. **Rodar `scripts/teste_inter.py`** e ler as três etapas. Se as três passarem, a P2-3 está
   fechada e a fase 7 pode começar.

**Por que isso é feito antes do importador:** o importador precisa saber o que a API devolve de
verdade. Hoje só sabemos o que a documentação pública diz. O sandbox é o lugar de descobrir isso sem
tocar na conta real.

**O que este passo a passo não faz (leia antes de criar expectativa):**

- O sandbox devolve **dado fictício**, de propósito. O saldo e as transações que aparecerem **não
  são da sua conta** e não servem para conferir valor nenhum. Servem para provar que o caminho
  funciona.
- Ele não importa extrato, não grava nada no app e não muda o `db.sqlite3`. O script não escreve
  nada em disco.
- Ele não testa a produção. Produção é outro cadastro, outro certificado e outro caminho
  (seção 13).

## 2. Antes de começar

| Você precisa de | Onde arruma | Observação |
| --- | --- | --- |
| Conta PJ (MEI) ativa no Inter Empresas | A que o app já usa | A API do Inter é **exclusiva de pessoa jurídica**. Conta PF não tem esse caminho (D4). O sandbox em si pede só a conta de desenvolvedor; a conta PJ é a que a produção vai ler |
| Conta na comunidade de desenvolvedores | No próprio portal do sandbox, com "Entrar" | É a **Comunidade Inter**, não o login do Internet Banking PJ (registro do projeto de 2026-11-01; o texto atual do portal diz "a mesma conta da comunidade") |
| Dia útil, entre 8h e 20h | Calendário | O sandbox só responde nessa janela |
| O `.venv` do projeto com `requests` e `python-dotenv` | Já instalado | Comando deste projeto é sempre `.venv/bin/python` |
| Uma pasta fora do repositório para o certificado | `segredos/inter` na sua home, como sugere o `.env.example` | Certificado e chave **nunca** entram no git (G13) |

Não é preciso, nesta etapa, a senha do Internet Banking PJ nem o número da conta para preencher
nada. O número da conta só entra se a integração estiver associada a mais de uma conta (seção 8).

## 3. Os dois ambientes não se misturam

| | **Sandbox** (é o desta página) | **Produção** (fica para depois) |
| --- | --- | --- |
| Para que serve | Provar que a integração funciona | Ler a conta de verdade |
| Onde se cria | Portal do desenvolvedor, menu **Sandbox** | Internet Banking PJ: menu **Integrar → Nova integração** |
| Login | Conta da comunidade (Comunidade Inter) | Login do Internet Banking PJ |
| Quem pode | Conta de desenvolvedor ativa | Só cliente PJ com conta Inter Empresas ativa |
| Escopos | **Não se escolhem**: a integração nasce com os escopos listados | **Você escolhe**: marcar somente `extrato.read` |
| Dado devolvido | Fictício, para teste | Real |
| Validade do certificado | **30 dias** (a doc do sandbox diz isso) | **1 ano**, renovável a partir de 90 dias antes de expirar |
| Host | `https://cdpj-sandbox.partners.uatinter.co` | `https://cdpj.partners.bancointer.com.br` |

O host do sandbox foi conferido no portal em 2026-11-03. Os três caminhos usados pelo script
(`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`) vieram da documentação pública e
**nunca foram exercitados com credencial**. O script é o diagnóstico, não uma promessa: se um
caminho não existir nesse ambiente, o resultado esperado é 404, e isso é informação, não fracasso.

## 4. Passo 1: entrar no sandbox

1. Abra o portal do desenvolvedor: `https://developers.inter.co`.
2. No menu, escolha **Sandbox** (a rota é `/sandbox`).
3. Clique em **"Entrar"** e faça login **com a conta da comunidade**. Se não tiver, cadastre uma
   nova ali mesmo.
4. Confirme que a página abriu a área de integrações, e não uma tela de erro.

**Janela de funcionamento:** o sandbox fica disponível das **8h às 20h, de segunda a sexta-feira**.
Fora disso, o esperado é a página ou a API não responder. Não é defeito do projeto.

**Se a página não abrir:** confira o dia e a hora primeiro. Se estiver na janela, tente outro
navegador e confira a conexão. Não instale nada para isso.

## 5. Passo 2: criar a integração no sandbox

Os rótulos abaixo são os da documentação oficial do portal (consultada em 2026-11-08). A tela pode
mudar de posição, mas os nomes são estes.

1. Na área do sandbox, procure **"Nova integração"** e clique no botão **"Acessar"**.
2. Preencha **nome** e **descrição**. Sugestão: nome `gestao-financeira` e descrição "Leitura de
   saldo e extrato para o app pessoal".
3. **Escopos: no sandbox não há o que marcar.** A documentação é explícita: "Para o ambiente Sandbox
   não será necessário selecionar os escopos desejados, a integração será criada com os escopos
   listados." A integração de teste nasce com os escopos que o portal lista.
4. Clique em **"Criar integração"**.
5. Abra **"Minhas Integrações"** e clique na integração (ou nos três pontinhos, em **"Ações"**,
   **"Detalhar integração"**).
6. O status começa como **"Novo"** e vira **"Ativo"** em alguns minutos, depois do download da
   chave e do certificado. Aguarde; não recrie a integração por causa disso.
7. **Anote a data de expiração** que aparece no detalhe. No sandbox o certificado vale 30 dias.
   Vencido, é preciso criar outra integração.

**Sobre "só `extrato.read`":** a decisão do projeto (D4) é pedir o menor privilégio possível, e o
app pede exatamente esse escopo no token. No sandbox não existe a tela de escolha, então não há
como "marcar só o extrato" ali. Essa regra vale na **integração de produção**: na hora de criá-la,
marque **somente `extrato.read`** e **não marque nada de pagamento** (boleto, DARF, lote, Pix) nem
webhook. O sandbox é descartável; a integração de produção é a que lê a conta de verdade.

**Sucesso aqui é:** a integração aparece na lista, com status **"Ativo"**, e o detalhe mostra a
permissão `extrato.read` entre as associadas.

## 6. Passo 3: baixar certificado, chave e credenciais

Ainda no detalhe da integração:

1. Baixe **a chave e o certificado**. A documentação do portal cita os dois como arquivos `.crt` e
   `.key`; se o seu download vier como um pacote `.pfx` (um arquivo só, com senha), o passo 7.2
   extrai os dois. As duas formas funcionam neste projeto.
2. **A ordem importa:** as credenciais (`client_id` e `client_secret`) são geradas **quando você
   baixa** a chave e o certificado. Depois do download, elas aparecem no detalhe da integração
   (no sandbox, pelos três pontinhos → "Detalhar integração").
3. Copie `client_id` e `client_secret` **direto para o `.env`** (passo 5). Não cole em documento,
   chat, print, issue ou mensagem. Não anote em papel deixado na mesa.
4. Salve os arquivos baixados numa pasta temporária e siga para o passo 4.

**Atenção, produção:** na integração de produção as credenciais aparecem **uma única vez**, num
pop-up no momento do download, e a doc avisa que não podem ser visualizadas de novo. Se perder,
é criar outra integração. No sandbox elas continuam visíveis no detalhe.

## 7. Passo 4: guardar e converter no WSL

### 7.1 Criar a pasta segura e mover os arquivos

No WSL, na raiz do projeto:

```bash
mkdir -p ~/segredos/inter
chmod 700 ~/segredos/inter
```

O download é feito no navegador do Windows. Para trazer do Windows para o WSL, troque
`<usuario-windows>` e `<arquivo-baixado>` pelos nomes reais:

```bash
cp "/mnt/c/Users/<usuario-windows>/Downloads/<arquivo-baixado>" ~/segredos/inter/
ls -l ~/segredos/inter
```

Renomeie para nomes simples, porque eles vão aparecer no `.env`:

```bash
mv ~/segredos/inter/<certificado-baixado> ~/segredos/inter/inter.crt
mv ~/segredos/inter/<chave-baixada> ~/segredos/inter/inter.key
chmod 600 ~/segredos/inter/inter.crt ~/segredos/inter/inter.key
```

Se o download veio como `.pfx`, pule o renomeio e vá para 7.2. O `chmod 600` é o que impede outro
usuário da máquina de ler a chave; o diretório `700` impede de listar o conteúdo.

### 7.2 Se veio um `.pfx`: extrair certificado e chave em PEM

O projeto usa **PEM**, que é o formato de texto que começa com `-----BEGIN ...`. O `.pfx` é um
pacote fechado com senha. Para abrir:

```bash
openssl pkcs12 -in ~/segredos/inter/inter.pfx -clcerts -nokeys -out ~/segredos/inter/inter.crt
openssl pkcs12 -in ~/segredos/inter/inter.pfx -nocerts -nodes -out ~/segredos/inter/inter.key
chmod 600 ~/segredos/inter/inter.crt ~/segredos/inter/inter.key
```

- A primeira linha pede a senha do `.pfx` e grava só o certificado público.
- A segunda grava a chave privada **sem senha no arquivo** (`-nodes`). É assim que o `requests` do
  script consegue usá-la sem ninguém digitar senha; por isso o `chmod 600` não é opcional.
- Se o OpenSSL reclamar de algoritmo não suportado (mensagem citando `RC2` ou "unsupported"), repita
  os dois comandos acrescentando `-legacy` no fim de cada um. O Ubuntu 24.04 usa OpenSSL 3, que
  deixou alguns algoritmos antigos fora do padrão.
- Depois de confirmar que o par funciona (7.3), você pode apagar o `.pfx`. Não é obrigatório nesta
  etapa; se apagar, não tem volta.

### 7.3 Conferir que os arquivos servem

1. O certificado e a chave são texto? O primeiro pedaço do certificado tem de ser
   `-----BEGIN CERTIFICATE-----`, e o da chave, `-----BEGIN` com `PRIVATE KEY` na mesma linha:

   ```bash
   head -c 27 ~/segredos/inter/inter.crt; echo
   head -c 40 ~/segredos/inter/inter.key; echo
   ```

   Se aparecer lixo binário em vez disso, o certificado está em DER. Converta:

   ```bash
   openssl x509 -in ~/segredos/inter/inter.crt -inform DER -out ~/segredos/inter/inter.crt.pem
   mv ~/segredos/inter/inter.crt.pem ~/segredos/inter/inter.crt
   chmod 600 ~/segredos/inter/inter.crt
   ```

2. O certificado está na validade e é o esperado?

   ```bash
   openssl x509 -in ~/segredos/inter/inter.crt -noout -subject -issuer -dates
   ```

   As datas precisam englobar hoje. Se estiver vencido, crie outra integração (sandbox vence em 30
   dias) ou renove (produção).

3. **O par bate?** Esta é a checagem que evita o erro mais comum. Os dois comandos precisam imprimir
   **o mesmo hash**:

   ```bash
   openssl x509 -in ~/segredos/inter/inter.crt -noout -pubkey | openssl md5
   openssl pkey -in ~/segredos/inter/inter.key -pubout | openssl md5
   ```

   Hash diferente significa que a chave não é a do certificado: quase sempre é arquivo de outra
   integração, ou um par antigo (certificado novo com chave velha). Baixe os dois juntos, de novo.

## 8. Passo 5: preencher o `.env`

Todos os comandos desta seção são na raiz do projeto.

O `.env` fica na **raiz do projeto**, é bloqueado pelo `.gitignore` e **já pode existir** por causa
de outras configurações (a `SECRET_KEY` e o `DJANGO_ALLOWED_HOSTS` do celular). **Acrescente as
linhas, não substitua o arquivo.**

Se o `.env` ainda não existir:

```bash
cp .env.example .env
```

Acrescente (ou ajuste) estas seis linhas. **Nenhum valor de segredo vai neste documento**; os dois
vazios você preenche com o que copiou no passo 3:

```dotenv
INTER_AMBIENTE=sandbox
INTER_CLIENT_ID=
INTER_CLIENT_SECRET=
INTER_CERT_PATH=/home/vinicius/segredos/inter/inter.crt
INTER_KEY_PATH=/home/vinicius/segredos/inter/inter.key
INTER_CONTA_CORRENTE=
```

| Variável | O que vai nela | De onde vem |
| --- | --- | --- |
| `INTER_AMBIENTE` | `sandbox` nesta etapa | decisão desta página; o script só aceita `sandbox` ou `producao` |
| `INTER_CLIENT_ID` | o id da integração | detalhe da integração (passo 3) |
| `INTER_CLIENT_SECRET` | o segredo da integração | detalhe da integração (passo 3) |
| `INTER_CERT_PATH` | caminho **absoluto** do certificado em PEM | `~/segredos/inter/inter.crt` |
| `INTER_KEY_PATH` | caminho **absoluto** da chave em PEM | `~/segredos/inter/inter.key` |
| `INTER_CONTA_CORRENTE` | número da conta, só dígitos, **se** a integração tiver mais de uma | detalhe da integração, "contas associadas" |

Regras de preenchimento:

- **Sem aspas e sem espaço** em volta do valor. Espaço sobrando é a causa mais comum de token
  recusado.
- `INTER_CONTA_CORRENTE` comece **vazio**. O script só envia o cabeçalho `x-conta-corrente` se a
  variável estiver preenchida. Com uma conta só, ele não é necessário; se o saldo ou o extrato
  voltarem 403/404, confira no detalhe qual conta está associada e preencha com os dígitos.
- Confirme que o `.env` está mesmo fora do git:

  ```bash
  git check-ignore -v .env
  ```

  Precisa imprimir a regra do `.gitignore`. Se não imprimir nada, **pare**: o arquivo não está
  ignorado e o segredo entraria no repositório.

## 9. Passo 6: rodar o diagnóstico e ler cada etapa

Na raiz do projeto:

```bash
.venv/bin/python scripts/teste_inter.py
```

O script tem duas barreiras antes de falar com a API: ele confere se as quatro variáveis
obrigatórias estão preenchidas e se os dois arquivos existem. Se parar ali, é configuração, não
API.

### 9.1 O que cada etapa prova

| Etapa | O que o script faz | O que fica provado se passar | Se falhar |
| --- | --- | --- | --- |
| Antes de tudo | confere `.env` e existência dos arquivos | a configuração está completa | a mensagem diz o nome da variável ou o caminho que falta |
| **1/3 TLS** | abre a conexão com o host apresentando certificado e chave | o par é aceito pelo banco (mTLS) | `Falha de SSL/mTLS` |
| **2/3 Token** | `POST /oauth/v2/token` com `client_credentials` e `scope=extrato.read` | as credenciais valem e o escopo está autorizado | `Token recusado (HTTP ...)` |
| **3/3 Saldo** | `GET /banking/v2/saldo` | o caminho de saldo responde | `Saldo falhou (HTTP ...)` |
| **3/3 Extrato** | `GET /banking/v2/extrato` com os últimos 30 dias | o caminho de extrato responde e aceita o período | `Extrato falhou (HTTP ...)` |

A ordem é o diagnóstico: se o TLS falha, nada depois roda. Então o primeiro erro que aparece é o
primeiro a resolver.

### 9.2 Como é o sucesso

A saída tem esta forma (os valores mudam a cada execução, e no sandbox são fictícios):

```text
Ambiente: sandbox (https://cdpj-sandbox.partners.uatinter.co)
Conta corrente informada: não

[1/3] Autenticando com certificado mTLS...
  token obtido, expira em 3600s

[2/3] Consultando saldo...
  disponível: <valor fictício>
  <demais campos do saldo>

[3/3] Consultando extrato de <hoje - 30 dias> a <hoje>...
  <N> transação(ões) retornada(s)
  <até 5 linhas: data | tipo | valor | descrição>

Sucesso: certificado, token, saldo e extrato funcionaram.
```

**O que esse sucesso prova:** o certificado é aceito, as credenciais valem, o escopo está no token,
e os três caminhos respondem no sandbox com os parâmetros que o script usa.

**O que ele não prova:** que o sandbox devolve dado real (não devolve), que a produção funciona
(outro host e outro certificado) e que o importador está pronto (ele é a próxima etapa). Também não
confirma ainda o que a documentação não descreve: sinal do `valor`, `idTransacao` sempre preenchido e
estável, e o significado de `dataTransacao`/`dataInclusao`. Esses pontos são o que a P2-3 foi feita
para começar a responder; a confirmação final é na conta real.

### 9.3 A saída contém dado financeiro

No sandbox, os valores são fictícios. Em produção, **o script imprime saldo e até cinco transações
reais**. Para pedir ajuda, copie **apenas** a etapa que falhou, o código HTTP e os campos `title` e
`detail` do corpo do erro. Nunca cole os valores, as descrições das transações nem o conteúdo do
`.env`.

## 10. Quando falhar: tabela de erros

O script imprime `resposta.text[:800]` nos erros de HTTP, então o corpo da resposta aparece no
terminal. É o primeiro lugar a olhar. Abaixo, o que cada código costuma significar **neste script**.

| O que aparece | Significado | Causa provável | O que fazer |
| --- | --- | --- | --- |
| `Faltam variáveis no .env: ...` | parou antes da API | nome ausente ou vazio | preencher as variáveis listadas na mensagem |
| `INTER_AMBIENTE precisa ser 'sandbox' ou 'producao'.` | valor inválido | sobrou texto, acento ou outra palavra | deixar exatamente `sandbox` |
| `INTER_CERT_PATH aponta para um arquivo que não existe: ...` (ou o da chave) | caminho errado | caminho do Windows, caminho relativo, arquivo em outro nome | conferir com `ls -l` o caminho absoluto no WSL e corrigir o `.env` |
| `Falha de SSL/mTLS: ...` | o handshake TLS não completou | par certificado/chave não bate; PEM malformado; certificado expirado ou ainda não ativo; `.pfx` no lugar do PEM | refazer 7.2 e 7.3 (hash do par, datas, formato); conferir o status "Ativo" |
| `Token recusado (HTTP 400)` | requisição malformada | espaço ou quebra de linha no valor; credencial copiada incompleta | recopiar `client_id`/`client_secret` sem aspas nem espaço |
| `Token recusado (HTTP 401)` | credencial não aceita | `client_id`/`client_secret` inválidos, de outra integração, ou integração cancelada/expirada | conferir no detalhe se as credenciais são da mesma integração do certificado; se cancelada, criar outra |
| `Token recusado (HTTP 403)` | autenticado, sem autorização | escopo `extrato.read` fora da integração; credencial de outro ambiente; integração não ativada | conferir as permissões no detalhe e o status "Ativo" |
| `Token recusado (HTTP 404)` | caminho ou host errado para o ambiente | `INTER_AMBIENTE` trocado, host fora do ar | conferir o ambiente; repetir dentro da janela |
| `Token recusado (HTTP 503)` | serviço indisponível | fora da janela 8h–20h, manutenção | repetir em dia útil, dentro da janela |
| `Saldo falhou (HTTP 403)` ou `Extrato falhou (HTTP 403)` | o token não autoriza essa API | escopo ausente; integração recriada e o `.env` ficou com credencial antiga | conferir as permissões e as credenciais |
| `Saldo falhou (HTTP 404)` ou `Extrato falhou (HTTP 404)` | recurso não encontrado | caminho nunca exercitado; conta informada inexistente; `x-conta-corrente` errado | deixar `INTER_CONTA_CORRENTE` vazio se há uma conta só; conferir o número se preencheu; guardar o corpo do erro |
| `... (HTTP 405)` | método não permitido | **apareceu de propósito em 2026-11-03**: um `GET` no endpoint de token sem credencial responde 405, e era o esperado (o token é `POST`). Rodando o script (que usa `POST`), 405 aponta para host/caminho ou proxy, não para a credencial | conferir `INTER_AMBIENTE` e o host; não testar o token pelo navegador |
| `... (HTTP 429)` | limite de chamadas | muitas execuções em pouco tempo | esperar um minuto e repetir |
| `Falha de rede: ...` (inclui `Timeout`) | a conexão não completou | internet, DNS, firewall, proxy, ou sandbox fora da janela | conferir a rede; repetir dentro da janela |

Nota sobre o 401: a referência pública lista **400, 403, 404 e 503** para token, saldo e extrato; o
401 aparece em outros endpoints com o corpo `Acesso negado` / `Login/senha inválido`. Se vier no
script, trate como credencial recusada e siga a linha da tabela.

Nota sobre TLS: alguns problemas de certificado chegam embrulhados em `Falha de rede`, com `SSL` no
meio da mensagem (o `requests` trata parte dos erros de conexão assim). Se a mensagem citar `SSL`,
`certificate` ou `handshake`, siga a linha do certificado, não a da rede.

Se a integração ficar em **"Novo"** e não virar "Ativo": aguarde alguns minutos; o status muda
depois que a chave e o certificado são baixados. Se não mudar, confira se o download concluiu antes
de recriar.

## 11. O que nunca sai deste computador (G13)

Não cole em chat, documento, print, issue, e-mail, WhatsApp ou mensagem para mim:

- o conteúdo do `.env` (nem a linha inteira, nem "só o pedacinho do meio");
- `INTER_CLIENT_ID` e `INTER_CLIENT_SECRET`;
- o certificado (`inter.crt`) e a chave (`inter.key`), ou o `.pfx` e a senha dele;
- print da tela de detalhe da integração em produção (as credenciais aparecem lá);
- a saída do script em produção (saldo e transações reais).

Pode e deve mandar: o **nome** da variável que está errada, o **código HTTP**, a **etapa** que
falhou e os campos `title`/`detail` do erro. Isso resolve quase todo diagnóstico sem expor nada.

## 12. Checklist final

Marque na ordem. Se travar em alguma caixa, a seção indicada entre parênteses é o lugar de voltar.

**No portal**

- [ ] Entrei no sandbox em dia útil, entre 8h e 20h (seção 4)
- [ ] Entrei com a conta da comunidade, não com o Internet Banking PJ (seção 4)
- [ ] Criei a integração no sandbox com nome e descrição (seção 5)
- [ ] Ela chegou ao status **"Ativo"** e mostra `extrato.read` nas permissões (seção 5)
- [ ] Anotei a **data de expiração** (sandbox vale 30 dias) (seção 5)
- [ ] Baixei **chave e certificado** antes de copiar as credenciais (seção 6)
- [ ] Copiei `client_id` e `client_secret` direto para o `.env`, sem passar por documento (seção 6)

**No WSL**

- [ ] Certificado e chave estão na pasta `segredos/inter` da sua home, diretório `700`, arquivos `600` (seção 7.1)
- [ ] Se veio `.pfx`, extraí para `.crt` e `.key` em PEM (seção 7.2)
- [ ] O certificado está na validade e o **hash do par bate** (seção 7.3)
- [ ] O `.env` tem as seis variáveis do Inter, sem apagar as do Django (seção 8)
- [ ] `git check-ignore -v .env` imprime a regra do `.gitignore` (seção 8)

**O diagnóstico (P2-3)**

- [ ] Rodei `.venv/bin/python scripts/teste_inter.py` (seção 9)
- [ ] A etapa de **TLS** passou (seção 9.1)
- [ ] A etapa de **token** passou (seção 9.1)
- [ ] A etapa de **saldo** passou (seção 9.1)
- [ ] A etapa de **extrato** passou (seção 9.1)
- [ ] Anotei a **data do primeiro extrato** bem-sucedido: ela é a data de corte da primeira
      importação, decidida na P2-8 (seção 9.2)
- [ ] Levei o resultado para a sessão só com etapa e código, sem valores (seção 9.3)
- [ ] **Rodei a P2-3**: com as três etapas verdes, o item pode ser fechado no `PENDENCIAS.md`

## 13. Depois do sandbox: a integração de produção

Não é o desta página, mas deixa o caminho anotado para não misturar as coisas:

1. No Internet Banking PJ: menu **Integrar → Nova integração**.
2. Nome, descrição e **permissões: marcar somente `extrato.read`**. Não marcar pagamento (boleto,
   DARF, lote, Pix) nem webhook. Ler e aceitar os termos da API escolhida.
3. Preencher o formulário (clientes, empresa, negócio) e enviar. A integração fica em
   **"Em validação"** e passa por análise; nesse período não dá para criar outra.
4. Aprovada, baixar **chave e certificado** pelos três pontinhos → **"Download chave e
   certificado"**. As credenciais aparecem **uma única vez**, num pop-up: salvar na hora.
5. O certificado de produção vale **1 ano**, renovável a partir de 90 dias antes de expirar. A
   renovação entrega novos `.crt` e `.key` e mantém `client_id`, `client_secret` e escopos.
6. Trocar `INTER_AMBIENTE=sandbox` por `INTER_AMBIENTE=producao` é mudança de ambiente com dado
   real: ação do dono, com o comando e o efeito na mesa antes (G3).

## 14. Fontes e data

Consultadas em **2026-11-08**, só documentação pública, sem login e sem credencial:

| Página | O que foi usado |
| --- | --- |
| [Sandbox](https://developers.inter.co/docs/sandbox) | janela 8h–20h de segunda a sexta; dados fictícios |
| [Como criar uma integração no Sandbox?](https://developers.inter.co/docs/sandbox/como-criar-uma-aplicacao) | login com a conta da comunidade; passos de criação; escopos não selecionáveis no sandbox; status "Novo"/"Ativo"; certificado de 30 dias |
| [O que é Sandbox?](https://developers.inter.co/docs/sandbox/sobre-este-portal) | ambiente de homologação com dados fictícios |
| [Como criar uma integração?](https://developers.inter.co/docs/introducao/como-criar-uma-aplicacao) | fluxo de produção; escolha de permissões; análise; credenciais exibidas uma vez |
| [Como renovar uma integração?](https://developers.inter.co/docs/introducao/como-renovar-uma-integracao) | validade de 1 ano em produção; renovação entrega `.crt` e `.key` |
| [Token OAuth](https://developers.inter.co/references/token) | `client_credentials`, `scope`, token de 60 minutos; respostas 200/400/403/404/503 |
| [Referência Banking (OpenAPI)](https://developers.inter.co/redocusaurus/swagger-banking-yaml.yaml) | `/saldo` e `/extrato` exigem `extrato.read`; respostas 400/403/404/503; corpos de erro |
| `PROGRESS.md`, entradas de 2026-11-01 e 2026-11-03 | login da Comunidade Inter no sandbox; host confirmado; `GET` no token dá 405 sem credencial |
| `scripts/teste_inter.py` e `.env.example` | etapas, mensagens, nomes das variáveis e formato esperado |

**Limite deste documento:** nada aqui foi exercitado com credencial real. O que o portal promete
está citado acima; o que o ambiente devolve é o que o script vai mostrar. Se a tela ou o texto do
portal mudarem, vale o portal, não esta página.
