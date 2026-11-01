# Briefing: app de gestão financeira pessoal

> **Estado: descoberta.** Ainda não há stack escolhida nem código. Este arquivo guarda a **descoberta do produto** (decisão fechada e não codada, G7) para a próxima sessão não repetir perguntas.
> **O estado do projeto não mora aqui:** o que foi feito fica em `PROGRESS.md`, o que está aberto em `PENDENCIAS.md`, e as fases em `docs-dev/painel.json`.
> Nome `gestao-financeira` é provisório. Pasta: `C:\Users\ViniciusAlarção\Documents\Projetos\gestao-financeira`.
> Regras de trabalho: `AGENTS.md` na raiz deste repositório. As regras universais e o perfil do dono moram em `~/Documents/IA` (`guardrails-ia/guardrails-core.md`, `cnr/como-trabalhamos.md`, `pessoal/sobre-mim.md`), que o Claude carrega sozinho e o Zed não.

## 1. O problema, nas palavras do dono

"Tenho diversos gastos e não tenho controle nem visão de para onde meu dinheiro está indo. Ele parece simplesmente evaporar."

Não é falta de app: é falta de **visão**. O critério de sucesso do produto é responder, sem esforço, "para onde foi o dinheiro deste mês" e "o que já está comprometido à frente".

## 2. O que ele quer ver ao abrir

1. **Saldo** (quanto tem agora).
2. **Gasto atual** (quanto já saiu no período).
3. **Gastos previstos** (o que já está comprometido e ainda vai sair).

## 3. Uso e usuários

| Item          | Decisão                                                                                                   |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| Usuários      | Duas pessoas: ele e a esposa. Uso exclusivamente pessoal, não é produto.                                  |
| Uso principal | **Celular.**                                                                                              |
| Forma         | **Web app responsivo** (instalável como PWA), para não publicar em loja.                                  |
| Sincronização | **Sempre que abrir** o app, não em horário fixo.                                                          |
| Nuvem         | Dados ficam sob controle dele. Nenhum dado financeiro em serviço de terceiro sem decisão explícita (G20). |

## 4. De onde vêm os dados

Integração **direta com a conta PJ do Inter**, para não importar arquivo de extrato. Ele respondeu "acredito que tudo isso" quando perguntei se entram extrato e saldo da PJ, conta PF, cartão, Pix e boletos. Ou seja: **intenção de consolidar tudo, escopo a fechar**.

Fatos conferidos no portal do Inter em 01/11/2026:

