"""Suíte do app (G4). Roda com `.venv/bin/python manage.py test`.

Cobre o que o modelo promete (saldo calculado, unicidade de categoria, previsto pago
sempre tem movimento) e a tela inicial da fase 2: login obrigatório, os três números
e a formatação de dinheiro.
"""

import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .forms import MovimentoRapidoForm, PrevistoForm
from .models import Categoria, Conta, Movimento, Previsto, TipoValor
from .templatetags.financas_extra import dinheiro, porcentagem


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

    def test_porcentagem_formata_com_virgula(self):
        self.assertEqual(porcentagem(Decimal("60.0")), "60,0%")
        self.assertEqual(porcentagem(Decimal("33.3")), "33,3%")
        self.assertEqual(porcentagem("abc"), "")


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


class ContaPadraoTests(BaseFinancas):
    """A conta padrão é a usada pelo lançamento rápido (decisão de 2026-11-03)."""

    def test_conta_nasce_sem_padrao(self):
        self.assertFalse(self.conta.padrao)

    def test_marcar_padrao_desmarca_as_outras(self):
        outra = Conta.objects.create(nome="Banco", padrao=True)
        self.conta.padrao = True
        self.conta.save()
        outra.refresh_from_db()
        self.assertFalse(outra.padrao)
        self.assertTrue(Conta.objects.get(pk=self.conta.pk).padrao)

    def test_banco_nao_aceita_duas_contas_padrao(self):
        Conta.objects.create(nome="Banco", padrao=True)
        outra = Conta.objects.create(nome="Carteira 2")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Conta.objects.filter(pk=outra.pk).update(padrao=True)


