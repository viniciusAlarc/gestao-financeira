"""Uso diário decidido em 2026-11-08: data no lançamento, editar, desfazer,
ignorar/reabrir previsto e navegação de mês.

Dado inventado; nenhum banco real é aberto. A suíte compartilhada continua em
`financas/tests.py`.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Conta, Movimento, Previsto, TipoValor


class BaseUsoDiario(TestCase):
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

    def lancar(self, tipo=TipoValor.DESPESA, valor="30.00", data=None, **extra):
        padrao = {
            "data": data or timezone.localdate(),
            "valor": Decimal(valor),
            "tipo": tipo,
            "conta": self.conta,
            "categoria": (
                self.despesa if tipo == TipoValor.DESPESA else self.receita
            ),
            "criado_por": self.usuario,
        }
        padrao.update(extra)
        return Movimento.objects.create(**padrao)

    def criar_previsto(self, **extra):
        padrao = {
            "descricao": "Aluguel",
            "valor": Decimal("100.00"),
            "vencimento": timezone.localdate() + timedelta(days=5),
            "tipo": TipoValor.DESPESA,
            "categoria": self.despesa,
            "conta": self.conta,
        }
        padrao.update(extra)
        return Previsto.objects.create(**padrao)


class DataNoLancamentoTests(BaseUsoDiario):
    def test_lanca_com_a_data_informada_e_abre_o_mes_dela(self):
        resposta = self.client.post(
            reverse("financas:lancamentos"),
            {"data": "2026-10-05", "valor": "30,00", "categoria": self.despesa.pk},
        )
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.data, date(2026, 10, 5))
        self.assertRedirects(
            resposta, f"{reverse('financas:lancamentos')}?mes=2026-10"
        )

    def test_sem_data_usa_hoje(self):
        self.client.post(
            reverse("financas:lancamentos"),
            {"valor": "30,00", "categoria": self.despesa.pk},
        )
        self.assertEqual(Movimento.objects.get().data, timezone.localdate())

    def test_form_antigo_sem_data_continua_valido(self):
        from .forms import MovimentoRapidoForm

        form = MovimentoRapidoForm(
            data={"valor": "30,00", "categoria": self.despesa.pk}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["data"])


class DescricaoNoLancamentoTests(BaseUsoDiario):
    """Descrição opcional no lançamento rápido (2026-11-08).

    Ela existe para diferenciar dois lançamentos da mesma categoria na lista;
    sem ela, o texto exibido continua sendo o nome da categoria.
    """

    def test_lanca_com_descricao_e_lista_mostra_ela(self):
        self.client.post(
            reverse("financas:lancamentos"),
            {
                "valor": "30,00",
                "categoria": self.despesa.pk,
                "descricao": "Padaria da esquina",
            },
        )
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.descricao, "Padaria da esquina")
        resposta = self.client.get(reverse("financas:lancamentos"))
        self.assertContains(resposta, "Padaria da esquina")

    def test_sem_descricao_a_lista_mostra_a_categoria(self):
        self.lancar(valor="30.00")
        resposta = self.client.get(reverse("financas:lancamentos"))
        self.assertContains(resposta, "Mercado")

    def test_editar_mostra_a_descricao_atual_e_grava_a_nova(self):
        movimento = self.lancar(valor="30.00", descricao="Almoço")
        url = reverse("financas:editar_movimento", args=[movimento.pk])

        resposta = self.client.get(url)
        self.assertContains(resposta, 'value="Almoço"')

        self.client.post(
            url,
            {
                "valor": "30,00",
                "categoria": self.despesa.pk,
                "descricao": "Almoço de sábado",
            },
        )
        movimento.refresh_from_db()
        self.assertEqual(movimento.descricao, "Almoço de sábado")

    def test_descricao_acima_de_120_e_recusada(self):
        resposta = self.client.post(
            reverse("financas:lancamentos"),
            {
                "valor": "30,00",
                "categoria": self.despesa.pk,
                "descricao": "D" * 121,
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Movimento.objects.exists())


class NavegacaoDeMesTests(BaseUsoDiario):
    def test_lista_mostra_o_mes_pedido(self):
        self.lancar(valor="10.00", data=date(2026, 10, 5))
        self.lancar(valor="20.00", data=timezone.localdate())
        resposta = self.client.get(
            reverse("financas:lancamentos"), {"mes": "2026-10"}
        )
        self.assertEqual(resposta.context["mes_atual"], date(2026, 10, 1))
        self.assertContains(resposta, "-R$ 10,00")
        self.assertNotContains(resposta, "-R$ 20,00")

    def test_mes_invalido_cai_no_mes_corrente(self):
        resposta = self.client.get(
            reverse("financas:lancamentos"), {"mes": "abc"}
        )
        self.assertEqual(
            resposta.context["mes_atual"],
            timezone.localdate().replace(day=1),
        )

    def test_mes_fora_do_calendario_cai_no_corrente(self):
        resposta = self.client.get(
            reverse("financas:lancamentos"),
            {"mes": "999999999999999999999-01"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.context["mes_atual"],
            timezone.localdate().replace(day=1),
        )

    def test_mes_anterior_e_seguinte_atravessam_o_ano(self):
        resposta = self.client.get(
            reverse("financas:lancamentos"), {"mes": "2026-01"}
        )
        self.assertEqual(resposta.context["mes_anterior"], date(2025, 12, 1))
        self.assertEqual(resposta.context["mes_seguinte"], date(2026, 2, 1))

    def test_relatorio_do_mes_pedido(self):
        self.lancar(valor="10.00", data=date(2026, 10, 5))
        self.lancar(valor="20.00", data=timezone.localdate())
        resposta = self.client.get(
            reverse("financas:relatorio"), {"mes": "2026-10"}
        )
        self.assertEqual(resposta.context["total_despesas"], Decimal("10.00"))
        self.assertContains(resposta, "R$ 10,00")
        self.assertNotContains(resposta, "R$ 20,00")


class EditarLancamentoTests(BaseUsoDiario):
    def setUp(self):
        super().setUp()
        self.movimento = self.lancar(valor="30.00", data=date(2026, 10, 5))
        self.url = reverse(
            "financas:editar_movimento", args=[self.movimento.pk]
        )

    def test_edita_data_valor_e_categoria(self):
        resposta = self.client.post(
            self.url,
            {
                "data": "2026-10-07",
                "valor": "45,90",
                "categoria": self.receita.pk,
            },
        )
        self.assertRedirects(
            resposta, f"{reverse('financas:lancamentos')}?mes=2026-10"
        )
        self.movimento.refresh_from_db()
        self.assertEqual(self.movimento.data, date(2026, 10, 7))
        self.assertEqual(self.movimento.valor, Decimal("45.90"))
        self.assertEqual(self.movimento.categoria, self.receita)
        # O tipo acompanha a categoria nova, como no lançamento rápido.
        self.assertEqual(self.movimento.tipo, TipoValor.RECEITA)

    def test_get_mostra_os_dados_atuais(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "2026-10-05")
        self.assertEqual(resposta.context["movimento"], self.movimento)

    def test_data_em_branco_na_edicao_mantem_a_original(self):
        self.client.post(
            self.url,
            {"data": "", "valor": "45,90", "categoria": self.despesa.pk},
        )
        self.movimento.refresh_from_db()
        self.assertEqual(self.movimento.data, date(2026, 10, 5))
        self.assertEqual(self.movimento.valor, Decimal("45.90"))

    def test_importado_do_inter_nao_e_editado(self):
        importado = self.lancar(
            origem=Movimento.Origem.INTER, id_externo="abc"
        )
        resposta = self.client.post(
            reverse("financas:editar_movimento", args=[importado.pk]),
            {"data": "2026-10-07", "valor": "99,00", "categoria": self.receita.pk},
            follow=True,
        )
        importado.refresh_from_db()
        self.assertEqual(importado.valor, Decimal("30.00"))
        self.assertContains(resposta, "importado do Inter não pode ser editado")

    def test_pagamento_de_previsto_nao_e_editado(self):
        previsto = self.criar_previsto()
        self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        movimento = Movimento.objects.get(previsto=previsto)
        resposta = self.client.get(
            reverse("financas:editar_movimento", args=[movimento.pk]),
            follow=True,
        )
        self.assertContains(resposta, "previsto pago")

    def test_movimento_desfeito_nao_e_editado(self):
        self.client.post(
            reverse("financas:desfazer_movimento", args=[self.movimento.pk])
        )
        resposta = self.client.get(self.url, follow=True)
        self.assertContains(resposta, "foi desfeito")


class DesfazerLancamentoTests(BaseUsoDiario):
    def test_desfazer_marca_cancelado_e_tira_dos_totais(self):
        movimento = self.lancar(valor="30.00")
        self.assertEqual(self.conta.saldo, Decimal("70.00"))

        resposta = self.client.post(
            reverse("financas:desfazer_movimento", args=[movimento.pk])
        )
        self.assertRedirects(resposta, reverse("financas:lancamentos"))

        movimento.refresh_from_db()
        self.assertTrue(movimento.cancelado)
        self.assertIsNotNone(movimento.cancelado_em)
        self.assertEqual(movimento.cancelado_por, self.usuario)
        self.assertEqual(self.conta.saldo, Decimal("100.00"))
        self.assertNotContains(
            self.client.get(reverse("financas:lancamentos")), "R$ 30,00"
        )
        inicio = self.client.get(reverse("financas:inicio"))
        self.assertEqual(inicio.context["gasto_mes"], Decimal("0.00"))
        relatorio = self.client.get(reverse("financas:relatorio"))
        self.assertEqual(relatorio.context["total_despesas"], Decimal("0.00"))

    def test_desfazer_e_idempotente(self):
        movimento = self.lancar()
        url = reverse("financas:desfazer_movimento", args=[movimento.pk])
        self.client.post(url)
        movimento.refresh_from_db()
        primeira_data = movimento.cancelado_em

        resposta = self.client.post(url, follow=True)

        movimento.refresh_from_db()
        self.assertEqual(movimento.cancelado_em, primeira_data)
        self.assertContains(resposta, "já foi desfeito")

    def test_importado_do_inter_nao_e_desfeito(self):
        movimento = self.lancar(
            origem=Movimento.Origem.INTER, id_externo="abc"
        )
        resposta = self.client.post(
            reverse("financas:desfazer_movimento", args=[movimento.pk]),
            follow=True,
        )
        movimento.refresh_from_db()
        self.assertFalse(movimento.cancelado)
        self.assertContains(resposta, "importado do Inter")

    def test_desfazer_pagamento_reabre_o_previsto(self):
        previsto = self.criar_previsto()
        self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)
        movimento = previsto.movimento

        self.client.post(
            reverse("financas:desfazer_movimento", args=[movimento.pk])
        )

        previsto.refresh_from_db()
        movimento.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.ABERTO)
        self.assertIsNone(previsto.movimento)
        self.assertTrue(movimento.cancelado)
        self.assertEqual(
            self.client.get(reverse("financas:previstos")).context[
                "previstos"
            ].count(),
            1,
        )
        inicio = self.client.get(reverse("financas:inicio"))
        self.assertEqual(inicio.context["previsto_aberto"], Decimal("100.00"))

        # O previsto reaberto pode ser pago de novo, sem ficar preso.
        self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)

    def test_get_nao_desfaz(self):
        movimento = self.lancar()
        resposta = self.client.get(
            reverse("financas:desfazer_movimento", args=[movimento.pk])
        )
        self.assertEqual(resposta.status_code, 405)
        movimento.refresh_from_db()
        self.assertFalse(movimento.cancelado)


class IgnorarPrevistoTests(BaseUsoDiario):
    def test_ignorar_tira_da_lista_e_do_total_sem_criar_movimento(self):
        previsto = self.criar_previsto(valor="100.00")
        resposta = self.client.post(
            reverse("financas:ignorar_previsto", args=[previsto.pk]),
            follow=True,
        )
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.IGNORADO)
        self.assertContains(resposta, "Ignorado: Aluguel")
        self.assertContains(resposta, "Ignorados")
        inicio = self.client.get(reverse("financas:inicio"))
        self.assertEqual(inicio.context["previsto_aberto"], Decimal("0.00"))
        self.assertFalse(Movimento.objects.exists())

    def test_reabrir_devolve_para_aberto(self):
        previsto = self.criar_previsto()
        self.client.post(
            reverse("financas:ignorar_previsto", args=[previsto.pk])
        )
        resposta = self.client.post(
            reverse("financas:reabrir_previsto", args=[previsto.pk]),
            follow=True,
        )
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.ABERTO)
        self.assertContains(resposta, "Reaberto: Aluguel")

    def test_ignorar_e_reabrir_sao_idempotentes(self):
        previsto = self.criar_previsto()
        ignorar = reverse("financas:ignorar_previsto", args=[previsto.pk])
        self.client.post(ignorar)
        resposta = self.client.post(ignorar, follow=True)
        self.assertContains(resposta, "já está ignorado")

        reabrir = reverse("financas:reabrir_previsto", args=[previsto.pk])
        self.client.post(reabrir)
        resposta = self.client.post(reabrir, follow=True)
        self.assertContains(resposta, "já está aberto")

    def test_reabrir_previsto_pago_e_recusado(self):
        previsto = self.criar_previsto()
        self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        resposta = self.client.post(
            reverse("financas:reabrir_previsto", args=[previsto.pk]),
            follow=True,
        )
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)
        self.assertContains(resposta, "Só um previsto ignorado")

    def test_get_nao_ignora_nem_reabre(self):
        previsto = self.criar_previsto()
        self.assertEqual(
            self.client.get(
                reverse("financas:ignorar_previsto", args=[previsto.pk])
            ).status_code,
            405,
        )
        self.assertEqual(
            self.client.get(
                reverse("financas:reabrir_previsto", args=[previsto.pk])
            ).status_code,
            405,
        )


class CancelamentoNoBancoTests(BaseUsoDiario):
    def test_cancelado_exige_quem_e_quando(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.lancar(cancelado=True)
