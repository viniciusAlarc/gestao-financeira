"""Telas do app.

Fase 2 do plano (2026-11-01): a tela inicial responde, sem esforço, "quanto tenho hoje,
quanto gastei neste mês e o que está comprometido à frente".
"""

from datetime import date, timedelta
from decimal import Decimal
from itertools import groupby
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CategoriaEdicaoForm,
    CategoriaForm,
    GastoFixoForm,
    MovimentoRapidoForm,
    PrevistoForm,
)
from .gastos_fixos import atualizar_previsto_do_mes, garantir_previstos_do_mes
from .models import Categoria, Conta, GastoFixo, Movimento, Previsto, TipoValor
from .templatetags.financas_extra import dinheiro

ZERO = Decimal("0.00")


def _mes_da_querystring(request):
    """Mês pedido em `?mes=AAAA-MM`; ausente ou inválido cai no mês corrente."""
    valor = request.GET.get("mes", "")
    try:
        ano, mes = (int(parte) for parte in valor.split("-"))
        return date(ano, mes, 1)
    except (TypeError, ValueError, OverflowError):
        return timezone.localdate().replace(day=1)


def _mes_anterior(primeiro_dia):
    return (primeiro_dia - timedelta(days=1)).replace(day=1)


def _mes_seguinte(primeiro_dia):
    return (primeiro_dia.replace(day=28) + timedelta(days=4)).replace(day=1)


def _url_do_mes(nome_rota, quando):
    """URL limpa no mês corrente; `?mes=AAAA-MM` quando a data é de outro mês."""
    url = reverse(nome_rota)
    if quando.replace(day=1) == timezone.localdate().replace(day=1):
        return url
    return f"{url}?mes={quando:%Y-%m}"