class LancamentoRapidoTests(BaseFinancas):
    """Fase 3: formulário de valor + categoria e lista do mês corrente."""

    def setUp(self):
        super().setUp()
        self.conta.padrao = True
        self.conta.save()
        self.url = reverse("financas:lancamentos")

    def _abrir(self):
        self.client.login(username="teste", password="senha-de-teste")
        return self.client.get(self.url)

    def test_exige_login(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_form_aceita_virgula_com_milhar(self):
        form = MovimentoRapidoForm(
            data={"valor": "1.234,56", "categoria": self.categoria_despesa.pk}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["valor"], Decimal("1234.56"))

    def test_form_aceita_ponto_decimal(self):
        form = MovimentoRapidoForm(
            data={"valor": "30.50", "categoria": self.categoria_despesa.pk}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["valor"], Decimal("30.50"))

    def test_lancar_cria_movimento_com_dados_da_sessao(self):
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(
            self.url,
            {"valor": "30,50", "categoria": self.categoria_despesa.pk},
        )
        self.assertRedirects(resposta, self.url)
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.valor, Decimal("30.50"))
        self.assertEqual(movimento.tipo, TipoValor.DESPESA)
        self.assertEqual(movimento.conta, self.conta)
        self.assertEqual(movimento.criado_por, self.usuario)
        self.assertEqual(movimento.data, timezone.localdate())

    def test_tipo_vem_da_categoria_escolhida(self):
        self.client.login(username="teste", password="senha-de-teste")
        self.client.post(
            self.url,
            {"valor": "50,00", "categoria": self.categoria_receita.pk},
        )
        self.assertEqual(Movimento.objects.get().tipo, TipoValor.RECEITA)

    def test_sem_conta_padrao_nao_lanca_e_explica(self):
        self.conta.padrao = False
        self.conta.save()
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(
            self.url,
            {"valor": "30,00", "categoria": self.categoria_despesa.pk},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "conta está marcada como padrão")
        self.assertFalse(Movimento.objects.exists())

    def test_conta_padrao_inativa_nao_e_usada(self):
        self.conta.ativa = False
        self.conta.save()
        resposta = self._abrir()
        self.assertIsNone(resposta.context["conta_padrao"])

    def test_lista_mostra_movimentos_do_mes_e_total_de_despesas(self):
        hoje = timezone.localdate()
        self.lancar(TipoValor.DESPESA, "30.00", data=hoje)
        self.lancar(TipoValor.RECEITA, "50.00", data=hoje)
        mes_passado = hoje.replace(day=1) - timedelta(days=1)
        self.lancar(TipoValor.DESPESA, "999.00", data=mes_passado)
        resposta = self._abrir()
        self.assertContains(resposta, "Total de despesas do mês")
        self.assertContains(resposta, "-R$ 30,00")
        self.assertContains(resposta, "R$ 50,00")
        self.assertNotContains(resposta, "999,00")

    def test_lista_agrupa_por_dia(self):
        hoje = timezone.localdate()
        self.lancar(TipoValor.DESPESA, "10.00", data=hoje.replace(day=1))
        self.lancar(TipoValor.DESPESA, "20.00", data=hoje.replace(day=2))
        resposta = self._abrir()
        self.assertEqual(len(resposta.context["dias"]), 2)
        self.assertContains(resposta, hoje.replace(day=1).strftime("%d/%m"))
        self.assertContains(resposta, hoje.replace(day=2).strftime("%d/%m"))

    def test_categoria_inativa_fica_fora_do_formulario(self):
        Categoria.objects.create(
            nome="Categoria velha", tipo=TipoValor.DESPESA, ativa=False
        )
        resposta = self._abrir()
        self.assertNotContains(resposta, "Categoria velha")

    def test_valor_invalido_mostra_erro_e_nao_lanca(self):
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(
            self.url,
            {"valor": "abc", "categoria": self.categoria_despesa.pk},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("valor", resposta.context["form"].errors)
        self.assertFalse(Movimento.objects.exists())


class GastosPrevistosTests(BaseFinancas):
    """Fase 4: criar previsto, listar abertos e pagar sem duplicar movimento."""

    def setUp(self):
        super().setUp()
        self.conta.padrao = True
        self.conta.save()
        self.url = reverse("financas:previstos")
        self.dados_validos = {
            "descricao": "Internet",
            "vencimento": "2026-12-10",
            "valor": "89,90",
            "categoria": self.categoria_despesa.pk,
        }

    def _abrir(self):
        self.client.login(username="teste", password="senha-de-teste")
        return self.client.get(self.url)

    def test_exige_login_na_lista(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_exige_login_ao_pagar(self):
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        resposta = self.client.post(reverse("financas:pagar_previsto", args=[previsto.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_formulario_mostra_somente_categorias_de_despesa_ativas(self):
        receita = Categoria.objects.create(
            nome="Salário previsto", tipo=TipoValor.RECEITA
        )
        inativa = Categoria.objects.create(
            nome="Categoria velha", tipo=TipoValor.DESPESA, ativa=False
        )
        resposta = self._abrir()
        self.assertContains(resposta, "Mercado")
        self.assertNotContains(resposta, "Salário previsto")
        self.assertNotContains(resposta, "Categoria velha")

    def test_formulario_rejeita_categoria_de_receita(self):
        form = PrevistoForm(
            data={
                **self.dados_validos,
                "categoria": self.categoria_receita.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("categoria", form.errors)

    def test_formulario_rejeita_descricao_ou_valor_invalido(self):
        for campo, valor in [("descricao", ""), ("valor", "abc")]:
            with self.subTest(campo=campo):
                dados = {**self.dados_validos, campo: valor}
                form = PrevistoForm(data=dados)
                self.assertFalse(form.is_valid(), form.errors)
                self.assertIn(campo, form.errors)

    def test_criar_previsto_grava_descricao_vencimento_valor_e_conta_padrao(self):
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(self.url, self.dados_validos)
        self.assertRedirects(resposta, self.url)
        previsto = Previsto.objects.get()
        self.assertEqual(previsto.descricao, "Internet")
        self.assertEqual(previsto.vencimento, date(2026, 12, 10))
        self.assertEqual(previsto.valor, Decimal("89.90"))
        self.assertEqual(previsto.tipo, TipoValor.DESPESA)
        self.assertEqual(previsto.conta, self.conta)
        self.assertEqual(previsto.categoria, self.categoria_despesa)
        self.assertEqual(previsto.status, Previsto.Status.ABERTO)
        self.assertIsNone(previsto.movimento)

    def test_sem_conta_padrao_nao_cria_previsto_e_explica(self):
        self.conta.padrao = False
        self.conta.save()
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(self.url, self.dados_validos)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "conta está marcada como padrão")
        self.assertFalse(Previsto.objects.exists())

    def test_sem_categoria_de_despesa_ativa_nao_cria_previsto_e_explica(self):
        self.categoria_despesa.ativa = False
        self.categoria_despesa.save()
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(self.url, self.dados_validos)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "categoria de despesa ativa")
        self.assertFalse(Previsto.objects.exists())

    def test_lista_somente_previstos_de_despesa_abertos_em_ordem(self):
        hoje = timezone.localdate()
        primeiro = Previsto.objects.create(
            descricao="Primeiro",
            valor=Decimal("10.00"),
            vencimento=hoje + timedelta(days=2),
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        segundo = Previsto.objects.create(
            descricao="Segundo",
            valor=Decimal("20.00"),
            vencimento=hoje + timedelta(days=5),
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        movimento = self.lancar(TipoValor.DESPESA, "30.00", descricao="Pago")
        Previsto.objects.create(
            descricao="Pago",
            valor=Decimal("30.00"),
            vencimento=hoje + timedelta(days=3),
            categoria=self.categoria_despesa,
            conta=self.conta,
            status=Previsto.Status.PAGO,
            movimento=movimento,
        )
        Previsto.objects.create(
            descricao="Receita",
            valor=Decimal("40.00"),
            vencimento=hoje + timedelta(days=4),
            tipo=TipoValor.RECEITA,
            categoria=self.categoria_receita,
            conta=self.conta,
        )

        resposta = self._abrir()
        self.assertEqual(list(resposta.context["previstos"]), [primeiro, segundo])
        self.assertContains(resposta, "Primeiro")
        self.assertContains(resposta, "Segundo")
        self.assertNotContains(resposta, "Pago")
        self.assertNotContains(resposta, "Receita")

    def test_paguei_cria_um_movimento_na_data_real_e_marca_como_pago(self):
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        data_pagamento = date(2026, 11, 3)
        self.client.login(username="teste", password="senha-de-teste")

        with patch("financas.views.timezone.localdate", return_value=data_pagamento):
            resposta = self.client.post(
                reverse("financas:pagar_previsto", args=[previsto.pk])
            )

        self.assertRedirects(resposta, self.url)
        previsto.refresh_from_db()
        movimento = Movimento.objects.get()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)
        self.assertEqual(previsto.movimento, movimento)
        self.assertEqual(movimento.data, data_pagamento)
        self.assertEqual(movimento.valor, Decimal("89.90"))
        self.assertEqual(movimento.tipo, TipoValor.DESPESA)
        self.assertEqual(movimento.conta, self.conta)
        self.assertEqual(movimento.categoria, self.categoria_despesa)
        self.assertEqual(movimento.descricao, "Internet")
        self.assertEqual(movimento.origem, Movimento.Origem.MANUAL)
        self.assertEqual(movimento.criado_por, self.usuario)

    def test_paguei_e_idempotente_para_clique_duplo(self):
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        url_pagamento = reverse("financas:pagar_previsto", args=[previsto.pk])
        self.client.login(username="teste", password="senha-de-teste")

        primeira = self.client.post(url_pagamento)
        segunda = self.client.post(url_pagamento)

        self.assertRedirects(primeira, self.url)
        self.assertRedirects(segunda, self.url)
        self.assertEqual(Movimento.objects.count(), 1)
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)
        self.assertIsNotNone(previsto.movimento)

    def test_paguei_previsto_de_outra_conta_usa_a_conta_do_previsto(self):
        outra_conta = Conta.objects.create(nome="Outra conta")
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=outra_conta,
        )
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        self.assertRedirects(resposta, self.url)
        previsto.refresh_from_db()
        movimento = Movimento.objects.get()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)
        self.assertEqual(previsto.movimento, movimento)
        self.assertEqual(movimento.conta, outra_conta)

    def test_paguei_funciona_sem_conta_padrao(self):
        self.conta.padrao = False
        self.conta.save()
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        self.assertRedirects(resposta, self.url)
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)
        self.assertEqual(Movimento.objects.get().conta, self.conta)

    def test_get_na_acao_paguei_e_recusado(self):
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.get(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        self.assertEqual(resposta.status_code, 405)
        self.assertFalse(Movimento.objects.exists())

    def test_previsto_futuro_aberto_nao_entra_no_gasto_do_mes(self):
        hoje = timezone.localdate()
        Previsto.objects.create(
            descricao="Internet futura",
            valor=Decimal("89.90"),
            vencimento=hoje + timedelta(days=10),
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.get(reverse("financas:inicio"))
        self.assertEqual(resposta.context["gasto_mes"], Decimal("0.00"))
        self.assertEqual(resposta.context["previsto_aberto"], Decimal("89.90"))

    def test_previsto_pago_entra_no_gasto_e_sai_do_total_em_aberto(self):
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento=timezone.localdate() + timedelta(days=10),
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        self.client.login(username="teste", password="senha-de-teste")
        self.client.post(reverse("financas:pagar_previsto", args=[previsto.pk]))

        resposta = self.client.get(reverse("financas:inicio"))
        self.assertEqual(resposta.context["gasto_mes"], Decimal("89.90"))
        self.assertEqual(resposta.context["previsto_aberto"], Decimal("0.00"))


class RelatorioTests(BaseFinancas):
    """Fase 5: despesas do mês por categoria, com percentual e ordem decrescente."""

    def setUp(self):
        super().setUp()
        self.url = reverse("financas:relatorio")
        self.hoje = timezone.localdate()
        self.transporte = Categoria.objects.create(
            nome="Transporte", tipo=TipoValor.DESPESA
        )

    def _abrir(self):
        self.client.login(username="teste", password="senha-de-teste")
        return self.client.get(self.url)

    def test_exige_login(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_soma_por_categoria_em_ordem_decrescente(self):
        self.lancar(TipoValor.DESPESA, "60.00", data=self.hoje)
        self.lancar(
            TipoValor.DESPESA, "40.00", data=self.hoje, categoria=self.transporte
        )
        resposta = self._abrir()
        linhas = resposta.context["linhas"]
        self.assertEqual([linha["nome"] for linha in linhas], ["Mercado", "Transporte"])
        self.assertEqual(
            [linha["total"] for linha in linhas],
            [Decimal("60.00"), Decimal("40.00")],
        )
        self.assertEqual(
            [linha["percentual"] for linha in linhas],
            [Decimal("60.0"), Decimal("40.0")],
        )
        self.assertContains(resposta, "60,0%")
        self.assertContains(resposta, "40,0%")

    def test_soma_das_categorias_fecha_com_o_total_de_despesas(self):
        self.lancar(TipoValor.DESPESA, "10.10", data=self.hoje)
        self.lancar(
            TipoValor.DESPESA, "20.20", data=self.hoje, categoria=self.transporte
        )
        self.lancar(TipoValor.DESPESA, "30.30", data=self.hoje)
        resposta = self._abrir()
        soma = sum(
            (linha["total"] for linha in resposta.context["linhas"]),
            Decimal("0.00"),
        )
        self.assertEqual(soma, resposta.context["total_despesas"])
        self.assertEqual(resposta.context["total_despesas"], Decimal("60.60"))

    def test_exclui_receitas_e_despesas_de_outro_mes(self):
        self.lancar(TipoValor.DESPESA, "30.00", data=self.hoje)
        self.lancar(TipoValor.RECEITA, "50.00", data=self.hoje)
        mes_passado = self.hoje.replace(day=1) - timedelta(days=1)
        self.lancar(TipoValor.DESPESA, "999.00", data=mes_passado)
        resposta = self._abrir()
        self.assertEqual(resposta.context["total_despesas"], Decimal("30.00"))
        self.assertEqual(len(resposta.context["linhas"]), 1)
        self.assertNotContains(resposta, "999,00")

    def test_mes_vazio_mostra_estado_vazio(self):
        resposta = self._abrir()
        self.assertEqual(resposta.context["linhas"], [])
        self.assertEqual(resposta.context["total_despesas"], Decimal("0.00"))
        self.assertContains(resposta, "Nenhuma despesa neste mês")


class LogoutTests(BaseFinancas):
    """Fase 6: sair da conta pela navegação."""

    def test_logout_encerra_a_sessao(self):
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.post(reverse("financas:logout"))
        self.assertRedirects(resposta, reverse("financas:login"))
        resposta = self.client.get(reverse("financas:inicio"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)

    def test_logout_nao_aceita_get(self):
        self.client.login(username="teste", password="senha-de-teste")
        resposta = self.client.get(reverse("financas:logout"))
        self.assertEqual(resposta.status_code, 405)


class DoisUsuariosTests(BaseFinancas):
    """Fase 6: duas contas veem tudo e o lançamento registra quem lançou."""

    def setUp(self):
        super().setUp()
        self.conta.padrao = True
        self.conta.save()
        self.esposa = get_user_model().objects.create_user(
            username="esposa", password="senha-dela"
        )

    def test_criado_por_registra_quem_lancou(self):
        self.client.login(username="esposa", password="senha-dela")
        self.client.post(
            reverse("financas:lancamentos"),
            {"valor": "12,00", "categoria": self.categoria_despesa.pk},
        )
        self.assertEqual(Movimento.objects.get().criado_por, self.esposa)

    def test_pagamento_registra_quem_pagou(self):
        previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("89.90"),
            vencimento="2026-12-10",
            categoria=self.categoria_despesa,
            conta=self.conta,
        )
        self.client.login(username="esposa", password="senha-dela")
        self.client.post(reverse("financas:pagar_previsto", args=[previsto.pk]))
        self.assertEqual(Movimento.objects.get().criado_por, self.esposa)

    def test_os_dois_veem_todos_os_lancamentos(self):
        self.lancar(TipoValor.DESPESA, "30.00", data=timezone.localdate())
        self.client.login(username="esposa", password="senha-dela")
        resposta = self.client.get(reverse("financas:lancamentos"))
        self.assertContains(resposta, "-R$ 30,00")


class PwaTests(SimpleTestCase):
    """Fase 6: manifesto, ícones e metatags para instalar o app."""

    def test_manifesto_tem_campos_e_icones(self):
        caminho = (
            Path(settings.BASE_DIR)
            / "financas"
            / "static"
            / "financas"
            / "manifest.webmanifest"
        )
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        for campo in ["name", "short_name", "start_url", "scope", "display", "icons"]:
            self.assertIn(campo, dados)
        self.assertEqual(dados["display"], "standalone")
        self.assertEqual(dados["start_url"], "/")
        self.assertEqual(dados["scope"], "/")
        for icone in dados["icons"]:
            arquivo = caminho.parent / Path(icone["src"]).name
            self.assertTrue(arquivo.exists(), arquivo)
            self.assertEqual(
                arquivo.read_bytes()[:8],
                bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
            )

    def test_base_tem_manifesto_icone_e_theme_color(self):
        resposta = self.client.get(reverse("financas:login"))
        self.assertContains(resposta, 'rel="manifest"')
        self.assertContains(resposta, "icone-192.png")
        self.assertContains(resposta, 'name="theme-color"')
