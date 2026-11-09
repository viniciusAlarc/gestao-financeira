"""Acesso pelo celular (P2-9): com o IP da máquina em `ALLOWED_HOSTS`, o login abre;
fora da lista, o Django responde 400 (`DisallowedHost`).

O script `scripts/preparar_acesso_celular.sh` grava esse IP no `.env`. Estes testes provam
o efeito no Django, sem subir servidor: cliente de teste com `HTTP_HOST` explícito. O IP e
o host usados aqui são inventados; nenhum valor do `.env` real entra na suíte.
"""

from django.test import SimpleTestCase, override_settings
from django.urls import reverse

IP_DA_REDE = "192.168.15.15"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", IP_DA_REDE])
class AcessoCelularTests(SimpleTestCase):
    def test_login_abre_pelo_ip_da_maquina_com_porta(self):
        resposta = self.client.get(
            reverse("financas:login"), headers={"host": f"{IP_DA_REDE}:8000"}
        )
        self.assertEqual(resposta.status_code, 200)

    def test_host_fora_do_allowed_hosts_recebe_400(self):
        resposta = self.client.get(
            reverse("financas:login"), headers={"host": "192.168.15.99:8000"}
        )
        self.assertEqual(resposta.status_code, 400)

    @override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1"])
    def test_ip_sem_a_linha_no_env_recebe_400(self):
        # É a situação do P2-9 antes do script: `.env` ausente, só o padrão do Django.
        resposta = self.client.get(
            reverse("financas:login"), headers={"host": f"{IP_DA_REDE}:8000"}
        )
        self.assertEqual(resposta.status_code, 400)
