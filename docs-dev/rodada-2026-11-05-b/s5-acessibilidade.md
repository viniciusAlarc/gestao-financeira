# S5 · T5 — acessibilidade e teclado nas telas

Rodada 2026-11-05-b · sessão t5 · executada em 8 de novembro de 2026.
Banco descartável (`config.settings_visual`), servidor na porta 8010; o `db.sqlite3` real
**não foi aberto**.

## Veredito

| Item | Antes | Depois |
| --- | --- | --- |
| Link ativo | `class="ativo"` só visual | `aria-current="page"` no link da tela atual, e só nele |
| Erro de campo | `<p class="erro">` solto, sem referência | `id="id_<campo>_error"` e `role="alert"`; input com `aria-invalid="true"` e `aria-describedby` apontando para o aviso |
| Login inválido | mensagem solta | `id="erro-login"`, `role="alert"`, os dois campos com `aria-describedby` e `aria-invalid` |
| Lista de mensagens | `<ul>` sem papel | `role="status"` |
| Foco de teclado | só o padrão do navegador | anel `2px solid #18181b` com `2px` de afastamento em links, botões e campos |
| Botões "Paguei" | seis botões com o mesmo nome acessível ("Paguei") | `aria-label="Paguei: <descrição>"`, um nome por previsto |

## O que mudou, arquivo por arquivo

- **`templates/base.html`** — `aria-current="page"` acompanha a classe `ativo` dos quatro links;
  `<ul class="mensagens">` virou `role="status"`.
- **`templates/login.html`** — erro com `id="erro-login"` e `role="alert"`; usuário e senha
  ganham `aria-invalid="true"` e `aria-describedby="erro-login"` quando o formulário tem erro.
- **`templates/lancamentos.html`** — cada `<p class="erro">` de campo ganhou
  `id="{{ form.<campo>.auto_id }}_error"` e `role="alert"`; o erro geral do formulário também
  ganhou `role="alert"`.
- **`templates/previstos.html`** — mesma correção nos quatro campos (descrição, vencimento,
  valor, categoria); o botão "Paguei" ganhou `aria-label` com a descrição do previsto.
- **`templates/relatorio.html` e `templates/inicio.html`** — sem mudança: não têm formulário nem
  controle próprio; a navegação vem do `base.html` e o foco da folha de estilo, e a medição
  cobre as duas telas.
- **`financas/static/financas/app.css`** — regra de `:focus-visible` para `a`, `button`,
  `input`, `select` e `textarea`; regra de `input[type="date"]:focus-within` para o seletor
  interno do Chrome. Só acréscimo no fim do arquivo, nenhum estilo existente mudou (G19).
- **`financas/test_acessibilidade.py`** (novo) — 6 testes.

**Detalhe de implementação:** o Django 5.2 já emite `aria-invalid="true"` e
`aria-describedby="<auto_id>_error"` no widget quando o campo tem erro
(`BoundField.build_widget_attrs`). O template só precisava dar ao `<p class="erro">` o `id` que
essa referência espera e o `role="alert"`. Por isso os inputs continuam renderizados por
`{{ form.<campo> }}` e nenhum `forms.py`/`views.py` foi tocado.

## Testes

- **Linha de base no início desta sessão:** `.venv/bin/python manage.py test` → **68 testes,
  OK**.
- **Depois:** `.venv/bin/python manage.py test` → **125 testes, OK**. O salto de 68 para 125
  inclui os testes que as outras sessões da rodada criaram em paralelo (T1, T2, T3); o T5
  contribui com **6** (o recorte `financas.test_acessibilidade` roda 6/6). Nenhuma falha nova.
- **Os 6 testes do T5:** link ativo com `aria-current` e só um; POST inválido de lançamento
  ligando valor ao erro; POST inválido de previsto ligando cada campo ao próprio erro (e sem
  marcar os campos válidos); login inválido ligando os dois campos; mensagem de sucesso dentro
  da região `role="status"`; e presença das regras de foco no CSS.

## Verificação a 375 e 360 px

