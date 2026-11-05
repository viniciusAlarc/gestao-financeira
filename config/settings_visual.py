"""Settings descartável da conferência visual a 375px (P4-4, rodada 2026-11-05).

NÃO é configuração do app: existe só para levantar as telas com dado inventado,
num SQLite em /tmp, sem encostar no db.sqlite3 real. Pode ser removido depois da
rodada.

Como usar (dois comandos, com o .venv do projeto):

    .venv/bin/python manage.py migrate --settings config.settings_visual
    .venv/bin/python manage.py runserver 0.0.0.0:8010 --noreload --settings config.settings_visual

O `VisualFerramentaMiddleware`, no fim da cadeia, entra como o usuário "visual"
(login automático, porque a tela exige login) e semeia o dado inventado no
primeiro acesso — depois do `migrate`, que é quando as tabelas passam a existir.
"""

import threading
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .settings import *  # noqa: F401,F403

# Banco descartável: fica fora do repositório e some quando o dono limpar /tmp.
BASE_VISUAL = Path("/tmp/gestao-visual")
BASE_VISUAL.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_VISUAL / "db.sqlite3",
    }
}

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Igual ao settings.py, mais o middleware do fim (login automático + semeadura).
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.settings_visual.VisualFerramentaMiddleware",
]

USUARIO_VISUAL = "visual"

_semeadura_trava = threading.Lock()
_semeado = False


def _dia_do_mes(hoje, dia):
    """Data dentro do mês corrente (para o relatório do mês enxergar a despesa)."""
    return date(hoje.year, hoje.month, dia)


def _semear():
    """Cria uma conta, categorias, movimentos e previstos de mentira, uma vez só.

    Nada aqui é dado real: valores e descrições foram inventados para a conferência.
    """
    global _semeado
    if _semeado:
        return
    with _semeadura_trava:
        if _semeado:
            return

        from django.contrib.auth.models import User
        from django.utils import timezone

        from financas.models import Categoria, Conta, Movimento, Previsto, TipoValor

        hoje = timezone.localdate()
        usuario, _ = User.objects.get_or_create(username=USUARIO_VISUAL)

        if Movimento.objects.exists():
            _semeado = True
            return

        conta, _ = Conta.objects.get_or_create(
            nome="Conta conjunta de teste",
            defaults={
                "tipo": Conta.Tipo.CORRENTE,
                "saldo_inicial": Decimal("2500.00"),
                "ativa": True,
                "padrao": True,
            },
        )

        def categoria(nome, tipo=TipoValor.DESPESA):
            obj, _ = Categoria.objects.get_or_create(
                nome=nome, tipo=tipo, defaults={"ativa": True}
            )
            return obj

        mercado = categoria("Mercado")
        moradia = categoria("Moradia")
        transporte = categoria("Transporte")
        saude = categoria("Saúde")
        cartao = categoria("Cartão de crédito parcelado")

        lancamentos = [
            (3, Decimal("512.34"), mercado, "Feira da semana"),
            (1, Decimal("1800.00"), moradia, "Aluguel de novembro"),
            (2, Decimal("89.90"), transporte, "Combustível"),
            (4, Decimal("289.90"), mercado, "Mercado do mês"),
            (2, Decimal("12750.00"), saude, "Tratamento dentário"),
            (5, Decimal("431.20"), mercado, "Compras do fim de semana"),
            (5, Decimal("45.50"), transporte, "Estacionamento"),
            (4, Decimal("1234.56"), cartao, "Parcela do cartão"),
        ]
        for dia, valor, cat, descricao in lancamentos:
            Movimento.objects.create(
                data=_dia_do_mes(hoje, min(dia, 28)),
                valor=valor,
                tipo=TipoValor.DESPESA,
                conta=conta,
                categoria=cat,
                descricao=descricao,
                criado_por=usuario,
            )

        previstos = [
            ("Aluguel de dezembro", Decimal("1800.00"), hoje + timedelta(days=5), moradia),
            ("Internet fibra 500 megas", Decimal("119.90"), hoje + timedelta(days=12), moradia),
            (
                "Parcela do financiamento do carro usado com seguro e taxas incluídas do mês",
                Decimal("99999.99"),
                hoje + timedelta(days=8),
                transporte,
            ),
            ("Escola das crianças", Decimal("850.00"), hoje + timedelta(days=20), saude),
            ("Dentista", Decimal("350.00"), hoje + timedelta(days=3), saude),
            ("Fatura do cartão", Decimal("1234.56"), hoje + timedelta(days=15), cartao),
        ]
        for descricao, valor, vencimento, cat in previstos:
            Previsto.objects.create(
                descricao=descricao,
                valor=valor,
                vencimento=vencimento,
                tipo=TipoValor.DESPESA,
                categoria=cat,
                conta=conta,
                status=Previsto.Status.ABERTO,
            )

        _semeado = True


class VisualFerramentaMiddleware:
    """Entra como o usuário de teste e garante o dado inventado, só nesta configuração."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.contrib.auth.models import User

        request.user = User.objects.get_or_create(username=USUARIO_VISUAL)[0]
        _semear()
        return self.get_response(request)
