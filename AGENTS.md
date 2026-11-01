# gestao-financeira — Instruções do projeto

**Stack:** não fechada (decisão D1 em aberto). Hoje: Python 3.12 + `requests` + `python-dotenv`,
rodando no `.venv` do projeto. Sem banco, sem front, sem servidor.

> **Fonte das regras.** As regras universais e o perfil do dono moram em `~/Documents/IA`
> (do Windows: `\\wsl.localhost\Ubuntu-24.04\home\vinicius\Documents\IA`), em
> `guardrails-ia/guardrails-core.md`, `cnr/como-trabalhamos.md` e `pessoal/sobre-mim.md`.
> O Claude carrega isso sozinho por `~/.claude/CLAUDE.md`; **o Zed não**. Por isso o que incide
> neste projeto está resumido abaixo, e este arquivo vence em conflito.

## O que este sistema é

Controle financeiro pessoal, privado, de duas pessoas (o dono e a esposa). Não é produto.
O problema não é registrar gasto, é **ver** para onde o dinheiro foi: responder sem esforço
"para onde foi o dinheiro deste mês" e "o que já está comprometido à frente".
Tela inicial: saldo, gasto atual, gastos previstos. Uso principal no celular, como web app
responsivo (PWA), sem publicar em loja.

## Estado atual

Fase 1: provar a integração com a API do Inter (mTLS, token, saldo, extrato) no **sandbox**.
Nada de tela e nada de banco antes disso. O que foi feito fica em `PROGRESS.md`; o que está
aberto, em `PENDENCIAS.md`.

## Documentos de referência — consultar antes de implementar

| Documento                                 | Quando consultar                                                |
| ----------------------------------------- | --------------------------------------------------------------- |
| `PENDENCIAS.md`                           | **Antes de codar** — rastreador único do que está aberto (G6)   |
| `PROGRESS.md`                             | Memória oficial: o que foi feito e quando (G5)                  |
| `docs-dev/a-codar/briefing-descoberta.md` | Descoberta do produto, decisões D1–D6, perguntas em aberto (G7) |
| `docs-dev/painel.json`                    | Fases e entregas do plano em andamento (G14)                    |

## Regras técnicas deste projeto — invioláveis

1. **Segredo não entra no repositório nem em documento (G13).** Certificado, chave, `client_id`
   e `client_secret` vivem só no `.env`, que o `.gitignore` bloqueia. Não imprimir valor em
   terminal, log, print ou resposta: referenciar o nome da variável.
2. **Dado financeiro é dado pessoal.** Extrato, saldo e transação não vão para serviço externo,
   IA de terceiro ou web sem decisão explícita do dono (G20).
3. **Ação irreversível espera o dono (G3).** Baixar e ativar certificado, criar integração no
   Internet Banking, trocar `INTER_AMBIENTE` para `producao`, mexer em servidor ou em banco:
   mostrar o comando e o efeito, e esperar o "pode".
4. **Não inventar endpoint nem campo (G1).** Os caminhos usados em `scripts/teste_inter.py`
   (`/oauth/v2/token`, `/banking/v2/saldo`, `/banking/v2/extrato`) vieram da documentação
   pública e **nunca foram conferidos no ambiente real**. Rota ou campo fora da doc oficial é
   retrabalho, não iniciativa.
5. **Testes (G4).** Ainda não existe suíte. Linha de base hoje = `scripts/teste_inter.py` contra
   o sandbox. Sem suíte possível, dizer antes de mexer, não no fim.
6. **Idioma:** conversa e documentação em pt-BR; código, nome de lib e termo técnico no original.
7. **Texto de interface:** só a primeira letra maiúscula ("Gastos previstos", não "Gastos Previstos").

## Como rodar

```bash
# na raiz do repositório, com o .venv do projeto
.venv/Scripts/python scripts/teste_inter.py     # Windows (situação atual)
.venv/bin/python scripts/teste_inter.py         # se o repositório migrar para o WSL
```

O script exige `.env` preenchido a partir de `.env.example`. Sem certificado baixado ele para
pedindo as variáveis: isso é o esperado, não defeito.

## Onde este projeto roda (decidido em 2026-11-01)

- **Zed + Windows é o ambiente dos projetos pessoais.** Este repositório fica em
  `C:\Users\ViniciusAlarção\Documents\Projetos\gestao-financeira`, com `.venv` de Windows.
  Não é divergência nem dívida: é a escolha do dono.
- **WSL (Ubuntu 24.04) existe para o trabalho e para o Claude Code**, onde ficam os projetos da
  CNR e as regras de `~/Documents/IA`. Comando escrito para bash/WSL não roda aqui sem conferir
  o interpretador, e o inverso também não.
- Consequência prática: comando de Python neste projeto é `.venv/Scripts/python ...`.

## Regras de processo

- **Fim de cada entrega:** `PROGRESS.md` atualizado na mesma resposta (G5); `PENDENCIAS.md` com
  o que abriu ou fechou (G6); `docs-dev/painel.json` só quando uma fase avança ou fecha (G14).
- **Fechamento (G11):** só declarar fase concluída depois de dizer item por item o que a doc
  pedia e o que foi feito. O que ficou para depois vai explícito, nunca em silêncio.
- **Outra sessão viva neste repositório (G21):** arquivo que mudou depois da minha leitura é
  trabalho dela — encaixar, nunca reverter.
