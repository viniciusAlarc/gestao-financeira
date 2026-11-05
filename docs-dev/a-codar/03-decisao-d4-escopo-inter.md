# Decisão D4 — Escopo da integração com o Inter

> **Estado: pesquisa concluída; a decisão é do dono.** Este documento delimita o que a API direta do
> Inter Empresas cobre e o que fica de fora, **com fonte oficial e data da consulta**. Não fecha D4 e
> não promete nada (P2-6 em `PENDENCIAS.md`).
> **Consulta feita em 2026-11-05**, só em documentação pública: nenhum acesso ao portal com login,
> nenhuma credencial usada, nenhuma chamada de API.
> Liga com **P2-8** (mapeamento da importação): as perguntas da seção 7 são as mesmas que travam o
> código da importação na rodada seguinte (G2).

## 1. Resposta curta

| Pergunta | Resposta com fonte | Fonte |
|---|---|---|
| A API direta cobre o quê? | **Saldo e extrato da conta corrente PJ** do Inter Empresas, mais pagamentos (boleto, DARF, lote, Pix) e webhooks. | S1, S3, S4, S5, S6 |
| Quem pode usar? | **Só pessoa jurídica**: "O acesso às APIs do Inter é exclusivo para clientes pessoa jurídica". Para consumir, a empresa precisa de conta ativa no Inter Empresas. | S1, S2 |
| Conta PF entra? | **Não pela API direta.** É um dos casos que só Open Finance alcança — e com barreira de credenciamento (seção 4). | S2, S9 |
| Cartão de crédito entra? | **Não há API de cartão de crédito** na lista oficial de APIs do portal. O extrato da conta mostra o que passou pela conta, não a fatura. | S1 |
| Boleto de outra titularidade entra? | A API **paga** boleto por código de barras e **consulta pagamentos feitos**; não lista boletos a pagar nem boletos emitidos para outra titularidade. | S6, S7 |
| Precisa Open Finance para quê? | Consolidar **contas de outras instituições (PF ou PJ), cartão de crédito, investimentos** — sempre com uma instituição receptora autorizada pelo Banco Central. | S9, S10 |
| O que a importação preenche no `Movimento`? | `data`, `valor`, `tipo`, `descricao`, `origem=inter` — e **nada de** `categoria`, `criado_por` nem chave antiduplicidade (seção 5). | S3, S5 |

## 2. O que a API direta cobre (conta PJ)

A lista oficial de funcionalidades da API Banking, transcrita do portal:

> "A API Banking disponibiliza as funcionalidades mais básicas do serviço bancário para integração com
> o sistema de gestão do parceiro Inter (...) Estas funcionalidades incluem até o momento: Consultar
> saldo. Consultar extrato. Exportar extrato para PDF. Incluir pagamento com código de barras. Incluir
> pagamento de DARF. Consultar pagamentos e DARF. Incluir pagamento em lote. Consultar pagamento em
> lote. Cancelar agendamento do pagamento. Incluir pagamento Pix. Consultar pagamento Pix." (S1)

A referência técnica acrescenta um endpoint que não aparece nessa lista: **extrato enriquecido**
(`/extrato/completo`, S5), também listado no SDK Python (S15). Ele nasceu como BETA em 10/10/2022
(S16) e a página atual não traz mais a marcação de BETA (consulta de 2026-11-05).

### 2.1 Saldo

- `GET /saldo`, escopo `extrato.read` (S4).
- Retorna: `disponivel` (saldo líquido), `bloqueadoCheque`, `bloqueadoJudicialmente`,
  `bloqueadoAdministrativo`, `limite` e `dataReferencia` (este último quando a consulta cai em dia não
  útil) (S4).
- Rate limit: 10 chamadas por minuto em produção e no sandbox; o token vale 60 minutos (S4, S8).

### 2.2 Extrato

| Endpoint | O que devolve | Observações |
|---|---|---|
| `GET /extrato` | Lista simples: `dataEntrada`, `tipoTransacao`, `tipoOperacao` (D/C), `valor`, `titulo`, `descricao`, `cpmf` | **Período máximo de 90 dias** entre `dataInicio` e `dataFim`; escopo `extrato.read` (S3) |
| `GET /extrato/completo` | Transação enriquecida: `idTransacao`, `dataInclusao`, `dataTransacao`, `tipoTransacao`, `tipoOperacao`, `valor`, `titulo`, `descricao`, `numeroDocumento` e `detalhes` por tipo (Pix, boleto, transferência, tarifa…) | Também limitado a 90 dias; paginação tradicional (até 10.000) ou scroll; filtros por `tipoOperacao` e `tipoTransacao` (S5) |
| `GET /extrato/exportar` | Extrato em PDF (base64) | Mesmo escopo e mesma janela (S3) |

