"""Telas do app.

Fase 2 do plano (2026-11-01): a tela inicial responde, sem esforço, "quanto tenho hoje,
quanto gastei neste mês e o que está comprometido à frente".
"""

from decimal import Decimal
from itertools import groupby
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MovimentoRapidoForm, PrevistoForm
from .models import Categoria, Conta, Movimento, Previsto, TipoValor
from .templatetags.financas_extra import dinheiro

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


@login_required
def lancamentos(request):
    """Fase 3: lançar em 3 toques e ver a lista do mês corrente.

    Decisões de 2026-11-03: o tipo vem da categoria escolhida e a conta é a
    marcada como padrão. Sem conta padrão ativa, a tela explica o que fazer em
    vez de escolher uma conta em silêncio. O total exibido é o de despesas.
    """
    hoje = timezone.localdate()
    conta_padrao = Conta.objects.filter(padrao=True, ativa=True).first()
    tem_categoria_ativa = Categoria.objects.filter(ativa=True).exists()
    pode_lancar = conta_padrao is not None and tem_categoria_ativa

    form = MovimentoRapidoForm(request.POST or None) if pode_lancar else None

    if request.method == "POST" and form is not None and form.is_valid():
        movimento = form.save(commit=False)
        movimento.data = hoje
        movimento.tipo = movimento.categoria.tipo
        movimento.conta = conta_padrao
        movimento.criado_por = request.user
        movimento.save()
        messages.success(
            request,
            f"Lançado: {movimento.categoria.nome} · {dinheiro(movimento.valor)}",
        )
        return redirect("financas:lancamentos")

    movimentos = (
        Movimento.objects.filter(data__year=hoje.year, data__month=hoje.month)
        .select_related("categoria", "conta")
        .order_by("-data", "-id")
    )
    total_despesas = (
        movimentos.filter(tipo=TipoValor.DESPESA).aggregate(total=Sum("valor"))["total"]
        or ZERO
    )
    dias = [
        (dia, list(itens))
        for dia, itens in groupby(movimentos, key=attrgetter("data"))
    ]

    return render(
        request,
        "lancamentos.html",
        {
            "form": form,
            "dias": dias,
            "total_despesas": total_despesas,
            "conta_padrao": conta_padrao,
            "tem_categoria_ativa": tem_categoria_ativa,
            "hoje": hoje,
        },
    )


@login_required
def previstos(request):
    """Fase 4: cadastra gastos previstos e lista os que estão em aberto."""
    conta_padrao = Conta.objects.filter(padrao=True, ativa=True).first()
    tem_categoria_despesa_ativa = Categoria.objects.filter(
        ativa=True, tipo=TipoValor.DESPESA
    ).exists()
    pode_criar = conta_padrao is not None and tem_categoria_despesa_ativa

    form = PrevistoForm(request.POST or None) if pode_criar else None
    if request.method == "POST" and form is not None and form.is_valid():
        previsto = form.save(commit=False)
        previsto.tipo = TipoValor.DESPESA
        previsto.conta = conta_padrao
        previsto.status = Previsto.Status.ABERTO
        previsto.save()
        messages.success(
            request,
            f"Previsto: {previsto.descricao} · {dinheiro(previsto.valor)}",
        )
        return redirect("financas:previstos")

    previstos_abertos = (
        Previsto.objects.filter(
            status=Previsto.Status.ABERTO, tipo=TipoValor.DESPESA
        )
        .select_related("categoria", "conta")
        .order_by("vencimento", "id")
    )

    return render(
        request,
        "previstos.html",
        {
            "form": form,
            "previstos": previstos_abertos,
            "conta_padrao": conta_padrao,
            "tem_categoria_despesa_ativa": tem_categoria_despesa_ativa,
        },
    )


@login_required
@require_POST
@transaction.atomic
def pagar_previsto(request, pk):
    """Marca um previsto como pago e cria exatamente um movimento manual.

    O movimento usa a conta do próprio previsto, não a conta padrão: a padrão
    só decide onde um previsto novo nasce, e pode mudar depois.
    """
    hoje = timezone.localdate()
    previsto = get_object_or_404(
        Previsto.objects.select_for_update().filter(
            pk=pk,
            tipo=TipoValor.DESPESA,
        )
    )

    if previsto.status != Previsto.Status.ABERTO:
        messages.info(request, "Este previsto já não está em aberto.")
        return redirect("financas:previstos")

    movimento = Movimento.objects.create(
        data=hoje,
        valor=previsto.valor,
        tipo=TipoValor.DESPESA,
        conta=previsto.conta,
        categoria=previsto.categoria,
        descricao=previsto.descricao,
        origem=Movimento.Origem.MANUAL,
        criado_por=request.user,
    )
    previsto.movimento = movimento
    previsto.status = Previsto.Status.PAGO
    previsto.save(update_fields=["movimento", "status"])

    messages.success(
        request,
        f"Pago: {previsto.descricao} · {dinheiro(previsto.valor)}",
    )
    return redirect("financas:previstos")


@login_required
def relatorio(request):
    """Fase 5: para onde foi o dinheiro do mês, por categoria.

    Só despesas do mês corrente, em ordem decrescente de total. O percentual é
    calculado sobre o total de despesas do mês. A soma das categorias é o mesmo
    total; a verificação do plano é coberta pela suíte.
    """
    hoje = timezone.localdate()
    despesas = Movimento.objects.filter(
        tipo=TipoValor.DESPESA,
        data__year=hoje.year,
        data__month=hoje.month,
    )
    total_despesas = despesas.aggregate(total=Sum("valor"))["total"] or ZERO
    por_categoria = (
        despesas.values("categoria__nome")
        .annotate(total=Sum("valor"))
        .order_by("-total", "categoria__nome")
    )
    linhas = []
    for linha in por_categoria:
        percentual = (
            (linha["total"] / total_despesas * 100).quantize(Decimal("0.1"))
            if total_despesas
            else ZERO
        )
        linhas.append(
            {
                "nome": linha["categoria__nome"],
                "total": linha["total"],
                "percentual": percentual,
            }
        )

    return render(
        request,
        "relatorio.html",
        {
            "linhas": linhas,
            "total_despesas": total_despesas,
            "hoje": hoje,
        },
    )
