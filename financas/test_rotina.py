"""Rotina diária (2026-11-22): tarefas por pessoa, check que reinicia todo dia
e leitura da rotina do outro perfil.

O dono da tarefa sai da sessão em toda escrita; a rotina do outro é somente
leitura. Dado inventado; nenhum banco real é aberto.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ConclusaoTarefa, Tarefa

SENHA = "senha-de-teste-rotina"


class BaseRotina(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.vinicius = Usuario.objects.create_user(
            username="vinicius", password=SENHA, first_name="Vinícius"
        )
        self.esposa = Usuario.objects.create_user(
            username="esposa", password=SENHA, first_name="Ana"
        )
        self.tarefa = Tarefa.objects.create(dono=self.vinicius, titulo="Tomar água")
        self.tarefa_dela = Tarefa.objects.create(dono=self.esposa, titulo="Alongar")
        self.client.login(username="vinicius", password=SENHA)

    def url_rotina(self, perfil=None):
        url = reverse("financas:rotina")
        if perfil is None:
            return url
        return f"{url}?perfil={perfil.pk}"

    def concluir(self, tarefa, quando=None):
        return ConclusaoTarefa.objects.create(
            tarefa=tarefa, data=quando or timezone.localdate()
        )


class TelaDaRotinaTests(BaseRotina):
    def test_login_obrigatorio(self):
        self.client.logout()
        resposta = self.client.get(reverse("financas:rotina"))
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("financas:login")))

    def test_minhas_tarefas_mostram_formulario_e_nao_as_do_outro(self):
        resposta = self.client.get(self.url_rotina())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Tomar água")
        self.assertNotContains(resposta, "Alongar")
        self.assertContains(resposta, 'name="titulo"')

    def test_contagem_do_dia(self):
        Tarefa.objects.create(dono=self.vinicius, titulo="Ler")
        self.concluir(self.tarefa)
        resposta = self.client.get(self.url_rotina())
        self.assertEqual(resposta.context["concluidas"], 1)
        self.assertEqual(resposta.context["total"], 2)
        self.assertContains(resposta, "1 de 2</strong> concluídas hoje", html=False)

    def test_rotina_do_outro_e_somente_leitura(self):
        resposta = self.client.get(self.url_rotina(self.esposa))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Alongar")
        self.assertNotContains(resposta, "Tomar água")
        self.assertContains(resposta, "Somente leitura")
        self.assertNotContains(resposta, 'name="titulo"')
        self.assertNotContains(
            resposta,
            reverse("financas:concluir_tarefa", args=[self.tarefa_dela.pk]),
        )

    def test_esposa_tambem_ve_a_rotina_do_outro_em_leitura(self):
        self.client.logout()
        self.client.login(username="esposa", password=SENHA)
        resposta = self.client.get(self.url_rotina(self.vinicius))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Tomar água")
        self.assertContains(resposta, "Somente leitura")
        self.assertNotContains(resposta, 'name="titulo"')

    def test_perfil_proprio_abre_minhas_tarefas(self):
        resposta = self.client.get(self.url_rotina(self.vinicius))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Tomar água")
        self.assertContains(resposta, 'name="titulo"')

    def test_perfil_inexistente_responde_404(self):
        for valor in ("999999", "abc", "-1"):
            with self.subTest(valor=valor):
                resposta = self.client.get(
                    f"{reverse('financas:rotina')}?perfil={valor}"
                )
                self.assertEqual(resposta.status_code, 404)

    def test_perfil_sem_nome_aparece_com_username(self):
        get_user_model().objects.create_user(username="sem-nome", password=SENHA)
        resposta = self.client.get(self.url_rotina())
        self.assertContains(resposta, "sem-nome")

    def test_navegacao_tem_link_da_rotina(self):
        resposta = self.client.get(reverse("financas:inicio"))
        self.assertContains(resposta, reverse("financas:rotina"))
        self.assertContains(resposta, "Rotina")


class CheckDiarioTests(BaseRotina):
    def test_concluir_cria_registro_de_hoje(self):
        resposta = self.client.post(
            reverse("financas:concluir_tarefa", args=[self.tarefa.pk])
        )
        self.assertRedirects(resposta, reverse("financas:rotina"))
        conclusao = ConclusaoTarefa.objects.get(tarefa=self.tarefa)
        self.assertEqual(conclusao.data, timezone.localdate())
        resposta = self.client.get(self.url_rotina())
        self.assertContains(resposta, "checked")

    def test_concluir_duas_vezes_nao_duplica(self):
        url = reverse("financas:concluir_tarefa", args=[self.tarefa.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(
            ConclusaoTarefa.objects.filter(tarefa=self.tarefa).count(), 1
        )

    def test_desmarcar_apaga_so_o_dia_de_hoje(self):
        ontem = timezone.localdate() - timedelta(days=1)
        self.concluir(self.tarefa, ontem)
        self.concluir(self.tarefa)
        resposta = self.client.post(
            reverse("financas:desfazer_conclusao_tarefa", args=[self.tarefa.pk])
        )
        self.assertRedirects(resposta, reverse("financas:rotina"))
        self.assertFalse(
            ConclusaoTarefa.objects.filter(
                tarefa=self.tarefa, data=timezone.localdate()
            ).exists()
        )
        self.assertTrue(
            ConclusaoTarefa.objects.filter(tarefa=self.tarefa, data=ontem).exists()
        )

    def test_desmarcar_sem_conclusao_e_idempotente(self):
        resposta = self.client.post(
            reverse("financas:desfazer_conclusao_tarefa", args=[self.tarefa.pk])
        )
        self.assertRedirects(resposta, reverse("financas:rotina"))
        self.assertFalse(ConclusaoTarefa.objects.exists())

    def test_conclusao_de_ontem_nao_aparece_como_hoje(self):
        self.concluir(self.tarefa, timezone.localdate() - timedelta(days=1))
        resposta = self.client.get(self.url_rotina())
        self.assertEqual(resposta.context["concluidas"], 0)
        self.assertFalse(resposta.context["tarefas"][0].concluida_hoje)

    def test_nao_conclui_tarefa_do_outro(self):
        resposta = self.client.post(
            reverse("financas:concluir_tarefa", args=[self.tarefa_dela.pk])
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertFalse(ConclusaoTarefa.objects.exists())

    def test_nao_desmarca_tarefa_do_outro(self):
        self.concluir(self.tarefa_dela)
        resposta = self.client.post(
            reverse("financas:desfazer_conclusao_tarefa", args=[self.tarefa_dela.pk])
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(
            ConclusaoTarefa.objects.filter(tarefa=self.tarefa_dela).exists()
        )

    def test_acoes_de_check_sao_post(self):
        for nome in ("concluir_tarefa", "desfazer_conclusao_tarefa"):
            with self.subTest(nome=nome):
                resposta = self.client.get(
                    reverse(f"financas:{nome}", args=[self.tarefa.pk])
                )
                self.assertEqual(resposta.status_code, 405)

    def test_conclusao_unica_por_dia_no_banco(self):
        self.concluir(self.tarefa)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.concluir(self.tarefa)


class GerenciarTarefasTests(BaseRotina):
    def test_criar_tarefa_propria(self):
        resposta = self.client.post(
            reverse("financas:rotina"), {"titulo": "Meditar"}
        )
        self.assertRedirects(resposta, reverse("financas:rotina"))
        tarefa = Tarefa.objects.get(titulo="Meditar")
        self.assertEqual(tarefa.dono, self.vinicius)

    def test_titulo_vazio_nao_cria_tarefa(self):
        resposta = self.client.post(
            reverse("financas:rotina"), {"titulo": "   "}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Tarefa.objects.filter(dono=self.vinicius).count(), 1)
        self.assertIn("titulo", resposta.context["form"].errors)

    def test_titulo_longo_nao_cria_tarefa(self):
        resposta = self.client.post(
            reverse("financas:rotina"), {"titulo": "T" * 121}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Tarefa.objects.filter(titulo="T" * 121).exists())

    def test_post_no_perfil_do_outro_nao_cria_tarefa(self):
        resposta = self.client.post(
            self.url_rotina(self.esposa), {"titulo": "Tarefa indevida"}
        )
        self.assertRedirects(
            resposta, f"{reverse('financas:rotina')}?perfil={self.esposa.pk}"
        )
        self.assertFalse(Tarefa.objects.filter(titulo="Tarefa indevida").exists())

    def test_editar_tarefa_propria(self):
        resposta = self.client.post(
            reverse("financas:editar_tarefa", args=[self.tarefa.pk]),
            {"titulo": "Tomar dois copos de água"},
        )
        self.assertRedirects(resposta, reverse("financas:rotina"))
        self.tarefa.refresh_from_db()
        self.assertEqual(self.tarefa.titulo, "Tomar dois copos de água")

    def test_editar_tarefa_do_outro_responde_404(self):
        resposta = self.client.post(
            reverse("financas:editar_tarefa", args=[self.tarefa_dela.pk]),
            {"titulo": "Alterada"},
        )
        self.assertEqual(resposta.status_code, 404)
        self.tarefa_dela.refresh_from_db()
        self.assertEqual(self.tarefa_dela.titulo, "Alongar")

    def test_excluir_tarefa_propria_apaga_historico(self):
        self.concluir(self.tarefa)
        resposta = self.client.post(
            reverse("financas:excluir_tarefa", args=[self.tarefa.pk])
        )
        self.assertRedirects(resposta, reverse("financas:rotina"))
        self.assertFalse(Tarefa.objects.filter(pk=self.tarefa.pk).exists())
        self.assertFalse(ConclusaoTarefa.objects.exists())

    def test_excluir_tarefa_do_outro_responde_404(self):
        resposta = self.client.post(
            reverse("financas:excluir_tarefa", args=[self.tarefa_dela.pk])
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(Tarefa.objects.filter(pk=self.tarefa_dela.pk).exists())

    def test_excluir_exige_post(self):
        resposta = self.client.get(
            reverse("financas:excluir_tarefa", args=[self.tarefa.pk])
        )
        self.assertEqual(resposta.status_code, 405)


class AcoesExigemLoginTests(BaseRotina):
    def test_acoes_redirecionam_anonimo_para_login(self):
        self.client.logout()
        urls = [
            ("get", reverse("financas:rotina")),
            ("post", reverse("financas:concluir_tarefa", args=[self.tarefa.pk])),
            (
                "post",
                reverse("financas:desfazer_conclusao_tarefa", args=[self.tarefa.pk]),
            ),
            ("get", reverse("financas:editar_tarefa", args=[self.tarefa.pk])),
            ("post", reverse("financas:excluir_tarefa", args=[self.tarefa.pk])),
        ]
        for metodo, url in urls:
            with self.subTest(url=url):
                resposta = getattr(self.client, metodo)(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertTrue(resposta.url.startswith(reverse("financas:login")))