- **Múltiplas contas:** quando a integração está associada a mais de uma conta corrente, a conta vai no
  header `x-conta-corrente` (só números, com dígito). Com uma conta só, o header não é necessário (S3).
- **Sandbox devolve dado fictício**, só para validar a requisição (S3).
- `tipoTransacao` traz um vocabulário fechado, entre outros: `PIX`, `PAGAMENTO`, `BOLETO_COBRANCA`,
  `TRANSFERENCIA`, `COMPRA_DEBITO`, `DEBITO_AUTOMATICO`, `DOMICILIO_CARTAO`, `TARIFA`, `IMPOSTO`,
  `INVESTIMENTO`, `ESTORNO`, `CASHBACK`, `JUROS`, `MULTA`, `SAQUE`, `CAMBIO` (S3).

### 2.3 Pagamentos (não é preciso para importar)

- `POST /pagamento` paga boleto, convênio ou tributo por código de barras; **pode exigir aprovação
  manual** dependendo das configurações da conta (S6). Há também DARF, pagamento em lote, Pix e
  cancelamento de agendamento (S1, S6).
- Para importar extrato, nada disso é necessário: o único escopo exigido é **`extrato.read`** (S3, S4).
  Pedir só esse escopo é o menor privilégio possível para a v1 (proposta, não decisão).

### 2.4 Receber dinheiro é outra API

- **API Pix** = cobrança Pix recebida (criar/consultar cobranças, devoluções, webhooks) (S13).
- **API Cobrança (Boleto com Pix)** = emissão e gestão de boletos **seus** (recebíveis): emitir,
  cancelar, consultar, PDF, sumário (S7).
- Nenhuma das duas serve para **listar contas a pagar** — elas tratam do dinheiro que entra.

### 2.5 Quem pode acessar

- "O acesso às APIs do Inter é exclusivo para clientes pessoa jurídica." (S2)
- "Para consumir nossas APIs, sua empresa deve ter uma conta ativa no Inter Empresas." (S1)
- O portal lista SDKs em **Java, C#, PHP e Python** (S15). A descoberta de 2026-11-01 registrava "SDK
  oficial só em Java e C#"; a informação envelheceu — há SDK Python hoje (consulta de 2026-11-05).

## 3. O que fica de fora da API direta

### 3.1 Conta de pessoa física (PF)

- A API é exclusiva de PJ (S2). Não existe caminho, na documentação do portal, para ler conta PF pela
  API do desenvolvedor.
- A conta PF do Inter aparece no Open Finance, ofertado ao cliente PF/MEI/PJ no app (S11) — mas como
  compartilhamento entre instituições, não como API para um app pessoal (seção 4).

### 3.2 Cartão de crédito

- **Não há API de cartão de crédito** entre as APIs listadas no portal: Banking, Cobranças, Pix, Pix
  Automático, Fórum e Webhooks (S1). Ausência conferida em 2026-11-05, não é uma exclusão escrita.
- O extrato da conta pode conter movimento **relacionado a cartão** (por exemplo `COMPRA_DEBITO` e
  `DOMICILIO_CARTAO` no vocabulário de `tipoTransacao`, S3). Isso é o que passou **na conta** (compra no
  débito, débito de fatura), não a fatura nem as compras individuais do cartão de crédito.
  **Leitura minha, não afirmação da doc** — a doc não descreve o significado de cada tipo.

### 3.3 Boleto de outra titularidade

Três coisas diferentes com o mesmo nome:

| O que é | A API direta faz? | Fonte |
|---|---|---|
| **Pagar** um boleto (de qualquer beneficiário) por código de barras | Sim — `POST /pagamento`, sujeito à aprovação manual conforme a conta | S6 |
| **Consultar** os pagamentos já feitos (inclusive boleto) | Sim — `GET /pagamento` | S1, S6 |
| **Listar** boletos a pagar, ou boletos emitidos para outra titularidade | **Não** — não há endpoint de "boletos a pagar"; a API Cobrança só trata dos boletos que **você emite** | S1, S7 |

- Consequência: "o que já está comprometido à frente" (`Previsto`) **não sai do Inter** por nenhum
  caminho. Continua manual, como o plano já previa (D2).
