"""Segurança e privacidade — regressão da rodada 2026-11-05-b (T3).

O app vai rodar para duas pessoas, na rede de casa, por HTTP, como PWA no celular.
Estes testes provam o que já está garantido hoje e não pode regredir:

- tela de dado só abre com login; o login é a única porta pública;
- escrita (pagar previsto, sair) só por POST e com o token CSRF da sessão;
- admin do Django só para staff;
- Host fora de ALLOWED_HOSTS é recusado com 400;
- cabeçalhos e cookies de segurança que o Django já entrega por padrão.

Dado de teste é inventado (regra 2 do AGENTS.md). O Django cria um banco descartável
para a suíte; o `db.sqlite3` real nunca é aberto. Os achados e o que ainda falta
estão em `docs-dev/rodada-2026-11-05-b/s3-seguranca.md`.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Categoria, Conta, Movimento, Previsto, TipoValor

SENHA = "senha-de-teste-t3"


class BaseSeguranca(TestCase):
    """Usuário comum, conta padrão, categoria e um previsto em aberto.

    É o mínimo para exercitar login, CSRF do "Paguei" e o estado do previsto
    depois de uma tentativa recusada.
    """

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="teste", password=SENHA
        )
        self.conta = Conta.objects.create(
            nome="Carteira",
            tipo=Conta.Tipo.CARTEIRA,
            saldo_inicial=Decimal("10.00"),
            padrao=True,
        )
        self.categoria = Categoria.objects.create(
            nome="Mercado", tipo=TipoValor.DESPESA
        )
        self.previsto = Previsto.objects.create(
            descricao="Internet",
            valor=Decimal("100.00"),
            vencimento=date(2026, 12, 10),
            tipo=TipoValor.DESPESA,
            categoria=self.categoria,
            conta=self.conta,
        )


class LoginObrigatorioTests(BaseSeguranca):
    """Anônimo não enxerga tela de dado; a única página pública é o login."""

    def test_views_de_dado_redirecionam_anonimo_para_login(self):
        """Toda tela nomeada do app leva ao login, preservando o destino em `next`."""
        urls = [
            reverse("financas:inicio"),
            reverse("financas:lancamentos"),
            reverse("financas:previstos"),
            reverse("financas:relatorio"),
        ]
        login = reverse("financas:login")
        for url in urls:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertTrue(resposta.url.startswith(f"{login}?next="))

    def test_pagar_previsto_recusa_anonimo_e_nao_paga(self):
        """O POST anônimo não pode ter efeito: o previsto continua aberto e sem movimento."""
        resposta = self.client.post(
            reverse("financas:pagar_previsto", args=[self.previsto.pk])
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("financas:login")))
        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.status, Previsto.Status.ABERTO)
        self.assertIsNone(self.previsto.movimento)
        self.assertFalse(Movimento.objects.exists())

    def test_get_de_pagar_previsto_anonimo_tambem_leva_ao_login(self):
        """O `login_required` roda antes do `require_POST`: anônimo vê o login, não 405."""
        resposta = self.client.get(
            reverse("financas:pagar_previsto", args=[self.previsto.pk])
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("financas:login")))

    def test_login_e_publico(self):
        """O login precisa abrir sem sessão; é a porta de entrada do app."""
        resposta = self.client.get(reverse("financas:login"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'name="password"', html=False)

    def test_usuario_logado_abre_as_quatro_telas(self):
        """Controle positivo: as quatro telas existem e respondem 200 com sessão."""
        self.assertTrue(self.client.login(username="teste", password=SENHA))
        for url in [
            reverse("financas:inicio"),
            reverse("financas:lancamentos"),
            reverse("financas:previstos"),
            reverse("financas:relatorio"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_erro_de_login_nao_revela_se_o_usuario_existe(self):
        """Usuário inexistente e senha errada mostram a mesma mensagem (não enumerar contas)."""
        tentativas = [
            {"username": "nao-existe", "password": SENHA},
            {"username": "teste", "password": "senha-errada"},
        ]
        for dados in tentativas:
            with self.subTest(username=dados["username"]):
                resposta = self.client.post(reverse("financas:login"), dados)
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, "Não foi possível entrar")


class EscritaSoPorPostComCsrfTests(BaseSeguranca):
    """Pagar previsto e sair mudam estado: só por POST e com o token da sessão.

    Usa um cliente com `enforce_csrf_checks=True` (o cliente de teste normal ignora
    o CSRF, o que esconderia a falta do token em produção).
    """

    def setUp(self):
        super().setUp()
        self.cliente = Client(enforce_csrf_checks=True)
        self.assertTrue(self.cliente.login(username="teste", password=SENHA))
        # O GET da tela autenticada emite o cookie `csrftoken` (o "Sair" carrega o token).
        self.cliente.get(reverse("financas:inicio"))
        self.token = self.cliente.cookies["csrftoken"].value

    def url_pagar(self):
        return reverse("financas:pagar_previsto", args=[self.previsto.pk])

    def test_pagar_por_get_da_405(self):
        """Pagar é ação de escrita: GET não pode disparar a criação do movimento."""
        resposta = self.cliente.get(self.url_pagar())
        self.assertEqual(resposta.status_code, 405)
        self.assertFalse(Movimento.objects.exists())

    def test_pagar_sem_token_csrf_da_403_e_nao_paga(self):
        """POST de outra origem (sem o token da sessão) é recusado sem efeito."""
        resposta = self.cliente.post(self.url_pagar())
        self.assertEqual(resposta.status_code, 403)
        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.status, Previsto.Status.ABERTO)
        self.assertFalse(Movimento.objects.exists())

    def test_pagar_com_token_csrf_funciona(self):
        """Controle positivo: com o token da própria sessão, o pagamento acontece."""
        resposta = self.cliente.post(
            self.url_pagar(), {"csrfmiddlewaretoken": self.token}
        )
        self.assertEqual(resposta.status_code, 302)
        self.previsto.refresh_from_db()
        self.assertEqual(self.previsto.status, Previsto.Status.PAGO)
        self.assertEqual(Movimento.objects.count(), 1)

    def test_logout_por_get_da_405(self):
        """Sair é POST (Django 5): GET por link/histórico não derruba a sessão."""
        self.assertEqual(
            self.cliente.get(reverse("financas:logout")).status_code, 405
        )
        self.assertEqual(
            Client().get(reverse("financas:logout")).status_code, 405
        )

    def test_logout_sem_token_csrf_da_403_e_mantem_sessao(self):
        """Sair sem o token é recusado: a sessão continua valendo."""
        resposta = self.cliente.post(reverse("financas:logout"))
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(
            self.cliente.get(reverse("financas:inicio")).status_code, 200
        )

    def test_logout_com_token_csrf_encerra_sessao(self):
        """Controle positivo: com token, sai e a tela de dado volta a pedir login."""
        resposta = self.cliente.post(
            reverse("financas:logout"), {"csrfmiddlewaretoken": self.token}
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("financas:login")))
        self.assertEqual(
            self.cliente.get(reverse("financas:inicio")).status_code, 302
        )

    def test_login_post_sem_token_csrf_da_403(self):
        """O próprio login exige CSRF, para não servir de 'login CSRF' a outra origem."""
        anonimo = Client(enforce_csrf_checks=True)
        resposta = anonimo.post(
            reverse("financas:login"), {"username": "teste", "password": SENHA}
        )
        self.assertEqual(resposta.status_code, 403)


class AdminExigeStaffTests(BaseSeguranca):
    """O admin é a tela de manutenção dos dados: só entra quem é staff."""

    def test_anonimo_nao_entra_no_admin(self):
        resposta = self.client.get(reverse("admin:index"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/login/", resposta.url)

    def test_usuario_comum_nao_entra_no_admin(self):
        """Quem tem login do app (as duas pessoas do casal) não é staff."""
        self.assertTrue(self.client.login(username="teste", password=SENHA))
        self.assertFalse(self.usuario.is_staff)
        resposta = self.client.get(reverse("admin:index"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/login/", resposta.url)

    def test_staff_entra_no_admin(self):
        """Controle positivo: staff abre o admin, então o 302 acima é do controle de acesso."""
        get_user_model().objects.create_user(
            username="chefe", password=SENHA, is_staff=True
        )
        self.assertTrue(self.client.login(username="chefe", password=SENHA))
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1"])
class HostForaDaListaTests(TestCase):
    """ALLOWED_HOSTS barra requisição endereçada a um nome que não é o da casa.

    O override fixa a lista para o teste não depender do `.env` de quem roda a suíte
    (o Django ainda acrescenta "testserver", o host padrão do cliente, por fora).
    """

    def test_host_permitido_abre_o_login(self):
        resposta = self.client.get(reverse("financas:login"), HTTP_HOST="localhost")
        self.assertEqual(resposta.status_code, 200)

    def test_host_permitido_com_porta_abre_o_login(self):
        resposta = self.client.get(
            reverse("financas:login"), HTTP_HOST="127.0.0.1:8000"
        )
        self.assertEqual(resposta.status_code, 200)

    def test_host_desconhecido_recebe_400(self):
        resposta = self.client.get(
            reverse("financas:login"), HTTP_HOST="atacante.example"
        )
        self.assertEqual(resposta.status_code, 400)


class CabecalhosECookiesTests(BaseSeguranca):
    """Baseline de segurança que o Django entrega por padrão neste projeto.

    Se um dia alguém tirar um middleware ou mudar um default, é aqui que aparece.
    """

    def test_login_traz_cabecalhos_de_protecao(self):
        """Anti-clickjacking, sem adivinhar tipo de arquivo e sem vazar a URL de origem."""
        resposta = self.client.get(reverse("financas:login"))
        self.assertEqual(resposta.headers["X-Frame-Options"], "DENY")
        self.assertEqual(resposta.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resposta.headers["Referrer-Policy"], "same-origin")

    def test_cookie_de_sessao_e_httponly_e_samesite_lax(self):
        """O JS da página não lê o cookie de sessão, e ele não viaja em POST de outro site."""
        resposta = self.client.post(
            reverse("financas:login"), {"username": "teste", "password": SENHA}
        )
        self.assertEqual(resposta.status_code, 302)
        sessao = resposta.cookies["sessionid"]
        self.assertTrue(sessao["httponly"])
        self.assertEqual(sessao["samesite"], "Lax")

    def test_cookie_csrf_e_samesite_lax(self):
        """O token CSRF só é enviado em requisição do mesmo site (default do Django)."""
        resposta = self.client.get(reverse("financas:login"))
        self.assertEqual(resposta.cookies["csrftoken"]["samesite"], "Lax")
