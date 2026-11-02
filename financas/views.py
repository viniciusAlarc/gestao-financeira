"""Telas do app.

Fase 2 do plano (2026-11-01): a tela inicial responde, sem esforço, "quanto tenho hoje,
quanto gastei neste mês e o que está comprometido à frente".
"""

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render
from django.utils import timezone

from .models import Conta, Movimento, Previsto, TipoValor

ZERO = Decimal("0.00")


@login_required
def inicio(request):
    """Os três números da tela inicial, calculados a cada leitura (nunca guardados).

    Leituras decididas em 2026-11-02, registradas no PROGRESS.md:
    - Saldo: todas as contas, pela regra do plano (saldos iniciais + receitas − despesas).
    - Gasto do mês: despesas do mês corrente, de todas as contas.
    - Previsto em aberto: só despesas abertas (decisão do dono).
    """
    hoje = timezone.localdate()

    saldo_inicial = Conta.objects.aggregate(total=Sum("saldo_inicial"))["total"] or ZERO
    totais = Movimento.objects.aggregate(
        receitas=Sum("valor", filter=Q(tipo=TipoValor.RECEITA)),
        despesas=Sum("valor", filter=Q(tipo=TipoValor.DESPESA)),
    )
    saldo = saldo_inicial + (totais["receitas"] or ZERO) - (totais["despesas"] or ZERO)

    gasto_mes = (
        Movimento.objects.filter(
            tipo=TipoValor.DESPESA,
            data__year=hoje.year,
            data__month=hoje.month,
        ).aggregate(total=Sum("valor"))["total"]
        or ZERO
    )

    previsto_aberto = (
        Previsto.objects.filter(
            status=Previsto.Status.ABERTO, tipo=TipoValor.DESPESA
        ).aggregate(total=Sum("valor"))["total"]
        or ZERO
    )

    return render(
        request,
        "inicio.html",
        {
            "saldo": saldo,
            "gasto_mes": gasto_mes,
            "previsto_aberto": previsto_aberto,
        },
    )
