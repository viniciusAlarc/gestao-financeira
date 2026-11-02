"""Suíte do app (G4). Roda com `.venv/bin/python manage.py test`.

Cobre o que o modelo promete (saldo calculado, unicidade de categoria, previsto pago
sempre tem movimento) e a tela inicial da fase 2: login obrigatório, os três números
e a formatação de dinheiro.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Conta, Movimento, Previsto, TipoValor
from .templatetags.financas_extra import dinheiro


class BaseFinancas(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="teste", password="senha-de-teste"
        )
        self.conta = Conta.objects.create(
            nome="Carteira",
            tipo=Conta.Tipo.CARTEIRA,
            saldo_inicial=Decimal("100.00"),
        )
        self.categoria_receita = Categoria.objects.create(
            nome="Salário", tipo=TipoValor.RECEITA
        )
        self.categoria_despesa = Categoria.objects.create(
            nome="Mercado", tipo=TipoValor.DESPESA
        )

    def lancar(self, tipo: str, valor: str, **extra) -> Movimento:
        padrao = {
            "data": "2026-11-01",
            "valor": Decimal(valor),
            "tipo": tipo,
            "conta": self.conta,
            "categoria": (
                self.categoria_receita
                if tipo == TipoValor.RECEITA
                else self.categoria_despesa
            ),
            "criado_por": self.usuario,
        }
        padrao.update(extra)
        return Movimento.objects.create(**padrao)


class SaldoTests(BaseFinancas):
    def test_saldo_sem_movimento_e_o_saldo_inicial(self):
        self.assertEqual(self.conta.saldo, Decimal("100.00"))

    def test_saldo_soma_receita_e_subtrai_despesa(self):
        self.lancar(TipoValor.RECEITA, "50.00")
        self.lancar(TipoValor.DESPESA, "30.00")
        self.assertEqual(self.conta.saldo, Decimal("120.00"))

    def test_saldo_nao_e_afetado_por_conta_de_outra_pessoa(self):
        outra = Conta.objects.create(nome="Banco", saldo_inicial=Decimal("10.00"))
        self.lancar(TipoValor.DESPESA, "5.00", conta=outra)
        self.assertEqual(self.conta.saldo, Decimal("100.00"))
        self.assertEqual(outra.saldo, Decimal("5.00"))


class CategoriaTests(BaseFinancas):
    def test_mesmo_nome_e_tipo_nao_repete(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categoria.objects.create(nome="Mercado", tipo=TipoValor.DESPESA)

    def test_mesmo_nome_em_outro_tipo_e_permitido(self):
        Categoria.objects.create(nome="Mercado", tipo=TipoValor.RECEITA)
        self.assertEqual(Categoria.objects.filter(nome="Mercado").count(), 2)


class PrevistoTests(BaseFinancas):
    def test_previsto_pago_exige_movimento(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Previsto.objects.create(
                descricao="Aluguel",
                valor=Decimal("1200.00"),
                vencimento="2026-11-10",
                categoria=self.categoria_despesa,
                conta=self.conta,
                status=Previsto.Status.PAGO,
            )

    def test_previsto_aberto_nao_exige_movimento(self):
        previsto = Previsto.objects.create(
            descricao="Aluguel",
            valor=Decimal("1200.00"),
            vencimento="2026-11-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        self.assertEqual(previsto.status, Previsto.Status.ABERTO)

    def test_previsto_pago_com_movimento_e_aceito(self):
        movimento = self.lancar(TipoValor.DESPESA, "1200.00", descricao="Aluguel")
        previsto = Previsto.objects.create(
            descricao="Aluguel",
            valor=Decimal("1200.00"),
            vencimento="2026-11-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
            status=Previsto.Status.PAGO,
            movimento=movimento,
        )
        self.assertEqual(previsto.movimento, movimento)
        self.assertEqual(self.conta.saldo, Decimal("-1100.00"))


class DinheiroFilterTests(SimpleTestCase):
    def test_formata_milhar_e_centavos(self):
        self.assertEqual(dinheiro(Decimal("1234.56")), "R$ 1.234,56")

    def test_valor_negativo_leva_sinal(self):
        self.assertEqual(dinheiro(Decimal("-1234.56")), "-R$ 1.234,56")

    def test_valor_invalido_vira_vazio(self):
        self.assertEqual(dinheiro("abc"), "")


class TelaInicialTests(BaseFinancas):
    """A raiz do site exige login e mostra saldo, gasto do mês e previsto em aberto."""

    def _abrir(self):
        self.client.login(username="teste", password="senha-de-teste")
        return self.client.get(reverse("financas:inicio"))

    def test_inicio_exige_login(self):
        resposta = self.client.get(reverse("financas:inicio"))
        self.assertRedirects(resposta, f"{reverse('financas:login')}?next=/")

    def test_login_correto_leva_para_inicio(self):
        resposta = self.client.post(
            reverse("financas:login"),
            {"username": "teste", "password": "senha-de-teste"},
        )
        self.assertRedirects(resposta, reverse("financas:inicio"))

    def test_login_com_credencial_errada_mostra_erro(self):
        resposta = self.client.post(
            reverse("financas:login"),
            {"username": "teste", "password": "senha-errada"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Confira usuário e senha")

    def test_inicio_sem_dados_mostra_saldo_inicial_e_zeros(self):
        resposta = self._abrir()
        self.assertEqual(resposta.status_code, 200)
        for rotulo in ["Saldo", "Gasto do mês", "Previsto em aberto"]:
            self.assertContains(resposta, rotulo)
        # a fixture já tem 1 conta com saldo inicial de 100,00
        self.assertContains(resposta, "R$ 100,00")
        self.assertContains(resposta, "R$ 0,00", count=2)

    def test_saldo_consolida_todas_as_contas(self):
        Conta.objects.create(nome="Banco", saldo_inicial=Decimal("25.00"))
        self.lancar(TipoValor.RECEITA, "50.00")
        resposta = self._abrir()
        self.assertContains(resposta, "R$ 175,00")  # 100 + 25 + 50

    def test_saldo_negativo_mostra_sinal(self):
        self.lancar(TipoValor.DESPESA, "110.00")
        resposta = self._abrir()
        self.assertContains(resposta, "-R$ 10,00")

    def test_gasto_do_mes_so_despesas_do_mes_corrente(self):
        hoje = timezone.localdate()
        mes_passado = hoje.replace(day=1) - timedelta(days=1)
        self.lancar(TipoValor.DESPESA, "30.00", data=hoje)
        self.lancar(TipoValor.DESPESA, "20.00", data=hoje)
        self.lancar(TipoValor.DESPESA, "999.00", data=mes_passado)
        self.lancar(TipoValor.RECEITA, "70.00", data=hoje)
        resposta = self._abrir()
        self.assertContains(resposta, "R$ 50,00")

    def test_previsto_em_aberto_soma_so_despesas_abertas(self):
        hoje = timezone.localdate()
        vencimento = hoje + timedelta(days=8)
        for valor in ["200.00", "300.00"]:
            Previsto.objects.create(
                descricao=f"Previsto {valor}",
                valor=Decimal(valor),
                vencimento=vencimento,
                categoria=self.categoria_despesa,
                conta=self.conta,
            )
        Previsto.objects.create(  # receita aberta não entra (decisão do dono)
            descricao="Salário",
            valor=Decimal("5000.00"),
            vencimento=vencimento,
            tipo=TipoValor.RECEITA,
            categoria=self.categoria_receita,
            conta=self.conta,
        )
        movimento = self.lancar(TipoValor.DESPESA, "100.00", data=hoje)
        Previsto.objects.create(  # pago não entra
            descricao="Internet",
            valor=Decimal("100.00"),
            vencimento=hoje - timedelta(days=1),
            categoria=self.categoria_despesa,
            conta=self.conta,
            status=Previsto.Status.PAGO,
            movimento=movimento,
        )
        resposta = self._abrir()
        self.assertContains(resposta, "R$ 500,00")
