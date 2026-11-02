"""Linha de base da suíte (G4). Roda com `.venv/bin/python manage.py test`.

Cobre o que o modelo promete: saldo calculado, unicidade de categoria e a regra de que
previsto pago sempre tem movimento.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Categoria, Conta, Movimento, Previsto, TipoValor


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
