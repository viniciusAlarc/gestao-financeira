# gestao-financeira — Instruções do projeto

**Stack:** Django 5.2 · SQLite · templates + HTMX · PWA. Decidida em 2026-11-01 (D1).
Python 3.12 no `.venv` do projeto, no WSL (Ubuntu 24.04). Plano e fases em `docs-dev/a-codar/01-plano-desenvolvimento.md`.

> **Fonte das regras.** As regras universais e o perfil do dono moram em `~/Documents/IA`
> (`guardrails-ia/guardrails-core.md`, `cnr/como-trabalhamos.md` e `pessoal/sobre-mim.md`). A sessão
> aberta pelo Dev Valley carrega isso sozinha (perfil pessoal, `~/.claude-pessoal/CLAUDE.md`, que roda
> com o DeepSeek); o `CLAUDE.md` daqui só importa este arquivo. O que incide neste projeto está resumido
> abaixo, e este arquivo vence em conflito.

## O que este sistema é

Controle financeiro pessoal, privado, de duas pessoas (o dono e a esposa). Não é produto.
O problema não é registrar gasto, é **ver** para onde o dinheiro foi: responder sem esforço
"para onde foi o dinheiro deste mês" e "o que já está comprometido à frente".
Tela inicial: saldo, gasto atual, gastos previstos. As duas contas de login veem todos os dados
(conta conjunta); cada lançamento registra quem lançou em `criado_por`. Uso principal no celular,
como web app responsivo (PWA), sem publicar em loja.

## Estado atual

Desenvolvimento da v1 por fases (8 no plano). O esqueleto do Django roda, o modelo de dado está
pronto (`Conta`, `Categoria`, `Movimento`, `GastoFixo`, `Previsto`) e a tela inicial com saldo,
gasto do mês e previsto em aberto está pronta e verificada a 375, 360, 768 e 1280px. As fases 4 e 5 estão concluídas
e validadas por testes: gastos fixos mensais com botão "paguei" e relatório do mês por categoria. A
fase 6 está implementada: as duas contas veem tudo, o lançamento registra a autoria, há logout e o
PWA tem manifest e ícones; falta a verificação de uso real (P3-9). Em 2026-11-08 entraram as funções
de uso diário (data editável, editar/desfazer lançamento, ignorar/reabrir previsto e navegação
entre meses), o previsto virou **gasto fixo mensal** (cadastro único que gera o previsto de cada
mês; o avulso ficou secundário) e ganhou a **tela de categorias** (criar, editar e desativar; tipo
fixo depois de criada). A **UI/UX foi revista** em 2026-11-08: cabeçalho com marca, barra inferior
no celular, topo no desktop, layout mais espaçado, mensagens por tipo e tema do PWA claro. A fase 7
(integrar o banco) mudou de caminho em 2026-11-09: **o Inter foi descartado** (a API é exclusiva de
PJ e não atende MEI) e o caminho escolhido é a **Pluggy pelo Open Finance, uso pessoal gratuito**
(Meu Pluggy + conector 200). O código do Inter foi removido do projeto em 2026-11-09; o mapeamento
da API da Pluggy é o próximo passo (P2-12/P2-13). As migrations 0001 a 0005 estão aplicadas no
banco real. A suíte tem 163 testes passando. O lançamento
rápido aceita uma descrição opcional (2026-11-08), que a lista usa no lugar do nome da categoria. O que foi
feito fica em `PROGRESS.md`; o que está aberto, em `PENDENCIAS.md`.

## Documentos de referência — consultar antes de implementar

| Documento                                      | Quando consultar                                                |
| ---------------------------------------------- | --------------------------------------------------------------- |
| `PENDENCIAS.md`                                | **Antes de codar** — rastreador único do que está aberto (G6)   |
| `PROGRESS.md`                                  | Memória oficial: o que foi feito e quando (G5)                  |
| `docs-dev/a-codar/01-plano-desenvolvimento.md` | O plano e as fases da v1                                        |
| `docs-dev/a-codar/briefing-descoberta.md`      | Descoberta do produto, decisões D1–D6, perguntas em aberto (G7) |
| `docs-dev/guias/OPERACAO.md`                   | Como subir, derrubar e o que olhar quando não sobe (G14)        |
| `docs-dev/painel.json`                         | Fases e entregas do plano em andamento (G14)                    |

