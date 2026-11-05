# Decisão D4 e P2-8 — escopo e mapeamento da importação do Inter

> **Estado: fechadas pelo dono em 2026-11-05.** O modelo e os filtros mínimos já foram codados
> nesta data; a importação em si continua bloqueada por credencial (P2-1/P2-2) e pelo diagnóstico
> no sandbox (P2-3). Decisões registradas aqui, não em conversa solta (G7).

## 1. D4 — o que a v1 lê

| Entra na v1 | Por quê |
|---|---|
| Saldo e extrato da **conta corrente PJ (MEI)** do Inter | É o que a API Banking entrega; a conta já existe no app |
| Permissão **`extrato.read`** | Menor privilégio possível para importar; nada de pagamento |

| Fica fora da v1 | Motivo |
|---|---|
| Conta PF | A API direta é exclusiva de PJ; PF só por Open Finance |
| Cartão de crédito | Não há API de cartão; Open Finance é outro caminho |
| Boletos a pagar / de outra titularidade | A API não lista contas a pagar |
| Investimentos (posição) | Não há endpoint de posição; o movimento aparece no extrato |
| Pagamentos, Pix, DARF, Cobrança | Não é preciso para importar e amplia o risco |
| Open Finance | Exige instituição receptora autorizada pelo Banco Central |
| `Previsto` automático | O Inter não expõe contas a pagar; continua manual |

Base: `03-decisao-d4-escopo-inter.md` (fontes oficiais consultadas em 2026-11-05).

## 2. P2-8 — mapeamento da importação

| Item | Decisão de 2026-11-05 |
|---|---|
| **Conta de destino** | A conta existente no app, nome `69 450 604 Vinicius Di Franca Alarc`. Ela já tem alguns lançamentos manuais de Pix. |
| **Data do movimento** | `dataTransacao` (quando o dinheiro se moveu); se vier nula, `dataInclusao`. |
| **Categoria** | "Não categorizado" (uma de despesa, uma de receita), criadas pelo importador; classificação manual depois (D3). |
| **Antiduplicidade** | `idTransacao` do extrato enriquecido, gravado em `Movimento.id_externo`; restrição única por conta. |
| **Autoria (`criado_por`)** | Usuário técnico `Inter`, sem senha utilizável. O histórico não atribui a importação a uma pessoa. |
| **Investimentos, estornos e cashback** | Importar com categoria própria ("Investimento", "Estorno", "Cashback"). "Investimento" nasce com `entra_no_gasto=False`. |
| **Saldo** | O saldo do app continua somando o investimento; só o "gasto do mês" e o relatório o excluem. Na ativação, o `saldo_inicial` da conta é ajustado uma vez para o saldo do app bater com o `/saldo` do Inter; como os lançamentos manuais são poucos e parciais, esse ajuste é o que ancora o histórico. |
| **Ponto de partida** | A primeira importação começa na data da primeira execução, para não duplicar os Pix manuais que já estão na conta. Daí em diante, ninguém lança à mão nessa conta. Importar histórico anterior é decisão separada e exige reconciliar os manuais. |
| **Permissão** | Só `extrato.read` na criação da integração (P2-1). |

## 3. O que já foi codado nesta data

- `Movimento.id_externo` (nulo em lançamento manual) e restrição única
  `(conta, id_externo)` — migration `0003`.
- `Categoria.entra_no_gasto` (padrão `True`).
- Tela inicial: "Gasto do mês" filtra `categoria__entra_no_gasto=True`.
- Relatório: mesma regra; o rodapé passou a dizer "Total de gastos do mês" (antes "despesas",
  que ficaria impreciso com o investimento fora).
- Admin: `entra_no_gasto` visível e filtrável em Categoria; `id_externo` fora do formulário.
- Testes: 62 → **68**, todos passando. Cobertura nova: categoria fora do gasto (tela inicial e
  relatório) e unicidade do `id_externo` por conta.

**Não aplicado no banco real:** a migration `0003` está escrita e testada no banco de teste, mas
`manage.py migrate` espera o "pode" do dono (G3). O comando é:

```bash
.venv/bin/python manage.py migrate
```

## 4. O que falta para importar de verdade

1. Aplicar a migration `0003` e criar as categorias padrão (P2-10).
2. Criar a integração e o certificado (P2-1/P2-2) e rodar o diagnóstico (P2-3).
3. Confirmar no sandbox o que a documentação não diz: sinal do `valor`, `idTransacao` sempre
   preenchido e estável, e o significado de `dataTransacao`/`dataInclusao`.
4. Escrever o importador usando `/extrato/completo`, idempotente pela chave externa.
5. No dia da ativação, ajustar o `saldo_inicial` da conta para o saldo do app bater com o `/saldo`
   do Inter e registrar no `PROGRESS.md` a data de corte da primeira importação.

## 5. Consequências

- O "gasto do mês" e o relatório deixam de somar investimento; o saldo continua somando.
- A tela de lançamentos continua listando o investimento e o total dela é o de **despesas**
  (inclui investimento). É um total diferente do "gasto" por definição, não um defeito.
- Enquanto o importador não existe, nada muda no uso atual: a flag só age quando uma categoria
  for marcada como fora do gasto.
