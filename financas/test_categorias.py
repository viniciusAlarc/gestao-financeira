"""Tela de categorias (decisão de 2026-11-08).

Cria com nome, tipo, 'entra no gasto' e ativa; edita nome, ativa e 'entra no
gasto'; o tipo fica fixo. Categoria não se apaga: desativa. Dado inventado.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Conta, Movimento, TipoValor


class BaseCategorias(TestCase):
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
        self.despesa = Categoria.objects.create(
            nome="Mercado", tipo=TipoValor.DESPESA
        )
        self.receita = Categoria.objects.create(
            nome="Salário", tipo=TipoValor.RECEITA
        )
        self.client.login(username="teste", password="senha-de-teste")
        self.url = reverse("financas:categorias")

    def dados_categoria(self, **extra):
        dados = {
            "nome": "Transporte",
            "tipo": TipoValor.DESPESA,
            "entra_no_gasto": "on",
            "ativa": "on",
        }
        dados.update(extra)
        return dados

    def editar_url(self, categoria):
        return reverse("financas:editar_categoria", args=[categoria.pk])

    def lancar(self, categoria, valor="30.00"):
        return Movimento.objects.create(
            data=timezone.localdate(),
            valor=Decimal(valor),
            tipo=categoria.tipo,
            conta=self.conta,
            categoria=categoria,
            criado_por=self.usuario,
        )


class CriacaoCategoriaTests(BaseCategorias):
    def test_exige_login_na_lista(self):
        self.client.logout()
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_exige_login_na_edicao(self):
        self.client.logout()
        resposta = self.client.get(self.editar_url(self.despesa))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_criar_categoria(self):
        resposta = self.client.post(self.url, self.dados_categoria())
        self.assertRedirects(resposta, self.url)
        categoria = Categoria.objects.get(nome="Transporte")
        self.assertEqual(categoria.tipo, TipoValor.DESPESA)
        self.assertTrue(categoria.ativa)
        self.assertTrue(categoria.entra_no_gasto)

        lancamentos = self.client.get(reverse("financas:lancamentos"))
        self.assertContains(lancamentos, "Transporte")

    def test_criar_categoria_fora_do_gasto(self):
        dados = self.dados_categoria(nome="Investimento")
        dados.pop("entra_no_gasto")
        self.client.post(self.url, dados)
        categoria = Categoria.objects.get(nome="Investimento")
        self.assertFalse(categoria.entra_no_gasto)
        self.lancar(categoria)

        inicio = self.client.get(reverse("financas:inicio"))
        self.assertEqual(inicio.context["gasto_mes"], Decimal("0.00"))
        relatorio = self.client.get(reverse("financas:relatorio"))
        self.assertEqual(relatorio.context["total_despesas"], Decimal("0.00"))

    def test_nome_duplicado_no_mesmo_tipo_e_rejeitado(self):
        resposta = self.client.post(
            self.url, self.dados_categoria(nome="Mercado")
        )
        self.assertEqual(resposta.status_code, 200)
        # O Django liga a restrição única em __all__; o que importa é recusar e
        # mostrar a mensagem no topo do formulário.
        self.assertTrue(resposta.context["form"].errors)
        self.assertContains(resposta, "já existe")
        self.assertEqual(
            Categoria.objects.filter(
                nome="Mercado", tipo=TipoValor.DESPESA
            ).count(),
            1,
        )

    def test_mesmo_nome_em_outro_tipo_e_aceito(self):
        resposta = self.client.post(
            self.url,
            self.dados_categoria(
                nome="Mercado", tipo=TipoValor.RECEITA
            ),
        )
        self.assertRedirects(resposta, self.url)
        self.assertTrue(
            Categoria.objects.filter(
                nome="Mercado", tipo=TipoValor.RECEITA
            ).exists()
        )

    def test_lista_mostra_inativa_e_fora_do_gasto(self):
        Categoria.objects.create(
            nome="Antiga", tipo=TipoValor.DESPESA, ativa=False
        )
        Categoria.objects.create(
            nome="Investimento",
            tipo=TipoValor.DESPESA,
            entra_no_gasto=False,
        )
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Antiga")
        self.assertContains(resposta, "inativa")
        self.assertContains(resposta, "Investimento")
        self.assertContains(resposta, "fora do gasto")

    def test_nav_marca_categorias_como_ativo(self):
        resposta = self.client.get(self.url)
        corpo = resposta.content.decode()
        self.assertEqual(corpo.count('aria-current="page"'), 1)
        # Direção A (2026-11-25): Categorias é link completo no desktop e entra
        # no menu "Mais" no celular; o link canônico do topo é o que carrega o
        # `aria-current`, e o summary do "Mais" só ganha a classe `ativo`.
        self.assertIn(
            f'<a class="nav-completo ativo" href="{self.url}" '
            f'aria-current="page">Categorias</a>',
            corpo,
        )


class EdicaoCategoriaTests(BaseCategorias):
    def test_editar_nome(self):
        movimento = self.lancar(self.despesa)
        resposta = self.client.post(
            self.editar_url(self.despesa),
            {
                "nome": "Mercado novo",
                "entra_no_gasto": "on",
                "ativa": "on",
            },
        )
        self.assertRedirects(resposta, self.url)
        self.despesa.refresh_from_db()
        movimento.refresh_from_db()
        self.assertEqual(self.despesa.nome, "Mercado novo")
        self.assertEqual(movimento.categoria.nome, "Mercado novo")

    def test_editar_ativa_desativa_e_reativa(self):
        url = self.editar_url(self.despesa)
        self.client.post(
            url,
            {"nome": "Mercado", "entra_no_gasto": "on"},
        )
        self.despesa.refresh_from_db()
        self.assertFalse(self.despesa.ativa)
        lancamentos = self.client.get(reverse("financas:lancamentos"))
        ativas = lancamentos.context["form"].fields["categoria"].queryset
        self.assertNotIn(self.despesa, ativas)

        self.client.post(
            url,
            {"nome": "Mercado", "entra_no_gasto": "on", "ativa": "on"},
        )
        self.despesa.refresh_from_db()
        self.assertTrue(self.despesa.ativa)
        lancamentos = self.client.get(reverse("financas:lancamentos"))
        ativas = lancamentos.context["form"].fields["categoria"].queryset
        self.assertIn(self.despesa, ativas)

    def test_editar_fora_do_gasto(self):
        self.lancar(self.despesa)
        self.client.post(
            self.editar_url(self.despesa),
            {"nome": "Mercado", "ativa": "on"},
        )
        self.despesa.refresh_from_db()
        self.assertFalse(self.despesa.entra_no_gasto)
        inicio = self.client.get(reverse("financas:inicio"))
        self.assertEqual(inicio.context["gasto_mes"], Decimal("0.00"))
        relatorio = self.client.get(reverse("financas:relatorio"))
        self.assertEqual(relatorio.context["total_despesas"], Decimal("0.00"))

    def test_tipo_nao_muda_na_edicao(self):
        self.client.post(
            self.editar_url(self.despesa),
            {
                "nome": "Mercado",
                "tipo": TipoValor.RECEITA,
                "entra_no_gasto": "on",
                "ativa": "on",
            },
        )
        self.despesa.refresh_from_db()
        self.assertEqual(self.despesa.tipo, TipoValor.DESPESA)

    def test_nome_duplicado_na_edicao_e_recusado(self):
        Categoria.objects.create(
            nome="Transporte", tipo=TipoValor.DESPESA
        )
        resposta = self.client.post(
            self.editar_url(self.despesa),
            {
                "nome": "Transporte",
                "entra_no_gasto": "on",
                "ativa": "on",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("nome", resposta.context["form"].errors)
        self.despesa.refresh_from_db()
        self.assertEqual(self.despesa.nome, "Mercado")