- **Não confirmado:** se a conta tem restrição para pagar boleto cujo pagador é outra pessoa. A
  especificação não fala de titularidade no `/pagamento` (S6); só o sandbox/produção responderia.

### 3.4 Investimentos e aplicações

- Movimentos de aplicação/resgate aparecem no extrato como `INVESTIMENTO` (S3). **Posição** de
  investimento (carteira, rentabilidade) não tem endpoint na lista oficial (S1).
- Open Finance cobre investimentos em fase posterior (S10).

### 3.5 Contas a pagar, agendamentos e previsto

- A API consulta **agendamentos feitos por ela mesma** (`/pagamento`), não as contas a pagar da conta
  (S1, S6). Não há endpoint de "boletos a vencer" nem de "faturas futuras".
- O `Previsto` do app fica 100% manual na v1 — nada a importar aqui.

## 4. O que exigiria Open Finance em vez da API direta

### 4.1 O que o Open Finance cobre

- "O consumidor poderá compartilhar seus dados (cadastros, transações em conta, informações sobre
  cartões e operações de crédito) com as instituições de sua preferência. Tudo é feito por meio de
  consentimento, que pode ser revogado a qualquer momento." (S9)
- A partir da 2ª fase: "compartilhamento de informações cadastrais e transacionais de contas de
  depósito à vista, de poupança, de pagamento pré-pagas, de cartão de crédito e de operações de
  crédito"; investimentos e seguros em fase futura (S9).
- Caso de uso descrito pelo próprio Open Finance: "Uso do agregador de dados: o cliente consente e
  reúne dados de várias instituições em um único ambiente." (S10)
- Vale para **pessoa física e jurídica**: "Poderão autorizar o compartilhamento de dados os clientes
  (tanto pessoas físicas como jurídicas) de instituições participantes" (S9).

### 4.2 A barreira que decide o caminho

- "Com quem eu posso/poderei compartilhar os meus dados? Com **instituições financeiras, de pagamento
  ou demais instituições autorizadas a funcionar pelo Banco Central do Brasil**." (S9)
- "Para participar do Open Finance, bancos, fintechs e cooperativas precisam ser **autorizadas pelo
  Banco Central do Brasil**." (S9)
- Ou seja: **um app pessoal não é receptor de Open Finance.** Para ler dados por essa via seria preciso
  ser uma instituição participante ou passar por uma (agregador licenciado) — a doc oficial descreve o
  compartilhamento **entre instituições autorizadas**, não o acesso direto por aplicativo de pessoa
  física. O caminho de contratar um agregador é prática de mercado, **não está descrito na doc oficial**
  — trate como pergunta em aberto (seção 8).

### 4.3 O Inter no Open Finance

- A ajuda oficial do Inter diz que o Open Finance está disponível "para clientes Pessoa Física (PF), MEI
  e Pessoa Jurídica (PJ)" e descreve os dois sentidos: trazer dados de outra instituição **para** o
  Inter e compartilhar dados **do** Inter com outra instituição (S11).
- "Open Finance é um serviço regulamentado pelo Banco Central" (S12).

### 4.4 Leitura para o D4

Open Finance **não substitui a API direta** para ler a conta PJ do Inter: é o caminho para consolidar
**outras** instituições (inclusive conta PF), cartão de crédito e investimentos — e exige instituição
receptora autorizada. Para a v1, a API direta continua sendo o caminho da conta PJ; Open Finance é
fase futura, se o dono quiser consolidar o resto.

## 5. O que a importação consegue preencher no `Movimento`

Campos do modelo atual (`financas/models.py`, lido em 2026-11-05 — não alterado):

| Campo do `Movimento` | Vem da API? | De onde / observação |
|---|---|---|
| `data` | Sim | `dataTransacao` ou `dataInclusao` (extrato enriquecido) / `dataEntrada` (extrato simples). **Qual usar muda o total do mês** — decisão do dono (seção 7) |
| `valor` | Sim | String no JSON; converter para `Decimal` com 2 casas. **Sinal não documentado** — confirmar no sandbox (seção 8) |
| `tipo` | Sim | `tipoOperacao`: `D` → despesa, `C` → receita (S3). `INVESTIMENTO`, `ESTORNO` e `CASHBACK` merecem regra própria — decisão do dono |
| `conta` | Não | A API não conhece a `Conta` do app; o vínculo é fixo, decidido pelo dono (P2-8) |
| `categoria` | **Não** | O modelo exige categoria (sem nulo). A API não traz nenhuma. Precisa de categoria padrão ou regra — decisão do dono (D3/P2-8) |
| `descricao` | Sim | `titulo` + `descricao` (máx. 120 no app; truncar). O extrato enriquecido traz `detalhes` melhores (nome do pagador/recebedor, CPF/CNPJ, endToEnd) (S5) |
| `origem` | — | Fixo `inter` |
| `criado_por` | **Não** | A API não tem autor; o importador precisa gravar um usuário — decisão do dono (P2-8) |
| `criado_em` | — | Automático do Django |

