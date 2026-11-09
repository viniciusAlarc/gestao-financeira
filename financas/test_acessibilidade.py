"""Acessibilidade e teclado (T5 da rodada 2026-11-05-b).

A conferência visual a 375px (P4-4) não via o que só aparece para quem usa
teclado ou leitor de tela. Aqui se verifica o HTML que o servidor entrega:
link ativo anunciado, erro de campo ligado ao input e mensagens anunciadas.
A navegação por Tab em si é verificada no navegador, em
`docs-dev/rodada-2026-11-05-b/s5-acessibilidade.md`.
"""

import re
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Categoria, Conta, TipoValor


class BaseAcessibilidade(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="teste", password="senha-de-teste"
        )
        self.conta = Conta.objects.create(
            nome="Carteira",
            tipo=Conta.Tipo.CARTEIRA,
            saldo_inicial=Decimal("100.00"),
            padrao=True,
        )
        self.categoria = Categoria.objects.create(
            nome="Mercado", tipo=TipoValor.DESPESA
        )
        self.client.login(username="teste", password="senha-de-teste")

    def corpo(self, resposta):
        return resposta.content.decode()

    @staticmethod
    def ids(corpo):
        return set(re.findall(r'id="([^"]+)"', corpo))

    @staticmethod
    def descritos(corpo):
        return set(re.findall(r'aria-describedby="([^"]+)"', corpo))

    @classmethod
    def campo(cls, corpo, html_id):
        """A tag do input/select com aquele id, para conferir os atributos dela."""
        match = re.search(
            rf'<(?:input|select|textarea)[^>]*\bid="{html_id}"[^>]*>', corpo
        )
        return match.group(0) if match else ""


class LinkAtivoTests(BaseAcessibilidade):
    """`aria-current="page"` anuncia o link da tela atual, e só ele."""

    def test_aria_current_marca_apenas_o_link_da_tela_atual(self):
        telas = [
            ("financas:inicio", "/", "Início"),
            ("financas:lancamentos", "/lancamentos/", "Lançamentos"),
            ("financas:previstos", "/previstos/", "Previstos"),
            ("financas:relatorio", "/relatorio/", "Relatório"),
        ]
        for nome, href, rotulo in telas:
            with self.subTest(tela=nome):
                corpo = self.corpo(self.client.get(reverse(nome)))
                self.assertEqual(corpo.count('aria-current="page"'), 1)
                self.assertIn(
                    f'<a href="{href}" class="ativo" '
                    f'aria-current="page">{rotulo}</a>',
                    corpo,
                )


class ErroDeCampoTests(BaseAcessibilidade):
    """O erro de cada campo tem `id` e o input aponta para ele."""

    def test_lancamento_invalido_liga_valor_ao_erro(self):
        resposta = self.client.post(
            reverse("financas:lancamentos"),
            {"valor": "abc", "categoria": self.categoria.pk},
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = self.corpo(resposta)
        valor = self.campo(corpo, "id_valor")
        self.assertIn('aria-invalid="true"', valor)
        self.assertIn('aria-describedby="id_valor_error"', valor)
        self.assertIn('id="id_valor_error" role="alert"', corpo)
        self.assertIn("id_valor_error", self.descritos(corpo))
        self.assertIn("id_valor_error", self.ids(corpo))
        self.assertEqual(corpo.count('aria-invalid="true"'), 1)

    def test_previsto_invalido_liga_cada_campo_ao_proprio_erro(self):
        resposta = self.client.post(
            reverse("financas:previstos"),
            {
                "descricao": "",
                "vencimento": "2026-12-10",
                "valor": "abc",
                "categoria": self.categoria.pk,
            },
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = self.corpo(resposta)
        for campo in ("descricao", "valor"):
            with self.subTest(campo=campo):
                tag = self.campo(corpo, f"id_{campo}")
                self.assertIn('aria-invalid="true"', tag)
                self.assertIn(f'aria-describedby="id_{campo}_error"', tag)
                self.assertIn(f'id="id_{campo}_error" role="alert"', corpo)
                self.assertIn(f"id_{campo}_error", self.descritos(corpo))
                self.assertIn(f"id_{campo}_error", self.ids(corpo))
        # vencimento e categoria estão válidos: não podem ser marcados como inválidos
        self.assertNotIn(
            'aria-invalid="true"', self.campo(corpo, "id_vencimento")
        )
        self.assertNotIn(
            'aria-invalid="true"', self.campo(corpo, "id_categoria")
        )
        self.assertEqual(corpo.count('aria-invalid="true"'), 2)


class LoginErroTests(BaseAcessibilidade):
    """A mensagem de login inválido é anunciada e ligada aos dois campos."""

    def test_login_invalido_liga_os_campos_ao_erro(self):
        self.client.logout()
        resposta = self.client.post(
            reverse("financas:login"),
            {"username": "teste", "password": "errada"},
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = self.corpo(resposta)
        self.assertIn('id="erro-login" role="alert"', corpo)
        self.assertEqual(corpo.count('aria-describedby="erro-login"'), 2)
        self.assertEqual(corpo.count('aria-invalid="true"'), 2)


class MensagensTests(BaseAcessibilidade):
    """A lista de mensagens é uma região de status (anunciada)."""

    def test_mensagem_de_sucesso_vive_numa_regiao_de_status(self):
        resposta = self.client.post(
            reverse("financas:lancamentos"),
            {"valor": "30,00", "categoria": self.categoria.pk},
            follow=True,
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, '<ul class="mensagens" role="status">')
        self.assertContains(resposta, "Lançado: Mercado")


class FocoVisivelTests(SimpleTestCase):
    """O CSS define anel de foco para link, botão e campo (inclusive o escuro)."""

    def test_css_tem_foco_visivel_para_todos_os_controles(self):
        caminho = (
            Path(settings.BASE_DIR)
            / "financas"
            / "static"
            / "financas"
            / "app.css"
        )
        css = caminho.read_text(encoding="utf-8")
        for seletor in (
            "a:focus-visible",
            "button:focus-visible",
            "input:focus-visible",
            "select:focus-visible",
            'input[type="date"]:focus-within',
        ):
            with self.subTest(seletor=seletor):
                self.assertIn(seletor, css)
        self.assertIn("outline: 2px solid #18181b", css)
        self.assertIn("outline-offset: 2px", css)