## Regras técnicas deste projeto — invioláveis

1. **Segredo não entra no repositório nem em documento (G13).** Certificado, chave, `client_id`
   e `client_secret` vivem só no `.env`, que o `.gitignore` bloqueia. Não imprimir valor em
   terminal, log, print ou resposta: referenciar o nome da variável.
2. **Dado financeiro é dado pessoal.** Extrato, saldo e transação não vão para serviço externo,
   IA de terceiro ou web sem decisão explícita do dono (G20). **Decisão do dono em 2026-11-09:** a
   Pluggy (Open Finance) é o provedor escolhido, em modo pessoal gratuito, somente leitura.
   **O assistente (DeepSeek, Claude) lê e escreve o código, nunca o dado real:** não abrir
   `db.sqlite3`, extrato, `.env` nem dump do banco, nem colar dado real em teste (decisão do dono,
   2026-11-01). Teste usa dado inventado.
3. **Ação irreversível espera o dono (G3).** Baixar e ativar certificado, criar integração no
   Internet Banking, conectar conta no provedor de Open Finance, mexer em servidor ou em banco:
   mostrar o comando e o efeito, e esperar o "pode".
4. **Não inventar endpoint nem campo (G1).** Os caminhos e campos da Pluggy seguem a documentação
   oficial (`docs.pluggy.ai`); rota ou campo fora da doc oficial é retrabalho, não iniciativa.
5. **Testes (G4).** Rodar `.venv/bin/python manage.py test` antes e depois de mexer no modelo.
   Linha de base em 2026-11-03: 62 testes; depois da limpeza do Inter, em 2026-11-09 a suíte está
   em 163, todos passando.
6. **Idioma:** conversa e documentação em pt-BR; código, nome de lib e termo técnico no original.
7. **Texto de interface:** só a primeira letra maiúscula ("Gastos previstos", não "Gastos Previstos").

## Como rodar

```bash
# na raiz do repositório, com o .venv do projeto
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 0.0.0.0:8000
.venv/bin/python manage.py createsuperuser     # uma vez, para o primeiro login
.venv/bin/python manage.py test               # suíte do modelo
```

Porta, `ALLOWED_HOSTS` e erros conhecidos: `docs-dev/guias/OPERACAO.md`. A `SECRET_KEY` vem do
`.env` (`DJANGO_SECRET_KEY`) ou de `.django-secret`, gerado no primeiro start e ignorado pelo git.
Nunca escrever chave no código (G13).

### Integração com o banco (fase 7)

O caminho é o **Pluggy em modo pessoal gratuito** (Meu Pluggy + conector 200), decidido em
2026-11-09. O mapeamento da API e os comandos de importação serão escritos na P2-13; até lá, não há
comando de importação no projeto.

### Importação (fase 7)

O mapeamento da Pluggy (extrato e saldo) e o comando de importação serão escritos na P2-13. A
idempotência continua sendo por `Movimento.id_externo`, agora com o id da transação da Pluggy.

## Onde este projeto roda (decidido em 2026-11-01, revisto no mesmo dia)

- **Só no WSL (Ubuntu 24.04)**, em `~/Documents/Projetos-pessoais/gestao-financeira`, codado pelo
  Dev Valley com o DeepSeek (perfil pessoal do Claude Code). A cópia antiga no Windows não é mais usada.
- O `.venv` é de Linux: comando de Python neste projeto é `.venv/bin/python ...`.
- O `.venv` foi criado sem pip (o WSL não tem o pacote `python3-venv`). Instalar dependência:
  `pip3 --python .venv/bin/python install -r requirements.txt`.

## Regras de processo

- **Fim de cada entrega:** `PROGRESS.md` atualizado na mesma resposta (G5); `PENDENCIAS.md` com
  o que abriu ou fechou (G6); `docs-dev/painel.json` só quando uma fase avança ou fecha (G14).
- **Fechamento (G11):** só declarar fase concluída depois de dizer item por item o que a doc
  pedia e o que foi feito. O que ficou para depois vai explícito, nunca em silêncio.
- **Outra sessão viva neste repositório (G21):** arquivo que mudou depois da minha leitura é
  trabalho dela — encaixar, nunca reverter.
