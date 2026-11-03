# Plano de desenvolvimento da v1

> Documento do plano (G7 e G14). A fonte do que está aberto continua sendo `PENDENCIAS.md`; as
> fases e o andamento ficam em `docs-dev/painel.json`. Escrito em 2026-11-01.
> **Pressuposto deste plano:** a integração com a conta PJ do Inter não entra no caminho crítico.
> O app funciona com lançamento manual e o Inter entra depois, como alimentador de dados.

## 1. O que a v1 precisa entregar

Uma pergunta respondida sem esforço, no celular: **para onde foi o dinheiro deste mês e o que já
está comprometido à frente**. Isso exige quatro peças de dado e três números na tela.

| Peça | Para quê |
|---|---|
| Conta | saber quanto tem hoje (saldo) |
| Categoria | saber para onde foi |
| Movimento (receita/despesa) | gasto atual |
| Previsto (conta com vencimento) | comprometido à frente |

**Fora da v1, explicitamente:** cartão de crédito, orçamento por categoria, Open Finance, conta PF,
notificação, multi-tenant, login social, importação de OFX/CSV.

## 2. Fase 0 — As quatro decisões que travam o modelo

Nada de código antes disso, porque cada uma muda a tabela.

| # | Decisão | Recomendação | Por quê |
|---|---|---|---|
| D1 | Stack | **Django 5 + SQLite + templates + HTMX + PWA** | ORM, migrations, auth e admin já vêm prontos; é Python, que é o seu forte; uma pessoa só mantém isso. Alternativas na seção 6 |
| D2 | O que é "gasto previsto" | **Conta a pagar com vencimento**, recorrente entra depois | É o que responde "o que está comprometido à frente" com o menor modelo possível |
| D3 | Categorização | **Manual, lista curta e fechada** | Regra por descrição só depois de 2 meses de uso real, com dado para basear a regra |
| D5 | Duas pessoas | **Duas contas de login, sem papéis**, as duas lançam | Sem papel, sem permissão, sem tela de admin de usuário |
| D6 | Onde roda | **Só na rede de casa na v1** | Zero custo, zero exposição; sair de casa é fase 8 e tem decisão de custo (G20) |

## 3. As fases

Cada fase entrega algo que você consegue **usar e olhar**, não uma camada de código.

### Fase 1 — Esqueleto que roda (pequena)

- Projeto Django, app `financas`, SQLite, `SECRET_KEY` e senha vindo do `.env`.
- Modelos: `Conta`, `Categoria`, `Movimento`, `Previsto`.
- Django admin habilitado como tela provisória.
- **Verificação:** cadastrar 1 conta, 3 categorias e 5 movimentos pelo admin, e conferir que o
  banco tem exatamente isso.
- **Não entra:** tela bonita, PWA, login de terceiros.

### Fase 2 — Os três números no celular (média)

- Tela inicial: saldo, gasto do mês, previsto em aberto.
- Layout mobile-first, primeira letra maiúscula nos rótulos.
- **Verificação:** abrir no navegador a 375px de largura e conferir que os três números batem com
  o que foi lançado na fase 1.
- **Regra de conta:** saldo = soma dos saldos iniciais + receitas − despesas. Nunca guardar saldo
  como campo escrito à mão; ele é calculado.

### Fase 3 — Lançar em 3 toques (média)

- Formulário rápido: valor, categoria, salvar. Data padrão é hoje.
- Lista do mês corrente, agrupada por dia, com total.
- **Verificação:** lançar 5 gastos reais do dia sem tocar no admin.
- **Não entra:** anexo, observação longa, edição em massa.

### Fase 4 — Gastos previstos (média)

- Criar previsto com vencimento, valor, categoria.
- Botão "paguei": gera o movimento e marca o previsto como pago.
- **Verificação:** um previsto pago sai do total de previstos e aparece no gasto do mês. Um
  previsto com vencimento no mês futuro não entra no gasto do mês corrente.

### Fase 5 — Para onde foi (média)

- Relatório do mês: total por categoria, com percentual e ordem decrescente.
- **Verificação:** a soma das categorias tem que fechar exatamente com o total de despesas do mês.

### Fase 6 — Uso real a dois (pequena)

- Segundo login para a esposa, dados separados por pessoa no lançamento.
- PWA instalável: `manifest.json`, ícone, `display: standalone`.
- **Verificação:** uma semana de uso real, com os dois lançando.
- **Decisão que volta aqui:** escopo por pessoa (cada um vê tudo?) precisa de resposta antes.

### Fase 7 — Inter (em andamento desde 2026-11-03)

- Host do sandbox confirmado em `cdpj-sandbox.partners.uatinter.co`; criar a integração no portal e
  baixar o certificado (P2-1/P2-2).
- Importar extrato como `Movimento` com `origem = inter`, sem duplicar.
- **Verificação:** um extrato importado duas vezes não gera movimento repetido.
- **Começa** quando o portal estiver na janela e a integração/certificado estiverem prontos.

### Fase 8 — Sair de casa (opcional, tem custo)

- Túnel ou VPS, com número de custo na mesa antes de criar (G20).
- Só entra se a fase 6 mostrar que a limitação de "só em casa" incomoda de verdade.

## 4. Modelo de dado proposto

Nomes em português, porque o domínio é seu, não genérico.

```text
Conta        nome, tipo[carteira|corrente], saldo_inicial, ativa
Categoria    nome, tipo[receita|despesa], ativa
Movimento    data, valor, tipo[receita|despesa], conta, categoria,
             descricao, origem[manual|inter], criado_por
Previsto     descricao, valor, vencimento, tipo, categoria, conta,
             status[aberto|pago|ignorado], movimento(pago)
```

Regras de dinheiro: `Decimal` com 2 casas, nunca `float`. Valor sempre positivo, com o sinal vindo
do `tipo`. Nada de exclusão física de movimento.

## 5. Gate de fechamento de cada fase (G11)

Só declarar fase concluída com quatro respostas dadas:

1. O que esta fase pedia e o que foi feito, item por item.
2. O que ficou de fora e onde foi registrado.
3. Qual foi a verificação e o resultado real.
4. Testes rodados, ou a declaração explícita de que não existe suíte ainda.

## 6. Alternativas de stack, se o D1 não fechar em Django

| Opção | A favor | Contra |
|---|---|---|
| **Django** (recomendada) | admin e auth prontos, migrations, um projeto só | menos "moderninho", templates no lugar de SPA |
| FastAPI + Jinja + HTMX | mais leve, você controla tudo | auth, admin e migrations viram trabalho seu |
| FastAPI + React | separação front/back, mercado | três peças para manter sozinho, e o ganho é zero para 2 usuários |

## 7. Ordem de grandeza

Fases 1 a 5 são o produto mínimo útil. Somadas, são algumas sessões de trabalho, não meses, e a
partir da fase 2 já dá para usar no dia a dia com o que estiver pronto.