**O que o modelo não tem e a fase 7 vai precisar:**

- **Chave antiduplicidade.** O plano exige "um extrato importado duas vezes não gera movimento
  repetido" (fase 7). O extrato **simples não tem id de transação**; o **enriquecido tem
  `idTransacao`** (S3, S5). O modelo não tem campo para guardar id externo, e `financas/models.py` é
  zona vermelha nesta rodada. Decisão e próxima rodada.
  **Não confirmado:** se `idTransacao` vem sempre preenchido e se é estável entre consultas — a
  especificação não descreve.
- **Saldo conciliado.** O app calcula `Conta.saldo` como `saldo_inicial + receitas − despesas`. O
  Inter tem `/saldo` com `disponivel`. Para o saldo do app bater com o do Inter, o `saldo_inicial` da
  conta precisa estar ancorado no saldo do Inter na data de corte do histórico importado — decisão do
  dono.

## 6. O que entra na v1 (proposta para o dono confirmar)

**Entra:**

1. Leitura da **conta corrente PJ** do Inter: saldo e extrato (simples e/ou enriquecido).
2. Importação de extrato como `Movimento` com `origem=inter`, numa única `Conta` do app (P2-8).
3. Escopo de permissão mínimo: **`extrato.read`** (nada de pagamento).

**Fica fora da v1 (com o motivo):**

| Fica fora | Por quê | Fonte |
|---|---|---|
| Conta PF | API é exclusiva PJ; PF só por Open Finance | S2, S11 |
| Cartão de crédito | Não há API de cartão; Open Finance é outro caminho | S1, S9 |
| Boletos a pagar / de outra titularidade | API não lista; só paga por código de barras | S1, S6, S7 |
| Investimentos (posição) | Sem endpoint | S1 |
| Pagamentos, Pix, DARF, Cobrança | Não é preciso para importar; amplia risco | S1, S6, S7 |
| Open Finance | Exige instituição receptora autorizada pelo BCB | S9 |
| `Previsto` automático | O Inter não expõe contas a pagar | S6 |

## 7. Perguntas que só o dono responde (liga com P2-8)

1. **A conta é PJ?** Qual conta corrente (e CNPJ) a integração vai ler? Se houver mais de uma conta PJ,
   entrar todas ou só uma?
2. **Qual `Conta` do app** recebe os movimentos importados? Ela já existe no banco?
3. **Data do movimento**: usar `dataTransacao` (quando o dinheiro se moveu) ou `dataInclusao` /
   `dataEntrada` (quando apareceu no extrato)? As duas mudam o fechamento do mês.
4. **Categoria**: importar tudo numa categoria padrão ("Não categorizado") e classificar depois, ou
   criar regra por descrição? O modelo exige categoria em todo movimento.
5. **Antiduplicidade**: aceitar dependência do `idTransacao` do extrato enriquecido (exige campo novo no
   `Movimento`, próxima rodada) ou tentar chave composta `data+valor+descrição` (mais frágil)?
6. **`criado_por`**: qual dos dois logins fica registrado nos movimentos importados?
7. **Investimentos, estornos e cashback**: importar como movimento (com categoria própria) ou ignorar?
8. **Saldo**: ancorar o `saldo_inicial` da conta no saldo do Inter na data de início do histórico?
9. **Escopo**: confirmar que a v1 pede só `extrato.read` na criação da integração (P2-1).
10. **Cartão e PF** ficam fora da v1 — confirmar que é isso mesmo (D4).

## 8. O que ainda não está confirmado (o sandbox responde — P2-3)

