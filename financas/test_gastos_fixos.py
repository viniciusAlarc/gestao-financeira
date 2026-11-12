"""Gastos fixos mensais (decisão de 2026-11-08).

O cadastro gera o previsto de cada mês de forma idempotente; editar o cadastro
atualiza o mês corrente aberto; desativar para de gerar. Dado inventado.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .gastos_fixos import garantir_previstos_do_mes
from .models import Categoria, Conta, GastoFixo, Previsto, TipoValor


class BaseGastosFixos(TestCase):
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

    def criar_fixo(self, **extra):
        padrao = {
            "descricao": "Aluguel",
            "valor": Decimal("1800.00"),
            "dia_vencimento": 5,
            "categoria": self.despesa,
            "conta": self.conta,
            "ativo": True,
        }
        padrao.update(extra)
        return GastoFixo.objects.create(**padrao)

    def dados_fixo(self, **extra):
        dados = {
            "fixo-descricao": "Aluguel",
            "fixo-valor": "1.800,00",
            "fixo-dia_vencimento": "5",
            "fixo-categoria": self.despesa.pk,
            "fixo-ativo": "on",
        }
        dados.update(extra)
        return dados

    @staticmethod
    def mes_seguinte(data):
        return (data.replace(day=28) + timedelta(days=4)).replace(day=1)


class CadastroGastoFixoTests(BaseGastosFixos):
    def test_cadastro_pela_tela_gera_o_previsto_do_mes(self):
        resposta = self.client.post(self.url, self.dados_fixo())

        self.assertRedirects(resposta, self.url)
        gasto = GastoFixo.objects.get()
        previsto = Previsto.objects.get()
        hoje = timezone.localdate()
        self.assertEqual(gasto.conta, self.conta)
        self.assertTrue(gasto.ativo)
        self.assertEqual(previsto.fixo, gasto)
        self.assertEqual(previsto.competencia, hoje.replace(day=1))
        self.assertEqual(previsto.vencimento.day, 5)
        self.assertEqual(previsto.valor, Decimal("1800.00"))
        self.assertEqual(previsto.tipo, TipoValor.DESPESA)
        self.assertEqual(previsto.categoria, self.despesa)
        self.assertEqual(previsto.status, Previsto.Status.ABERTO)

    def test_geracao_e_idempotente(self):
        fixo = self.criar_fixo()
        garantir_previstos_do_mes()
        garantir_previstos_do_mes()
        self.assertEqual(Previsto.objects.filter(fixo=fixo).count(), 1)

    def test_dia_31_cai_no_ultimo_dia_do_mes(self):
        fixo = self.criar_fixo(dia_vencimento=31)
        garantir_previstos_do_mes(date(2026, 2, 10))
        previsto = Previsto.objects.get(fixo=fixo)
        self.assertEqual(previsto.vencimento, date(2026, 2, 28))

    def test_dia_31_em_fevereiro_bissexto_usa_o_dia_29(self):
        fixo = self.criar_fixo(dia_vencimento=31)
        garantir_previstos_do_mes(date(2028, 2, 10))
        self.assertEqual(
            Previsto.objects.get(fixo=fixo).vencimento, date(2028, 2, 29)
        )

    def test_cadastro_inativo_nao_gera_previsto(self):
        fixo = self.criar_fixo(ativo=False)
        garantir_previstos_do_mes()
        self.assertFalse(Previsto.objects.filter(fixo=fixo).exists())

    def test_dia_fora_do_intervalo_e_rejeitado(self):
        resposta = self.client.post(
            self.url, self.dados_fixo(**{"fixo-dia_vencimento": "32"})
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("dia_vencimento", resposta.context["form_fixo"].errors)
        self.assertFalse(GastoFixo.objects.exists())

    def test_categoria_de_receita_e_rejeitada(self):
        resposta = self.client.post(
            self.url,
            self.dados_fixo(**{"fixo-categoria": self.receita.pk}),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("categoria", resposta.context["form_fixo"].errors)
        self.assertFalse(GastoFixo.objects.exists())


class PrevisaoDoMesTests(BaseGastosFixos):
    def test_home_soma_o_previsto_gerado(self):
        self.criar_fixo()
        resposta = self.client.get(reverse("financas:inicio"))
        self.assertEqual(resposta.context["previsto_aberto"], Decimal("1800.00"))
        self.assertEqual(Previsto.objects.count(), 1)

    def test_abrir_a_home_duas_vezes_nao_duplica(self):
        self.criar_fixo()
        self.client.get(reverse("financas:inicio"))
        self.client.get(reverse("financas:inicio"))
        self.assertEqual(Previsto.objects.count(), 1)

    def test_paguei_e_o_mes_seguinte_gera_outro(self):
        fixo = self.criar_fixo()
        novembro = date(2026, 11, 8)
        garantir_previstos_do_mes(novembro)
        previsto = Previsto.objects.get(fixo=fixo)

        self.client.post(
            reverse("financas:pagar_previsto", args=[previsto.pk])
        )
        previsto.refresh_from_db()
        self.assertEqual(previsto.status, Previsto.Status.PAGO)

        garantir_previstos_do_mes(self.mes_seguinte(novembro))
        dezembro = Previsto.objects.get(
            fixo=fixo, competencia=date(2026, 12, 1)
        )
        self.assertEqual(dezembro.status, Previsto.Status.ABERTO)
        self.assertEqual(dezembro.vencimento, date(2026, 12, 5))
        self.assertEqual(dezembro.valor, Decimal("1800.00"))

    def test_ignorar_o_mes_nao_impede_o_proximo(self):
        fixo = self.criar_fixo()
        novembro = date(2026, 11, 8)
        garantir_previstos_do_mes(novembro)
        previsto = Previsto.objects.get(fixo=fixo)
        self.client.post(
            reverse("financas:ignorar_previsto", args=[previsto.pk])
        )

        garantir_previstos_do_mes(self.mes_seguinte(novembro))
        self.assertTrue(
            Previsto.objects.filter(
                fixo=fixo,
                competencia=date(2026, 12, 1),
                status=Previsto.Status.ABERTO,
            ).exists()
        )


class EdicaoDoCadastroTests(BaseGastosFixos):
    def setUp(self):
        super().setUp()
        self.fixo = self.criar_fixo()
        garantir_previstos_do_mes()
        self.previsto = Previsto.objects.get(fixo=self.fixo)
        self.url_editar = reverse(
            "financas:editar_gasto_fixo", args=[self.fixo.pk]
        )

    def test_editar_atualiza_o_mes_aberto(self):
        resposta = self.client.post(
            self.url_editar,
            self.dados_fixo(
                **{
                    "fixo-descricao": "Aluguel novo",
                    "fixo-valor": "2.000,00",
                    "fixo-dia_vencimento": "10",
                }
            ),
        )
        self.assertRedirects(resposta, self.url)
        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.descricao, "Aluguel novo")
        self.assertEqual(self.previsto.valor, Decimal("2000.00"))
        self.assertEqual(self.previsto.vencimento.day, 10)

    def test_editar_nao_mexe_no_mes_pago(self):
        self.client.post(
            reverse("financas:pagar_previsto", args=[self.previsto.pk])
        )
        self.client.post(
            self.url_editar,
            self.dados_fixo(
                **{"fixo-descricao": "Aluguel novo", "fixo-valor": "2.000,00"}
            ),
        )
        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.descricao, "Aluguel")
        self.assertEqual(self.previsto.valor, Decimal("1800.00"))

        proximo = self.mes_seguinte(timezone.localdate())
        garantir_previstos_do_mes(proximo)
        novo = Previsto.objects.get(
            fixo=self.fixo, competencia=proximo.replace(day=1)
        )
        self.assertEqual(novo.descricao, "Aluguel novo")
        self.assertEqual(novo.valor, Decimal("2000.00"))

    def test_desativar_para_de_gerar_os_seguintes(self):
        self.client.post(
            self.url_editar,
            {
                "fixo-descricao": "Aluguel",
                "fixo-valor": "1.800,00",
                "fixo-dia_vencimento": "5",
                "fixo-categoria": self.despesa.pk,
                # sem fixo-ativo: desmarcado
            },
        )
        self.fixo.refresh_from_db()
        self.assertFalse(self.fixo.ativo)

        proximo = self.mes_seguinte(timezone.localdate())
        garantir_previstos_do_mes(proximo)
        self.assertFalse(
            Previsto.objects.filter(
                fixo=self.fixo, competencia=proximo.replace(day=1)
            ).exists()
        )
        # O mês corrente já gerado continua na lista.
        self.assertTrue(
            Previsto.objects.filter(
                fixo=self.fixo, competencia=timezone.localdate().replace(day=1)
            ).exists()
        )

    def test_editar_gasto_fixo_exige_login(self):
        self.client.logout()
        resposta = self.client.get(self.url_editar)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("financas:login"), resposta.url)


class PrevistoAvulsoTests(BaseGastosFixos):
    def test_previsto_avulso_continua_funcionando(self):
        resposta = self.client.post(
            self.url,
            {
                "descricao": "Conserto",
                "vencimento": "2026-12-10",
                "valor": "200,00",
                "categoria": self.despesa.pk,
            },
        )
        self.assertRedirects(resposta, self.url)
        previsto = Previsto.objects.get()
        self.assertIsNone(previsto.fixo)
        self.assertIsNone(previsto.competencia)
        self.assertEqual(previsto.descricao, "Conserto")
        self.assertFalse(GastoFixo.objects.exists())


class TotalDosFixosTests(BaseGastosFixos):
    """O total mensal dos fixos ativos fica no botão que abre a lista (2026-11-08).

    Pedido do dono: ele quer ver em algum lugar quanto os gastos fixos somam
    por mês. O total sai do cadastro, não dos previstos do mês: inativo não
    entra, porque não gera cobrança. Com a lista recolhida, o número continua
    à vista no resumo.
    """

    def test_total_soma_so_os_ativos(self):
        self.criar_fixo()  # 1.800,00 ativo
        self.criar_fixo(descricao="Academia", valor=Decimal("250.00"), ativo=False)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.context["total_fixos"], Decimal("1800.00"))
        self.assertContains(resposta, "R$ 1.800,00 por mês")
        self.assertNotContains(resposta, "R$ 2.050,00")

    def test_sem_gasto_fixo_o_resumo_nao_mostra_valor(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.context["total_fixos"], Decimal("0.00"))
        self.assertNotContains(resposta, "por mês")

    def test_bloco_de_fixos_vem_recolhido(self):
        self.criar_fixo()

        resposta = self.client.get(self.url)

        self.assertNotContains(resposta, 'bloco-recolhivel" open')

    def test_erro_no_cadastro_abre_o_bloco(self):
        """Sem isso, o erro do formulário ficaria escondido atrás do botão."""
        resposta = self.client.post(
            self.url, self.dados_fixo(**{"fixo-valor": "abc"})
        )

        self.assertContains(resposta, 'bloco-recolhivel" open')

    def test_pagar_o_previsto_nao_muda_o_total(self):
        fixo = self.criar_fixo()
        garantir_previstos_do_mes()
        previsto = Previsto.objects.get(fixo=fixo)
        self.client.post(reverse("financas:pagar_previsto", args=[previsto.pk]))

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.context["total_fixos"], Decimal("1800.00"))