@login_required
def inicio(request):
    """Os três números da tela inicial, calculados a cada leitura (nunca guardados).

    Leituras decididas em 2026-11-02, registradas no PROGRESS.md:
    - Saldo: todas as contas, pela regra do plano (saldos iniciais + receitas − despesas).
    - Gasto do mês: despesas do mês corrente, de todas as contas, menos as
      categorias marcadas como fora do gasto (ex.: Investimento).
    - Previsto em aberto: só despesas abertas (decisão do dono).
    """
    hoje = timezone.localdate()

    # Antes de somar, garante que o mês corrente tem o previsto de cada gasto
    # fixo ativo. Idempotente; o custo é uma consulta aos cadastros.
    garantir_previstos_do_mes()

    saldo_inicial = Conta.objects.aggregate(total=Sum("saldo_inicial"))["total"] or ZERO
    totais = Movimento.objects.filter(cancelado=False).aggregate(
        receitas=Sum("valor", filter=Q(tipo=TipoValor.RECEITA)),
        despesas=Sum("valor", filter=Q(tipo=TipoValor.DESPESA)),
    )
    saldo = saldo_inicial + (totais["receitas"] or ZERO) - (totais["despesas"] or ZERO)

    gasto_mes = (
        Movimento.objects.filter(
            cancelado=False,
            tipo=TipoValor.DESPESA,
            data__year=hoje.year,
            data__month=hoje.month,
            categoria__entra_no_gasto=True,
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
    """Fase 3: lançar em 3 toques e ver a lista do mês, que pode ser navegado.

    Decisões de 2026-11-03: o tipo vem da categoria escolhida e a conta é a
    marcada como padrão. Sem conta padrão ativa, a tela explica o que fazer em
    vez de escolher uma conta em silêncio. O total exibido é o de despesas.
    Decisão de 2026-11-08: a data do lançamento é editável e nasce hoje; a lista
    aceita `?mes=AAAA-MM` e movimento desfeito não aparece.
    """
    hoje = timezone.localdate()
    mes = _mes_da_querystring(request)
    conta_padrao = Conta.objects.filter(padrao=True, ativa=True).first()
    tem_categoria_ativa = Categoria.objects.filter(ativa=True).exists()
    pode_lancar = conta_padrao is not None and tem_categoria_ativa

    form = MovimentoRapidoForm(request.POST or None) if pode_lancar else None

    if request.method == "POST" and form is not None and form.is_valid():
        movimento = form.save(commit=False)
        movimento.data = form.cleaned_data["data"] or hoje
        movimento.tipo = movimento.categoria.tipo
        movimento.conta = conta_padrao
        movimento.criado_por = request.user
        movimento.save()
        messages.success(
            request,
            f"Lançado: {movimento.categoria.nome} · {dinheiro(movimento.valor)}",
        )
        return redirect(_url_do_mes("financas:lancamentos", movimento.data))

    movimentos = (
        Movimento.objects.filter(
            cancelado=False, data__year=mes.year, data__month=mes.month
        )
        .select_related("categoria", "conta", "previsto")
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
            "mes_atual": mes,
            "mes_anterior": _mes_anterior(mes),
            "mes_seguinte": _mes_seguinte(mes),
        },
    )


def _motivo_sem_edicao(movimento):
    """Explica por que o lançamento não entra no formulário de edição."""
    if movimento.cancelado:
        return "Este lançamento foi desfeito e não pode ser editado."
    if movimento.origem != Movimento.Origem.MANUAL:
        return "Lançamento importado do Inter não pode ser editado: o banco é a fonte."
    return (
        "Este lançamento veio de um previsto pago. "
        "Desfaça o pagamento e lance de novo."
    )


@login_required
def editar_movimento(request, pk):
    """Corrige data, valor e categoria de um lançamento manual (2026-11-08).

    Importado do Inter e lançamento vindo de previsto pago não entram: o primeiro
    tem o banco como fonte; o segundo desalinharia o previsto do movimento.
    """
    movimento = get_object_or_404(Movimento, pk=pk)
    if not movimento.pode_ser_editado:
        messages.error(request, _motivo_sem_edicao(movimento))
        return redirect(_url_do_mes("financas:lancamentos", movimento.data))

    # O ModelForm zera `instance.data` na validação quando o campo vem vazio;
    # a data original precisa ser guardada antes para o caso de a pessoa limpar.
    data_original = movimento.data
    form = MovimentoRapidoForm(request.POST or None, instance=movimento)
    if request.method == "POST" and form.is_valid():
        movimento = form.save(commit=False)
        movimento.data = form.cleaned_data["data"] or data_original
        movimento.tipo = movimento.categoria.tipo
        movimento.save()
        messages.success(
            request,
            f"Atualizado: {movimento.categoria.nome} · {dinheiro(movimento.valor)}",
        )
        return redirect(_url_do_mes("financas:lancamentos", movimento.data))

    return render(
        request, "editar_movimento.html", {"form": form, "movimento": movimento}
    )


@login_required
@require_POST
@transaction.atomic
def desfazer_movimento(request, pk):
    """Desfaz um lançamento manual sem apagar o registro (decisão de 2026-11-08).

    Se o lançamento veio do botão "Paguei", o previsto volta para aberto. O
    desfazer é idempotente e só roda para lançamento manual ativo: importado do
    Inter tem o banco como fonte e não se desfaz aqui.
    """
    movimento = get_object_or_404(Movimento.objects.select_for_update(), pk=pk)
    destino = _url_do_mes("financas:lancamentos", movimento.data)

    if movimento.cancelado:
        messages.info(request, "Este lançamento já foi desfeito.")
        return redirect(destino)
    if movimento.origem != Movimento.Origem.MANUAL:
        messages.error(
            request,
            "Lançamento importado do Inter não pode ser desfeito: o banco é a fonte.",
        )
        return redirect(destino)

    previsto_reaberto = False
    previsto = getattr(movimento, "previsto", None)
    if previsto is not None and previsto.status == Previsto.Status.PAGO:
        previsto.status = Previsto.Status.ABERTO
        previsto.movimento = None
        previsto.save(update_fields=["status", "movimento"])
        previsto_reaberto = True

    movimento.cancelado = True
    movimento.cancelado_em = timezone.now()
    movimento.cancelado_por = request.user
    movimento.save(update_fields=["cancelado", "cancelado_em", "cancelado_por"])

    texto = (
        f"Desfeito: {movimento.descricao or movimento.categoria.nome} · "
        f"{dinheiro(movimento.valor)}"
    )
    if previsto_reaberto:
        texto += " O previsto voltou para aberto."
    messages.success(request, texto)
    return redirect(destino)


@login_required
def previstos(request):
    """Fase 4: gastos fixos mensais, instâncias do mês e previstos avulsos.

    Decisão de 2026-11-08: o previsto nasce de um cadastro fixo e cada mês gera
    a instância daquele mês; o avulso continua como opção secundária. Ignorar e
    reabrir seguem a máquina de estados (par simétrico, G10).
    """
    garantir_previstos_do_mes()
    conta_padrao = Conta.objects.filter(padrao=True, ativa=True).first()
    tem_categoria_despesa_ativa = Categoria.objects.filter(
        ativa=True, tipo=TipoValor.DESPESA
    ).exists()
    pode_criar = conta_padrao is not None and tem_categoria_despesa_ativa

    form_fixo = GastoFixoForm(prefix="fixo") if pode_criar else None
    form = PrevistoForm() if pode_criar else None

    if request.method == "POST" and pode_criar:
        enviou_fixo = "fixo-dia_vencimento" in request.POST
        if enviou_fixo:
            form_fixo = GastoFixoForm(request.POST, prefix="fixo")
            if form_fixo.is_valid():
                gasto = form_fixo.save(commit=False)
                gasto.conta = conta_padrao
                gasto.save()
                garantir_previstos_do_mes()
                messages.success(
                    request,
                    f"Gasto fixo: {gasto.descricao} · "
                    f"todo dia {gasto.dia_vencimento}",
                )
                return redirect("financas:previstos")
        else:
            form = PrevistoForm(request.POST)
            if form.is_valid():
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

    gastos_fixos = GastoFixo.objects.select_related(
        "categoria", "conta"
    ).order_by("descricao")
    previstos_abertos = (
        Previsto.objects.filter(
            status=Previsto.Status.ABERTO, tipo=TipoValor.DESPESA
        )
        .select_related("categoria", "conta", "fixo")
        .order_by("vencimento", "id")
    )
    previstos_ignorados = (
        Previsto.objects.filter(
            status=Previsto.Status.IGNORADO, tipo=TipoValor.DESPESA
        )
        .select_related("categoria", "conta", "fixo")
        .order_by("-vencimento", "id")
    )

    return render(
        request,
        "previstos.html",
        {
            "form": form,
            "form_fixo": form_fixo,
            "gastos_fixos": gastos_fixos,
            "previstos": previstos_abertos,
            "ignorados": previstos_ignorados,
            "conta_padrao": conta_padrao,
            "tem_categoria_despesa_ativa": tem_categoria_despesa_ativa,
        },
    )


@login_required
def editar_gasto_fixo(request, pk):
    """Edita o cadastro do gasto fixo (decisão de 2026-11-08).

    O previsto do mês corrente, se ainda aberto, acompanha descrição, valor,
    dia, categoria e conta. Mês pago ou ignorado não muda. Desativar para de
    gerar os meses seguintes; reativar volta a gerar a partir do mês corrente.
    """
    gasto = get_object_or_404(GastoFixo, pk=pk)
    form = GastoFixoForm(request.POST or None, instance=gasto, prefix="fixo")
    if request.method == "POST" and form.is_valid():
        gasto = form.save()
        atualizar_previsto_do_mes(gasto)
        messages.success(
            request, f"Gasto fixo atualizado: {gasto.descricao}"
        )
        return redirect("financas:previstos")

    return render(
        request,
        "editar_gasto_fixo.html",
        {"form": form, "gasto": gasto},
    )


@login_required
def categorias(request):
    """Cria e lista categorias por tipo (decisão de 2026-11-08).

    O tipo é escolhido na criação e fica fixo; desativar tira a categoria dos
    formulários sem apagar o histórico. Nome repetido no mesmo tipo é recusado.
    """
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f"Categoria criada: {categoria.nome}")
            return redirect("financas:categorias")
    else:
        form = CategoriaForm()

    categorias_despesa = Categoria.objects.filter(
        tipo=TipoValor.DESPESA
    ).order_by("-ativa", "nome")
    categorias_receita = Categoria.objects.filter(
        tipo=TipoValor.RECEITA
    ).order_by("-ativa", "nome")

    return render(
        request,
        "categorias.html",
        {
            "form": form,
            "categorias_despesa": categorias_despesa,
            "categorias_receita": categorias_receita,
        },
    )