- Portal do desenvolvedor Inter Empresas tem [Extrato e Saldos](https://developers.inter.co/references/banking), além de Pix, Cobrança e Pagamento.
- O credenciamento é feito no Internet Banking PJ: _Soluções para sua empresa → Nova Integração_, aceitar as permissões, e depois **baixar e ativar chaves e certificado** ([passo a passo no portal](https://developers.inter.co/docs/sdks/sdk-python)).
- Autenticação é **certificado do cliente (mTLS) + token**, com **sandbox** para teste antes de produção.
- SDK oficial só em **Java e C#**; fora isso, HTTP direto com o certificado serve em qualquer linguagem.

### Consequências técnicas já certas

- Precisa de **backend com processo**: guardar certificado, pedir token, chamar a API, sincronizar e gravar.
- O certificado e a chave são **segredo** (G13): ficam em `.env` ou cofre local, fora do git, nunca em documento, print ou repositório.
- Acesso pelo celular significa backend **alcançável fora de casa**. Três caminhos, com custo diferente: só na rede local (o celular só sincroniza em casa), túnel (Cloudflare Tunnel e afins), ou VPS barato. **Decisão pendente**, e entra no G20.

## 5. O que ainda não está decidido

| #   | Decisão                      | Por que importa                                                                                                                                                                                                                                                       |
| --- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | **Stack**                    | Definir depois da descrição completa. Critérios: conforto dele (Python é o forte), suporte a mTLS, agendamento e um processo que rode no PC. Nenhuma das opções está instalada: `git` existe, **Python e Node não**. Java não foi verificado. Instalar exige ok dele. |
| D2  | **O que é "gasto previsto"** | Pode ser conta a pagar com data, gasto recorrente (assinatura, aluguel) ou orçamento por categoria. São três features diferentes.                                                                                                                                     |
| D3  | **Categorização**            | Manual, por regra (descrição do lançamento) ou ambos. Decidir antes da tela, porque define o modelo de dados.                                                                                                                                                         |
| D4  | **Escopo da integração**     | A API de Empresas cobre a PJ. Conta PF, cartão de crédito e boletos de outra titularidade podem exigir outro caminho (Open Finance). Confirmar antes de prometer "tudo".                                                                                              |
| D5  | **Duas pessoas**             | Quem lança, quem só vê, e se cada um tem login. Com 2 usuários, login simples já basta; sem login também é opção, se o app só roda na rede dele.                                                                                                                      |
| D6  | **Onde o backend roda**      | PC de casa, túnel ou VPS. Muda custo, disponibilidade e como o celular alcança.                                                                                                                                                                                       |

## 6. Perguntas em aberto para a próxima conversa

1. Do que você chama "gasto previsto": conta com vencimento, assinatura recorrente, ou limite de orçamento por categoria?
2. O cartão de crédito entra? Se sim, o gasto conta na data da compra ou no vencimento da fatura?
3. A conta PF (pessoal) e a PJ (MEI) ficam no mesmo app, com relatório separado?
4. A esposa lança despesa pelo celular ou só consulta?
5. O app precisa funcionar fora de casa, ou sincronizar quando chegar é suficiente?

## 7. Próximos passos combinados

1. **Configurar o Zed** (é a IDE do desenvolvimento todo), em sessão separada.
2. **Fase 1, o teste que decide tudo:** criar a integração no Internet Banking PJ, baixar certificado e chaves, tirar um token no **sandbox** e puxar o extrato. Se isso funciona, o resto é tela e regra de negócio.
3. Só então fechar **stack** e **escopo da v1**, e gerar o projeto a partir de `regras/templates/` do workspace.

## 8. Registro da conversa (01/11/2026)

Perguntas e respostas originais, para não perder nuance:

- **Onde roda:** web local no navegador.
- **Stack:** "temos que decidir isso com base no app em si, seria interessante eu te descrever a ideia melhor e com base nela definimos."
- **Escopo v1:** lançamentos de receita e despesa, contas e saldo, orçamento mensal por categoria, relatórios simples. E: "a ideia é que ele tenha uma integração com minha conta PJ do Inter, para consumir os dados da minha conta diretamente, ao invés de eu ficar importando relatórios de extrato."
- **O problema:** "não tenho controle nem visão de para onde meu dinheiro está indo, ele parece simplesmente evaporar."
- **Tela inicial:** saldo, gasto atual e gastos previstos.
- **Dados do Inter:** "acredito que tudo isso" (extrato, saldo, PF, cartão, Pix, boletos).
- **Sincronização:** sempre que abrir.
- **Uso:** principal no celular, web app para não publicar, usado só por ele e pela esposa.

## 9. Progresso no Zed (sessão de 01/11/2026)

O que saiu do papel:

- **Repositório privado:** https://github.com/viniciusAlarc/gestao-financeira
  - `main` com `.gitignore` (bloqueia `.env`, `*.pem`, `*.pfx`, `*.key`, `certs/`, `secrets/`) e `.gitattributes` (LF).
  - Ferramentas instaladas no usuário: `gh` 2.103.3 e Python 3.12.10 (sem admin).
  - Identidade git configurada **só no repositório**, com e-mail `noreply`.
- **Ambiente Python:** `.venv` no projeto com `requests` e `python-dotenv`; dependências em `requirements.txt`.
- **Script de teste:** `scripts/teste_inter.py` — autentica com mTLS, pega token, consulta saldo e extrato de 30 dias. Não grava nada em disco e não imprime segredo.

Ainda pendente nesta fase:

1. Criar a integração no Internet Banking PJ e baixar certificado e chaves (só o dono faz).
2. Converter para PEM, se vier `.pfx`, e preencher o `.env` a partir do `.env.example`.
3. Rodar o script contra o **sandbox** e conferir os endpoints. Os caminhos usados (`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`) vieram da documentação pública, mas **não foram verificados no ambiente real** — o portal do Inter é SPA e não entrega o detalhe por requisição simples.

Decisões D1 a D6 seguem em aberto. Python já está instalado, o que pesa a favor dele na D1, mas a stack não foi fechada.