Feita com Edge headless por CDP, com emulação real de viewport, no banco descartável
(`config.settings_visual`), nas quatro telas autenticadas.

| Largura | Tela | scrollWidth / clientWidth | Alvos < 44px | Elementos fora da borda | Paradas de Tab |
| --- | --- | --- | --- | --- | --- |
| 375 | Início | 375 / 375 | 0 | 0 | 5 |
| 375 | Lançamentos | 375 / 375 | 0 | 0 | 8 |
| 375 | Previstos | 375 / 375 | 0 | 0 | 17 |
| 375 | Relatório | 375 / 375 | 0 | 0 | 5 |
| 360 | Início | 360 / 360 | 0 | 0 | 5 |
| 360 | Lançamentos | 360 / 360 | 0 | 0 | 8 |
| 360 | Previstos | 360 / 360 | 0 | 0 | 17 |
| 360 | Relatório | 360 / 360 | 0 | 0 | 5 |

- **Rolagem horizontal:** zero em todas as telas e larguras (`scrollWidth = clientWidth`).
- **Alvos de toque:** os 5/8/16/5 controles visíveis de cada tela medem ≥ 44px nos dois lados
  (o P4-5 continua valendo).
- **Foco por Tab:** todas as paradas recebem `outline: 2px solid rgb(24, 24, 27)` com
  `outline-offset: 2px`, inclusive o botão escuro ("Salvar", "Adicionar previsto", "Paguei").
  Em `/previstos/` são **17 paradas para 16 controles**: o `<input type="date">` do Chrome tem
  uma parada interna (o seletor de data) que não casa `:focus-visible`; ela recebe o anel pela
  regra de `:focus-within` criada por causa desse teste. Sem ela, essa parada ficava sem anel.
- **Estado de erro (375):** POST com valor `abc` devolve `role="alert"`,
  `aria-invalid="true"`, `aria-describedby="id_valor_error"` e o id existe no documento
  ("Informe um número.").
- **Mensagem de sucesso:** a lista aparece com `role="status"` e o texto do lançamento.

## O que não foi possível verificar

1. **Leitor de tela de verdade (NVDA/VoiceOver).** Não há leitor instalado no WSL. Verifiquei o
   HTML que o servidor entrega e o que o navegador calcula (`role`, `aria-*`, foco e anel); a
   locução real fica para a verificação de uso (P3-9), se o dono quiser.
2. **Tela de login no navegador.** O `settings_visual` entra logado por middleware e o
   `LoginView` redireciona usuário autenticado, então `/login/` não abre nessa configuração. O
   HTML do login é coberto pelos testes (os dois campos ligados ao erro) e a mudança não afeta
   layout.
3. **Anúncio da `role="status"` após redirecionamento.** A região existe e o texto está nela;
   se o leitor anuncia ao carregar a página nova depende do leitor, não do HTML.
4. **Aparelho físico a 360px.** A medição é por emulação de viewport, não em celular real.

## Evidência

- `/tmp/gestao-visual/t5-medicoes.json` — medidas de todas as telas nas duas larguras, foco,
  erro e mensagem.
- `/tmp/gestao-visual/t5-{375,360}-{inicio,lancamentos,previstos,relatorio}.png` e
  `/tmp/gestao-visual/t5-375-lancamentos-erro.png` — capturas de página inteira.
- Para abrir pelo Windows: `\\wsl.localhost\Ubuntu-24.04\tmp\gestao-visual\`.
- `captura.mjs` foi **recriado nesta rodada** (o da rodada anterior sumiu no reinício do WSL) e
  fica em `/tmp/gestao-visual/captura.mjs`, fora do git.

## O que ficou de fora e por quê

- Nada do escopo do T5 ficou sem fazer.
- O `/tmp/gestao-visual/db.sqlite3` ganhou **um movimento inventado** no teste de mensagem de
  sucesso (R$ 12,34, "Cartão de crédito parcelado"). É o banco descartável do P4-6; o banco real
  não foi tocado.
- `views.py`, `models.py`, `settings.py`, `financas/tests.py` e `config/settings_visual.py` não
  foram editados, conforme o briefing.
