"""Entrada fixa mensal e o bloco "Fixo do mês" (decisão de 2026-11-22).

Dado inventado; nenhum banco real é aberto. A entrada fixa gera um `Previsto`
de receita por mês, idempotente, e não entra no gasto do mês nem no previsto em
aberto de despesas.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EntradaFixaForm
from .gastos_fixos import garantir_previstos_do_mes
from .models import (
    Categoria,
    Conta,
    EntradaFixa,
    GastoFixo,
    Movimento,
    Previsto,
    TipoValor,
)


class BaseEntradaFixa(TestCase):
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
            nome="Moradia", tipo=TipoValor.DESPESA
        )
        self.receita = Categoria.objects.create(
            nome="Salário", tipo=TipoValor.RECEITA
        )
        self.client.login(username="teste", password="senha-de-teste")
        self.url = reverse("financas:previstos")
        self.mes_atual = timezone.localdate().replace(day=1)
        self.mes_seguinte = (
            self.mes_atual.replace(day=28) + timedelta(days=4)
        ).replace(day=1)

    def criar_entrada(self, **extra):
        padrao = {
            "descricao": "Salário",
            "valor": Decimal("5000.00"),
            "dia_recebimento": 5,
            "categoria": self.receita,
            "conta": self.conta,
            "ativo": True,
        }
        padrao.update(extra)
        return EntradaFixa.objects.create(**padrao)

    def dados_entrada(self, **extra):
        dados = {
            "entrada-descricao": "Salário",
            "entrada-valor": "5.000,00",
            "entrada-dia_recebimento": "5",
            "entrada-categoria": self.receita.pk,
            "entrada-ativo": "on",
        }
        dados.update(extra)
        return dados


class CadastroEntradaFixaTests(BaseEntradaFixa):
    def test_cadastro_pela_tela_gera_o_previsto_de_receita_do_mes(self):
        resposta = self.client.post(self.url, self.dados_entrada())

        self.assertRedirects(resposta, self.url)
        entrada = EntradaFixa.objects.get()
        self.assertEqual(entrada.conta, self.conta)
        previsto = Previsto.objects.get()
        self.assertEqual(previsto.entrada_fixa, entrada)
        self.assertEqual(previsto.tipo, TipoValor.RECEITA)
        self.assertEqual(previsto.categoria, self.receita)
        self.assertEqual(previsto.descricao, "Salário")
        self.assertEqual(previsto.valor, Decimal("5000.00"))
        self.assertEqual(previsto.competencia, self.mes_atual)
        self.assertEqual(previsto.vencimento.day, 5)
        self.assertEqual(previsto.status, Previsto.Status.ABERTO)

    def test_gera_um_previsto_por_entrada_ativa_e_por_mes(self):
        primeira = self.criar_entrada()
        segunda = self.criar_entrada(
            descricao="Freela", valor=Decimal("1000.00")
        )

        garantir_previstos_do_mes(self.mes_atual)
        garantir_previstos_do_mes(self.mes_seguinte)

        self.assertEqual(
            Previsto.objects.filter(entrada_fixa=primeira).count(), 2
        )
        self.assertEqual(
            Previsto.objects.filter(entrada_fixa=segunda).count(), 2
        )
        self.assertEqual(Previsto.objects.count(), 4)

    def test_geracao_e_idempotente(self):
        entrada = self.criar_entrada()
        garantir_previstos_do_mes(self.mes_atual)
        garantir_previstos_do_mes(self.mes_atual)
        self.assertEqual(
            Previsto.objects.filter(entrada_fixa=entrada).count(), 1
        )

    def test_entrada_inativa_nao_gera_previsto(self):
        self.criar_entrada(ativo=False)
        garantir_previstos_do_mes(self.mes_atual)
        self.assertFalse(Previsto.objects.exists())

    def test_dia_31_cai_no_ultimo_dia_do_mes(self):
        self.criar_entrada(dia_recebimento=31)
        garantir_previstos_do_mes(date(2026, 2, 15))
        previsto = Previsto.objects.get()
        self.assertEqual(previsto.vencimento, date(2026, 2, 28))

    def test_categoria_de_despesa_e_recusada(self):
        form = EntradaFixaForm(
            data={
                "entrada-descricao": "Salário",
                "entrada-valor": "5000,00",
                "entrada-dia_recebimento": "5",
                "entrada-categoria": self.despesa.pk,
                "entrada-ativo": "on",
            },
            prefix="entrada",
        )
        self.assertFalse(form.is_valid())
        self.assertIn("categoria", form.errors)
        self.assertFalse(EntradaFixa.objects.exists())

    def test_dia_fora_do_intervalo_e_rejeitado(self):
        form = EntradaFixaForm(
            data=self.dados_entrada(**{"entrada-dia_recebimento": "32"}),
            prefix="entrada",
        )
        self.assertFalse(form.is_valid())
        self.assertIn("dia_recebimento", form.errors)

    def test_marcar_previsto_de_receita_como_pago_nao_cria_movimento(self):
        entrada = self.criar_entrada()
        garantir_previstos_do_mes(self.mes_atual)
        previsto = Previsto.objects.get(entrada_fixa=entrada)

        self.client.post(
            reverse("financas:ignorar_previsto", args=[previsto.pk])
        )

        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.IGNORADO)
        self.assertFalse(Movimento.objects.exists())

    def test_previsto_de_receita_aparece_na_lista_do_mes(self):
        self.criar_entrada()
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Salário")
        self.assertContains(resposta, "R$ 5.000,00")


class EdicaoEntradaFixaTests(BaseEntradaFixa):
    def setUp(self):
        super().setUp()
        self.entrada = self.criar_entrada()
        garantir_previstos_do_mes(self.mes_atual)
        self.previsto = Previsto.objects.get(entrada_fixa=self.entrada)
        self.url_editar = reverse(
            "financas:editar_entrada_fixa", args=[self.entrada.pk]
        )

    def test_get_da_edicao_mostra_os_dados_atuais(self):
        resposta = self.client.get(self.url_editar)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Editar entrada fixa")
        self.assertContains(resposta, "Salário")

    def test_editar_com_categoria_de_despesa_e_recusado(self):
        resposta = self.client.post(
            self.url_editar,
            self.dados_entrada(**{"entrada-categoria": self.despesa.pk}),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("categoria", resposta.context["form"].errors)
        self.entrada.refresh_from_db()
        self.assertEqual(self.entrada.categoria, self.receita)

    def test_editar_atualiza_o_previsto_aberto_do_mes(self):
        resposta = self.client.post(
            self.url_editar,
            self.dados_entrada(
                **{
                    "entrada-descricao": "Salário novo",
                    "entrada-valor": "6.000,00",
                    "entrada-dia_recebimento": "10",
                }
            ),
        )

        self.assertRedirects(resposta, self.url)
        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.descricao, "Salário novo")
        self.assertEqual(self.previsto.valor, Decimal("6000.00"))
        self.assertEqual(self.previsto.vencimento.day, 10)

    def test_editar_nao_mexe_no_mes_pago(self):
        self.client.post(
            reverse("financas:ignorar_previsto", args=[self.previsto.pk])
        )
        self.client.post(
            self.url_editar,
            self.dados_entrada(**{"entrada-valor": "6.000,00"}),
        )

        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.valor, Decimal("5000.00"))

    def test_desativar_para_de_gerar_os_seguintes(self):
        dados = self.dados_entrada()
        dados.pop("entrada-ativo")
        self.client.post(self.url_editar, dados)

        self.entrada.refresh_from_db()
        self.assertFalse(self.entrada.ativo)
        garantir_previstos_do_mes(self.mes_seguinte)
        self.assertFalse(
            Previsto.objects.filter(
                entrada_fixa=self.entrada, competencia=self.mes_seguinte
            ).exists()
        )

    def test_editar_entrada_exige_login(self):
        self.client.logout()
        resposta = self.client.get(self.url_editar)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)


class TelaInicialFixoDoMesTests(BaseEntradaFixa):
    def test_mostra_entra_sai_e_sobra_na_ordem_decidida(self):
        self.criar_entrada(valor=Decimal("5000.00"))
        GastoFixo.objects.create(
            descricao="Aluguel",
            valor=Decimal("1800.00"),
            dia_vencimento=5,
            categoria=self.despesa,
            conta=self.conta,
        )

        resposta = self.client.get(reverse("financas:inicio"))

        self.assertEqual(resposta.context["entra_fixo"], Decimal("5000.00"))
        self.assertEqual(resposta.context["sai_fixo"], Decimal("1800.00"))
        self.assertEqual(resposta.context["sobra_fixa"], Decimal("3200.00"))
        corpo = resposta.content.decode()
        posicoes = [
            corpo.index(rotulo)
            for rotulo in [
                "Saldo",
                "Fixo do mês",
                "Entra fixo",
                "Sai fixo",
                "Sobra fixa",
                "Gasto do mês",
                "Previsto em aberto",
            ]
        ]
        self.assertEqual(posicoes, sorted(posicoes))

    def test_sobra_fixa_negativa_mostra_sinal(self):
        GastoFixo.objects.create(
            descricao="Aluguel",
            valor=Decimal("1800.00"),
            dia_vencimento=5,
            categoria=self.despesa,
            conta=self.conta,
        )

        resposta = self.client.get(reverse("financas:inicio"))

        self.assertEqual(resposta.context["sobra_fixa"], Decimal("-1800.00"))
        self.assertContains(resposta, "-R$ 1.800,00")

    def test_previsto_de_receita_nao_entra_no_aberto_nem_no_gasto_do_mes(self):
        self.criar_entrada()

        resposta = self.client.get(reverse("financas:inicio"))

        self.assertEqual(resposta.context["entra_fixo"], Decimal("5000.00"))
        self.assertEqual(resposta.context["previsto_aberto"], Decimal("0.00"))
        self.assertEqual(resposta.context["gasto_mes"], Decimal("0.00"))

    def test_entrada_inativa_nao_soma_no_entra_fixo(self):
        self.criar_entrada(valor=Decimal("5000.00"))
        self.criar_entrada(
            descricao="Extra antigo",
            valor=Decimal("2000.00"),
            ativo=False,
        )

        resposta = self.client.get(reverse("financas:inicio"))

        self.assertEqual(resposta.context["entra_fixo"], Decimal("5000.00"))