@login_required
def editar_categoria(request, pk):
    """Edita nome, ativa e 'entra no gasto'; o tipo fica fixo (2026-11-08)."""
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaEdicaoForm(request.POST or None, instance=categoria)
    if request.method == "POST" and form.is_valid():
        categoria = form.save()
        messages.success(request, f"Categoria atualizada: {categoria.nome}")
        return redirect("financas:categorias")
    return render(
        request,
        "editar_categoria.html",
        {"form": form, "categoria": categoria},
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
@require_POST
@transaction.atomic
def ignorar_previsto(request, pk):
    """Tira um previsto em aberto da lista sem criar movimento (2026-11-08).

    Par simétrico de `reabrir_previsto` (G10) e idempotente.
    """
    previsto = get_object_or_404(Previsto.objects.select_for_update(), pk=pk)
    if previsto.status == Previsto.Status.IGNORADO:
        messages.info(request, "Este previsto já está ignorado.")
    elif previsto.status != Previsto.Status.ABERTO:
        messages.error(request, "Só um previsto em aberto pode ser ignorado.")
    else:
        previsto.status = Previsto.Status.IGNORADO
        previsto.save(update_fields=["status"])
        messages.success(
            request,
            f"Ignorado: {previsto.descricao} · {dinheiro(previsto.valor)}",
        )
    return redirect("financas:previstos")


@login_required
@require_POST
@transaction.atomic
def reabrir_previsto(request, pk):
    """Devolve um previsto ignorado para aberto (par do `ignorar_previsto`)."""
    previsto = get_object_or_404(Previsto.objects.select_for_update(), pk=pk)
    if previsto.status == Previsto.Status.ABERTO:
        messages.info(request, "Este previsto já está aberto.")
    elif previsto.status != Previsto.Status.IGNORADO:
        messages.error(
            request,
            "Só um previsto ignorado pode ser reaberto. Para desfazer um pagamento, "
            "use o desfazer do lançamento.",
        )
    else:
        previsto.status = Previsto.Status.ABERTO
        previsto.save(update_fields=["status"])
        messages.success(
            request,
            f"Reaberto: {previsto.descricao} · {dinheiro(previsto.valor)}",
        )
    return redirect("financas:previstos")


@login_required
def relatorio(request):
    """Fase 5: para onde foi o dinheiro do mês, por categoria.

    Só despesas do mês escolhido em `?mes=AAAA-MM`, em ordem decrescente de
    total, fora as categorias marcadas como fora do gasto e os movimentos
    desfeitos. O percentual é calculado sobre o total de despesas do mês. A soma
    das categorias é o mesmo total; a verificação do plano é coberta pela suíte.
    """
    hoje = timezone.localdate()
    mes = _mes_da_querystring(request)
    despesas = Movimento.objects.filter(
        cancelado=False,
        tipo=TipoValor.DESPESA,
        data__year=mes.year,
        data__month=mes.month,
        categoria__entra_no_gasto=True,
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
            "mes_atual": mes,
            "mes_anterior": _mes_anterior(mes),
            "mes_seguinte": _mes_seguinte(mes),
        },
    )
