"""Testes do cliente da API da Pluggy (P2-13).

Nenhum teste chama a internet: a sessão do `requests` é trocada por um dublê que
devolve respostas prontas e registra o que foi pedido. O que se trava aqui é o
contrato que o cliente assume da documentação oficial (conferida em 2026-11-09):
autenticação no corpo, `X-API-KEY` nas chamadas, envelope de paginação e erro com
status — sem segredo na mensagem.
"""

import os
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import requests
from django.test import SimpleTestCase

from .pluggy_api import (
    ErroConfiguracaoPluggy,
    ErroPluggy,
    PluggyCliente,
    URL_BASE,
)

ITEM_ID = "item-de-teste"


class RespostaFalsa:
    def __init__(self, corpo=None, status_code=200):
        self._corpo = corpo if corpo is not None else {}
        self.status_code = status_code

    def json(self):
        return self._corpo


class SessaoFalsa:
    """Imita `requests.Session.request`, devolvendo as respostas na ordem."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def request(self, metodo, url, params=None, json=None, headers=None, timeout=None):
        self.chamadas.append(
            {
                "metodo": metodo,
                "url": url,
                "params": params,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if not self.respostas:
            raise AssertionError(f"chamada inesperada: {metodo} {url}")
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def cliente(sessao, **extra):
    padrao = {"client_id": "id-de-teste", "client_secret": "segredo-de-teste"}
    padrao.update(extra)
    return PluggyCliente(sessao=sessao, **padrao)


class AutenticacaoTest(SimpleTestCase):
    def test_credenciais_vao_no_corpo_e_a_chave_vai_no_cabecalho(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave-de-teste"}),
                RespostaFalsa({"page": 1, "totalPages": 1, "results": []}),
            ]
        )
        c = cliente(sessao)

        c.contas(item_id=ITEM_ID)

        autenticacao, consulta = sessao.chamadas
        self.assertEqual(autenticacao["metodo"], "POST")
        self.assertEqual(autenticacao["url"], f"{URL_BASE}/auth")
        self.assertEqual(
            autenticacao["json"],
            {"clientId": "id-de-teste", "clientSecret": "segredo-de-teste"},
        )
        # O /auth não usa chave; quem usa é a chamada seguinte.
        self.assertNotIn("X-API-KEY", autenticacao["headers"])
        self.assertEqual(consulta["headers"]["X-API-KEY"], "chave-de-teste")

    def test_chave_e_reaproveitada_entre_chamadas(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave-de-teste"}),
                RespostaFalsa({"page": 1, "totalPages": 1, "results": []}),
                RespostaFalsa({"page": 1, "totalPages": 1, "results": []}),
            ]
        )
        c = cliente(sessao)

        c.contas(item_id=ITEM_ID)
        c.contas(item_id=ITEM_ID)

        pedidos_de_chave = [ch for ch in sessao.chamadas if ch["url"].endswith("/auth")]
        self.assertEqual(len(pedidos_de_chave), 1)

    def test_chave_vencida_e_renovada(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave-1"}),
                RespostaFalsa({"page": 1, "totalPages": 1, "results": []}),
                RespostaFalsa({"apiKey": "chave-2"}),
                RespostaFalsa({"page": 1, "totalPages": 1, "results": []}),
            ]
        )
        c = cliente(sessao)
        c.contas(item_id=ITEM_ID)
        c._valida_ate = datetime.now(timezone.utc) - timedelta(seconds=1)

        c.contas(item_id=ITEM_ID)

        ultima = sessao.chamadas[-1]
        self.assertEqual(ultima["headers"]["X-API-KEY"], "chave-2")

    def test_sem_credenciais_levanta_erro_de_configuracao(self):
        c = PluggyCliente(client_id="", client_secret="", sessao=SessaoFalsa([]))

        with self.assertRaises(ErroConfiguracaoPluggy):
            c.api_key()

    def test_sem_item_id_levanta_erro_de_configuracao(self):
        c = cliente(SessaoFalsa([]))
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PLUGGY_ITEM_ID", None)
            with self.assertRaises(ErroConfiguracaoPluggy):
                c.contas()

    def test_auth_sem_api_key_e_erro(self):
        sessao = SessaoFalsa([RespostaFalsa({})])
        with self.assertRaises(ErroPluggy):
            cliente(sessao).api_key()


class ContasETransacoesTest(SimpleTestCase):
    def test_contas_percorre_todas_as_paginas(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave"}),
                RespostaFalsa(
                    {
                        "page": 1,
                        "totalPages": 2,
                        "results": [{"id": "conta-1", "type": "BANK"}],
                    }
                ),
                RespostaFalsa(
                    {
                        "page": 2,
                        "totalPages": 2,
                        "results": [{"id": "conta-2", "type": "CREDIT"}],
                    }
                ),
            ]
        )

        contas = cliente(sessao).contas(item_id=ITEM_ID)

        self.assertEqual([c["id"] for c in contas], ["conta-1", "conta-2"])
        paginas = [ch["params"] for ch in sessao.chamadas[1:]]
        self.assertEqual([p["page"] for p in paginas], [1, 2])
        self.assertTrue(all(p["pageSize"] == 500 for p in paginas))
        self.assertTrue(all(p["itemId"] == ITEM_ID for p in paginas))

    def test_transacoes_passa_dateFrom_e_dateTo_em_iso(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave"}),
                RespostaFalsa({"results": [], "next": None}),
            ]
        )

        cliente(sessao).transacoes(
            "conta-1", desde=date(2026, 11, 1), ate=date(2026, 11, 30)
        )

        chamada = sessao.chamadas[1]
        self.assertTrue(chamada["url"].endswith("/v2/transactions"))
        parametros = chamada["params"]
        self.assertEqual(parametros["accountId"], "conta-1")
        self.assertEqual(parametros["dateFrom"], "2026-11-01")
        self.assertEqual(parametros["dateTo"], "2026-11-30")

    def test_transacoes_segue_o_cursor_next(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave"}),
                RespostaFalsa(
                    {
                        "results": [{"id": "t1"}],
                        "next": "?accountId=conta-1&after=abc",
                    }
                ),
                RespostaFalsa({"results": [{"id": "t2"}], "next": None}),
            ]
        )

        transacoes = cliente(sessao).transacoes("conta-1")

        self.assertEqual([t["id"] for t in transacoes], ["t1", "t2"])
        segunda = sessao.chamadas[2]["params"]
        self.assertEqual(segunda["accountId"], "conta-1")
        self.assertEqual(segunda["after"], "abc")

    def test_cursor_que_nao_termina_para_em_vez_de_loop_infinito(self):
        sessao = SessaoFalsa(
            [RespostaFalsa({"apiKey": "chave"})]
            + [
                RespostaFalsa({"results": [], "next": "?accountId=conta-1&after=x"})
                for _ in range(5)
            ]
        )
        with patch("financas.pluggy_api.LIMITE_PAGINAS", 3):
            with self.assertRaises(ErroPluggy):
                cliente(sessao).transacoes("conta-1")

    def test_transacao_sem_conta_e_erro(self):
        with self.assertRaises(ErroPluggy):
            cliente(SessaoFalsa([])).transacoes("")

    def test_resposta_sem_results_e_erro(self):
        sessao = SessaoFalsa(
            [
                RespostaFalsa({"apiKey": "chave"}),
                RespostaFalsa({"page": 1, "totalPages": 1}),
            ]
        )
        with self.assertRaises(ErroPluggy):
            cliente(sessao).contas(item_id=ITEM_ID)

    def test_paginacao_travada_para_em_vez_de_loop_infinito(self):
        sessao = SessaoFalsa(
            [RespostaFalsa({"apiKey": "chave"})]
            + [
                RespostaFalsa({"page": 1, "totalPages": 99, "results": []})
                for _ in range(5)
            ]
        )
        with patch("financas.pluggy_api.LIMITE_PAGINAS", 3):
            with self.assertRaises(ErroPluggy):
                cliente(sessao).contas(item_id=ITEM_ID)


class ErrosTest(SimpleTestCase):
    def test_erro_http_vira_erro_pluggy_com_status_e_mensagem(self):
        sessao = SessaoFalsa(
            [RespostaFalsa({"message": "Unauthorized"}, status_code=401)]
        )
        with self.assertRaises(ErroPluggy) as capturado:
            cliente(sessao).api_key()

        erro = capturado.exception
        self.assertEqual(erro.status, 401)
        self.assertIn("HTTP 401", str(erro))
        self.assertIn("Unauthorized", str(erro))

    def test_erro_de_rede_vira_erro_pluggy(self):
        sessao = SessaoFalsa([requests.ConnectionError("sem rota")])
        with self.assertRaises(ErroPluggy):
            cliente(sessao).api_key()

    def test_segredo_nao_aparece_na_mensagem_de_erro(self):
        sessao = SessaoFalsa(
            [RespostaFalsa({"message": "credencial inválida"}, status_code=401)]
        )
        with self.assertRaises(ErroPluggy) as capturado:
            cliente(
                sessao, client_id="id-visivel", client_secret="SEGREDO-QUE-NAO-PODE-VAZAR"
            ).api_key()

        texto = str(capturado.exception)
        self.assertNotIn("SEGREDO-QUE-NAO-PODE-VAZAR", texto)
        self.assertNotIn("id-visivel", texto)

    def test_resposta_nao_json_vira_erro_pluggy(self):
        class RespostaQuebrada(RespostaFalsa):
            def json(self):
                raise ValueError("não é json")

        sessao = SessaoFalsa([RespostaQuebrada(status_code=200)])
        with self.assertRaises(ErroPluggy):
            cliente(sessao).api_key()