| Dúvida | Por quê | Como resolver |
|---|---|---|
| Sinal do campo `valor` | A especificação tipa `valor` como string e não diz se vem com sinal; o sinal pode vir só no `tipoOperacao` | Rodar `scripts/teste_inter.py` com credencial (P2-3) |
| `idTransacao` sempre preenchido e estável | A doc não descreve | Sandbox + duas consultas iguais |
| `dataEntrada` é a data do movimento ou da entrada no extrato | A doc não descreve | Conferir com extrato real do dono |
| Restrição a boleto de terceiro | A doc não fala de titularidade no pagamento | Teste no sandbox |
| MEI tem acesso? | A doc fala "pessoa jurídica" e "conta Inter Empresas"; MEI é PJ, mas não há frase específica | Confirmar com o Inter ou no cadastro |
| O que o Open Finance do Inter transmite de PJ | A ajuda diz que PF/MEI/PJ compartilham, sem detalhar quais dados | Fora da v1; só quando/se virar fase futura |

## 9. Fontes (todas consultadas em 2026-11-05)

| ID | Página | O que foi usado |
|---|---|---|
| S1 | [Nossas APIs](https://developers.inter.co/docs/introducao/nossas-apis) | Lista de funcionalidades da API Banking; "sua empresa deve ter uma conta ativa no Inter Empresas"; APIs existentes (sem cartão) |
| S2 | [Como criar uma integração](https://developers.inter.co/docs/introducao/como-criar-uma-aplicacao) | "O acesso às APIs do Inter é exclusivo para clientes pessoa jurídica" |
| S3 | [Referência Banking — Extrato](https://developers.inter.co/references/banking#tag/Extrato) | `/extrato`: 90 dias, escopo `extrato.read`, campos e tipos de transação. Conteúdo lido na especificação OpenAPI servida pelo portal: `https://developers.inter.co/redocusaurus/swagger-banking-yaml.yaml` |
| S4 | [Referência Banking — Saldo](https://developers.inter.co/references/banking#tag/Saldo) | `/saldo`: campos, escopo e rate limit |
| S5 | [Referência Banking — Extrato enriquecido](https://developers.inter.co/references/banking#tag/Extrato) | `/extrato/completo`: `idTransacao`, `dataTransacao`, `dataInclusao`, `detalhes`, paginação |
| S6 | [Referência Banking — Pagamento](https://developers.inter.co/references/banking#tag/Pagamento) | Pagamento por código de barras, aprovação manual, consulta de pagamentos |
| S7 | [API Cobrança (Boleto com Pix)](https://developers.inter.co/references/cobranca-bolepix) | Emissão de boletos próprios (recebíveis) |
| S8 | [Token OAuth](https://developers.inter.co/references/token) | Token de 60 minutos |
| S9 | [Open Finance Brasil — Perguntas frequentes](https://openfinancebrasil.org.br/perguntas-frequentes) | PF e PJ; dados da 2ª fase (contas, poupança, pré-paga, cartão, crédito); só instituições autorizadas pelo BCB recebem |
| S10 | [Conheça o Open Finance](https://openfinancebrasil.org.br/conheca-o-open-finance) | Consentimento revogável; agregador de dados; fases futuras (câmbio, investimentos, seguros) |
| S11 | [Inter — Open Finance na conta PF](https://ajuda.inter.co/open-finance/como-compartilhar-dados-pelo-open-finance-na-conta-pf/) | Disponível para PF, MEI e PJ; compartilhamento nos dois sentidos |
| S12 | [Inter — O que é o Open Finance](https://ajuda.inter.co/open-finance/o-que-e-o-open-finance) | Serviço regulamentado pelo BCB |
| S13 | [Changelog 24/12/2025](https://developers.inter.co/changelog/24/12/2025) | Pix e Banking desabilitadas para novas integrações, exceto saldo e extrato |
| S14 | [Changelog 12/03/2026](https://developers.inter.co/changelog/12/03/2026) | Pix e Banking reabilitadas para novas integrações |
| S15 | [SDK Python — API Banking](https://developers.inter.co/docs/sdks/sdk-python#api-banking) | SDK Python existe; lista de funcionalidades cobertas |
| S16 | [Changelog 10/10/2022](https://developers.inter.co/changelog/10/10/2022) | Extrato enriquecido lançado como BETA |
| S17 | [API Pix](https://developers.inter.co/references/pix) | Cobrança Pix recebida (recebíveis) |

**Nota de método:** o portal é uma SPA; o texto das páginas de guia foi lido no índice de busca do
próprio portal (`search-doc-1793133581277.json`, gerado no build de 2026-10-27) e a referência técnica,
na especificação OpenAPI que a mesma página carrega. Nenhuma página exigiu login.

**Limite desta pesquisa:** só documentação pública. Nada aqui foi exercitado contra o sandbox — é
exatamente o que a P2-3 faz. Até lá, o que está na seção 8 continua **não confirmado**.
