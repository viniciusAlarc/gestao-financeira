# S1 — Importador do Inter (núcleo, sem credencial)

> Rodada 2026-11-05-b, tarefa T1. Execução em 2026-11-08.
> Núcleo da importação: transforma um JSON do `/extrato/completo` em `Movimento`, de forma
> idempotente, com `--dry-run`. **Nenhuma chamada à API e nenhuma credencial usada.**

## O que foi feito

1. `financas/importacao_inter.py` — serviço `importar_extrato(transacoes, conta, usuario=None,
   dry_run=False)`, com um relatório (`RelatorioImportacao`) de `criados`, `pulados` e `erros`.
   Cada transação ruim é recusada **e reportada**: as demais seguem, a importação não cai inteira.
2. `financas/management/commands/importar_inter.py` — comando `importar_inter` com `--arquivo`
   (JSON), `--conta` (nome exato) e `--dry-run`. Imprime o resumo e sai com código 1 quando há
   erro (via `CommandError`).
3. `financas/management/__init__.py` e `financas/management/commands/__init__.py` — pastas novas.
4. `financas/test_importacao.py` — 26 testes com payload inventado.
5. Este relatório.

## Como o mapeamento ficou

| Campo do `Movimento` | Regra implementada |
|---|---|
| `data` | `dataTransacao`; se vazia, `dataInclusao`. Data presente mas inválida é **erro**, não cai para o outro campo (cair mascararia formato inesperado). |
| `valor` | `Decimal` positivo com 2 casas (aceita vírgula e milhar `1.234,56`); o sinal vem de `tipoOperacao`. Zero, negativo impossível ou texto é erro da transação. |
| `tipo` | `tipoOperacao` `D` = despesa, `C` = receita; qualquer outro valor é erro reportado. |
| `conta` | A recebida por parâmetro. |
| `origem` | `inter`. |
| `id_externo` | `idTransacao`; transação sem id é **recusada e reportada** (sem chave composta de reserva). |
| `categoria` | `INVESTIMENTO` → "Investimento" (despesa, `entra_no_gasto=False`); `ESTORNO` → "Estorno"; `CASHBACK` → "Cashback", com o tipo da transação; o resto → "Não categorizado" do tipo. Criadas por `get_or_create`. |
| `descricao` | `titulo` + `descricao` separados por espaço, truncada em 120. |
| `criado_por` | Usuário técnico `Inter` (`set_unusable_password()`, sem staff/superuser) ou o `usuario` informado. |

**Idempotência:** pula o par `(conta, id_externo)` que já existe e a duplicata dentro do próprio
payload. A restrição única do banco continua sendo a última linha de defesa (a gravação roda em
`atomic` e um `IntegrityError` vira "pulado", não derruba a importação).

**`--dry-run`:** não grava movimento, não cria categoria e não cria usuário. Lê o banco só para
saber o que seria pulado e devolve o que *seria* criado no relatório.

## Entrada do comando

O arquivo pode ser o corpo do `/extrato/completo` (objeto com a chave `transacoes`) ou a lista de
transações direto. A chave `transacoes` é a mesma que `scripts/teste_inter.py` já lê do extrato
simples, então não é campo novo inventado. Um JSON com outro formato termina com erro claro.

## Testes

| Momento | Comando | Resultado |
|---|---|---|
| Antes de mexer (linha de base) | `.venv/bin/python manage.py test` | **68 testes, OK** |
| Só o importador | `.venv/bin/python manage.py test financas.test_importacao` | **26 testes, OK** |
| Depois, suíte completa | `.venv/bin/python manage.py test` | **116 testes, OK** |

Os 116 são 68 da linha de base + 26 novos + 22 que as outras sessões da rodada acrescentaram
(encontrados verdes no mesmo comando). `manage.py check` sem problemas; `importar_inter --help`
lista os três argumentos.

### Evidência do aceite

- **`--dry-run` não grava:** `test_dry_run_nao_grava_movimento_categoria_nem_usuario` confere
  `Movimento`, `Categoria` e usuário `Inter` zerados depois da simulação, inclusive com
  INVESTIMENTO e ESTORNO no payload (que criariam categoria no modo real). O teste do comando
  repete a conferência pelo `call_command(..., dry_run=True)`.
- **Duas importações, um movimento:** `test_importar_duas_vezes_deixa_um_movimento_por_id_transacao`
  importa o mesmo payload duas vezes e confere 1 movimento, 0 criados e 1 pulado na segunda.
- **Idempotência por conta:** mesmo `idTransacao` em outra conta é importado normalmente
  (a restrição é por conta, como no modelo).
- **Recusas reportadas:** sem `idTransacao`, `tipoOperacao` fora de D/C, data inválida e valor
  inválido/zerado viram `erro` no relatório, e a transação boa do mesmo lote entra.
- **Usuário técnico:** `has_usable_password()` é `False`, `is_staff` e `is_superuser` são `False`.
- **Comando:** arquivo inexistente, conta inexistente e transação inválida terminam com
  `CommandError` (código 1 no terminal); as transações válidas do mesmo arquivo já foram gravadas.

## O que ficou de fora (e por quê)

- **Chamar a API / usar certificado:** a fase continua bloqueada por P2-1/P2-2 e pelo diagnóstico
  P2-3. O comando lê um JSON já salvo; buscar o extrato é outro passo.
- **Sinal do `valor` e estabilidade do `idTransacao`:** a documentação não descreve; o código segue
  a regra decidida e o sandbox confirma. Se o extrato vier com valor já sinalizado, `abs()` evita
  valor negativo — mas isso só se prova com dado real.
- **Data de corte da primeira importação:** a decisão P2-8 ("começa na data da execução") pertence
  ao passo que busca o extrato, não a este importador; aqui entra o que o JSON trouxer.
- **Saldo inicial / conciliação:** ajuste único do `saldo_inicial` no dia da ativação (P2-8), fora
  do escopo desta tarefa.
- **Investimento com `tipoOperacao=C` (resgate):** a decisão diz "Investimento (despesa, fora do
  gasto)" e foi seguida ao pé da letra — mesmo um resgate `C` usa a categoria "Investimento" de
  despesa, com movimento de receita. O sandbox dirá se esse caso aparece; se aparecer com
  frequência, a decisão merece revisão do dono.
- **Descrição com separador:** `titulo` e `descricao` são unidos por espaço. A decisão não fixa o
  separador; mudar é uma linha em `_montar_descricao`.
- **`PROGRESS.md` / `PENDENCIAS.md` / `painel.json`:** não editados, conforme a regra 3 da rodada
  (o coordenador consolida). Nada de migration, banco real, commit ou servidor.

## Arquivos tocados

- `financas/importacao_inter.py` (novo)
- `financas/management/__init__.py` (novo)
- `financas/management/commands/__init__.py` (novo)
- `financas/management/commands/importar_inter.py` (novo)
- `financas/test_importacao.py` (novo)
- `docs-dev/rodada-2026-11-05-b/s1-importador.md` (este)
