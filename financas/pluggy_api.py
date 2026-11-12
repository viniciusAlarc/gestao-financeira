"""Cliente HTTP da API da Pluggy (fase 7, P2-13).

Só transporte: autenticação, leitura de contas e de transações, paginação e erros.
A conversão para `Movimento` fica em `importacao_pluggy.py`, para o mapeamento poder
ser testado sem rede.

Caminhos e campos seguem a documentação oficial (`docs.pluggy.ai`), conferida em
2026-11-09:

- `POST /auth` com `{"clientId": ..., "clientSecret": ...}` devolve `{"apiKey": ...}`;
  a chave vale 2 horas e vai no cabeçalho `X-API-KEY` das chamadas seguintes.
- `GET /accounts?itemId=<uuid>` devolve `{page, total, totalPages, results}`; cada
  conta traz `id`, `type` (`BANK`/`CREDIT`), `subtype`, `name`, `number`, `balance`,
  `currencyCode` e `itemId`.
- `GET /v2/transactions?accountId=<uuid>` devolve `{results, next}` (paginação por
  cursor); cada transação traz `id`, `description`, `descriptionRaw`, `amount`,
  `date`, `type` (`DEBIT`/`CREDIT`), `status` (`PENDING`/`POSTED`), `currencyCode`
  e `category`. O filtro por data usa `dateFrom`/`dateTo` (inclusivos, sobre a data
  da transação); `next` é a query string pronta da página seguinte.

O módulo não importa Django e não grava nada. Segredo (G13): as variáveis
`PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET` vêm do `.env` e nunca aparecem em
mensagem de erro, log ou relatório.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs

import requests

URL_BASE = "https://api.pluggy.ai"

# A API aceita até 500 por página e responde 400 acima disso.
TAMANHO_PAGINA = 500
LIMITE_PAGINAS = 200  # trava de segurança contra paginação que não avança
SEGUNDOS_DE_TIMEOUT = 30

# A chave vale 2 horas; renovamos um pouco antes para não usar uma chave vencida
# numa chamada que já estava em voo.
VALIDADE_DA_CHAVE = timedelta(hours=1, minutes=50)


class ErroPluggy(Exception):
    """Falha ao falar com a Pluggy: status HTTP e mensagem da API, sem segredo."""

    def __init__(self, mensagem, status=None, detalhe=None):
        self.status = status
        self.detalhe = detalhe
        texto = mensagem
        if status is not None:
            texto = f"HTTP {status}: {texto}"
        if detalhe:
            texto = f"{texto} ({detalhe})"
        super().__init__(texto)


class ErroConfiguracaoPluggy(ErroPluggy):
    """Falta `PLUGGY_CLIENT_ID`/`PLUGGY_CLIENT_SECRET` no ambiente."""


class PluggyCliente:
    """Cliente mínimo da API: `/auth`, `/accounts` e `/transactions`.

    `sessao` existe para os testes trocarem o `requests` por um dublê e para o
    importador reaproveitar conexão; em produção fica a sessão padrão.
    """

    def __init__(self, client_id=None, client_secret=None, url_base=URL_BASE, sessao=None):
        self.client_id = client_id if client_id is not None else os.getenv("PLUGGY_CLIENT_ID", "")
        self.client_secret = (
            client_secret if client_secret is not None else os.getenv("PLUGGY_CLIENT_SECRET", "")
        )
        self.url_base = url_base.rstrip("/")
        self.sessao = sessao if sessao is not None else requests.Session()
        self._api_key = None
        self._valida_ate = None

    # --- autenticação -------------------------------------------------------

    def api_key(self):
        """Devolve a chave, pedindo uma nova quando não existe ou está perto de vencer."""
        agora = datetime.now(timezone.utc)
        if self._api_key and self._valida_ate and agora < self._valida_ate:
            return self._api_key

        if not self.client_id or not self.client_secret:
            raise ErroConfiguracaoPluggy(
                "PLUGGY_CLIENT_ID e PLUGGY_CLIENT_SECRET precisam estar no .env "
                "(ver .env.example)"
            )

        resposta = self._pedir(
            "POST",
            "/auth",
            json={"clientId": self.client_id, "clientSecret": self.client_secret},
            autenticado=False,
        )
        api_key = resposta.get("apiKey")
        if not isinstance(api_key, str) or not api_key:
            raise ErroPluggy("resposta do /auth sem apiKey")
        self._api_key = api_key
        self._valida_ate = agora + VALIDADE_DA_CHAVE
        return api_key

    # --- leitura -----------------------------------------------------------

    def contas(self, item_id=None):
        """Todas as contas do item, percorrendo as páginas.

        `item_id` é a conexão criada no Meu Pluggy; sem ele, a Pluggy não sabe de
        qual instituição ler. Padrão: `PLUGGY_ITEM_ID` do ambiente.
        """
        item_id = item_id or os.getenv("PLUGGY_ITEM_ID", "")
        if not item_id:
            raise ErroConfiguracaoPluggy(
                "PLUGGY_ITEM_ID precisa estar no .env para ler as contas "
                "(id da conexão no Meu Pluggy)"
            )
        return self._listar_paginado("/accounts", {"itemId": item_id})

    def transacoes(self, account_id, desde=None, ate=None):
        """Todas as transações da conta, percorrendo as páginas por cursor.

        `desde` e `ate` são `date`; a API filtra por `dateFrom`/`dateTo`
        (inclusivos) no formato `AAAA-MM-DD`. Sem eles, vêm todas as transações
        disponíveis para a conta.
        """
        if not account_id:
            raise ErroPluggy("conta da Pluggy sem id; não há como ler transações")
        parametros = {"accountId": account_id}
        if desde is not None:
            parametros["dateFrom"] = _data_iso(desde)
        if ate is not None:
            parametros["dateTo"] = _data_iso(ate)
        return self._listar_por_cursor("/v2/transactions", parametros)

    # --- HTTP --------------------------------------------------------------

    def _listar_paginado(self, caminho, parametros):
        """Percorre `page` de 1 até `totalPages`, juntando `results`."""
        itens = []
        pagina = 1
        while pagina <= LIMITE_PAGINAS:
            resposta = self._pedir(
                "GET",
                caminho,
                params={**parametros, "page": pagina, "pageSize": TAMANHO_PAGINA},
            )
            resultados = resposta.get("results")
            if not isinstance(resultados, list):
                raise ErroPluggy(f"resposta de {caminho} sem a lista 'results'")
            itens.extend(resultados)

            total_paginas = resposta.get("totalPages")
            if not isinstance(total_paginas, int) or pagina >= total_paginas:
                return itens
            pagina += 1
        raise ErroPluggy(
            f"{caminho}: paginação passou de {LIMITE_PAGINAS} páginas; "
            "os parâmetros de filtro podem estar sendo ignorados"
        )

    def _listar_por_cursor(self, caminho, parametros):
        """Percorre `next` até a última página, juntando `results`.

        O `next` devolvido pela API já é a query string completa da página
        seguinte (com `after`); a documentação manda usar o valor dele, não
        remontar o cursor.
        """
        itens = []
        atuais = dict(parametros)
        for _ in range(LIMITE_PAGINAS):
            resposta = self._pedir("GET", caminho, params=atuais)
            resultados = resposta.get("results")
            if not isinstance(resultados, list):
                raise ErroPluggy(f"resposta de {caminho} sem a lista 'results'")
            itens.extend(resultados)

            proximo = resposta.get("next")
            if not proximo:
                return itens
            atuais = _parametros_do_proximo(proximo)
        raise ErroPluggy(
            f"{caminho}: paginação por cursor passou de {LIMITE_PAGINAS} páginas"
        )

    def _pedir(self, metodo, caminho, params=None, json=None, autenticado=True):
        url = f"{self.url_base}{caminho}"
        cabecalhos = {"Content-Type": "application/json"}
        if autenticado:
            cabecalhos["X-API-KEY"] = self.api_key()

        try:
            resposta = self.sessao.request(
                metodo, url, params=params, json=json, headers=cabecalhos,
                timeout=SEGUNDOS_DE_TIMEOUT,
            )
        except requests.RequestException as erro:
            raise ErroPluggy(f"falha de rede em {caminho}: {erro}") from erro

        if resposta.status_code >= 400:
            raise ErroPluggy(
                f"erro em {caminho}",
                status=resposta.status_code,
                detalhe=_detalhe_do_erro(resposta),
            )
        try:
            return resposta.json()
        except ValueError as erro:
            raise ErroPluggy(f"resposta de {caminho} não é JSON válido") from erro


def _data_iso(valor: date) -> str:
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    return valor.isoformat()


def _parametros_do_proximo(proximo: str) -> dict:
    """Converte o `?a=1&b=2` do campo `next` nos parâmetros da chamada seguinte."""
    consulta = proximo[1:] if proximo.startswith("?") else proximo
    return {chave: valores[0] for chave, valores in parse_qs(consulta).items()}


def _detalhe_do_erro(resposta) -> str:
    """Mensagem da API quando ela vier em JSON; nunca inclui o corpo inteiro."""
    try:
        corpo = resposta.json()
    except ValueError:
        return ""
    if isinstance(corpo, dict):
        for campo in ("message", "error", "detail"):
            if corpo.get(campo):
                return str(corpo[campo])[:300]
    return ""
