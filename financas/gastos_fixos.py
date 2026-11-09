"""Regras dos gastos fixos mensais (decisão de 2026-11-08).

O cadastro (`GastoFixo`) é a fonte; o `Previsto` de cada mês nasce dele. A
geração é idempotente: a restrição única `(fixo, competencia)` é a última linha
de defesa, e `get_or_create` cobre o caso normal.
"""

import calendar
from datetime import date

from django.utils import timezone

from .models import GastoFixo, Previsto, TipoValor


def _vencimento_do_mes(gasto: GastoFixo, referencia: date) -> date:
    """Dia do cadastro no mês de referência; mês curto cai no último dia."""
    ultimo_dia = calendar.monthrange(referencia.year, referencia.month)[1]
    return date(
        referencia.year,
        referencia.month,
        min(gasto.dia_vencimento, ultimo_dia),
    )


def garantir_previstos_do_mes(referencia: date | None = None) -> None:
    """Cria o previsto do mês de referência para cada gasto fixo ativo.

    A referência padrão é hoje; o parâmetro existe para os testes de virada de
    mês. Chamar de novo no mesmo mês não duplica.
    """
    referencia = referencia or timezone.localdate()
    competencia = referencia.replace(day=1)

    ativos = GastoFixo.objects.filter(ativo=True).select_related(
        "categoria", "conta"
    )
    for gasto in ativos:
        Previsto.objects.get_or_create(
            fixo=gasto,
            competencia=competencia,
            defaults={
                "descricao": gasto.descricao,
                "valor": gasto.valor,
                "vencimento": _vencimento_do_mes(gasto, referencia),
                "tipo": TipoValor.DESPESA,
                "categoria": gasto.categoria,
                "conta": gasto.conta,
                "status": Previsto.Status.ABERTO,
            },
        )


def atualizar_previsto_do_mes(
    gasto: GastoFixo, referencia: date | None = None
) -> None:
    """Faz o previsto do mês corrente, se aberto, acompanhar a edição do cadastro.

    Mês pago ou ignorado não muda: o histórico daquele mês fica como estava.
    """
    referencia = referencia or timezone.localdate()
    competencia = referencia.replace(day=1)
    Previsto.objects.filter(
        fixo=gasto,
        competencia=competencia,
        status=Previsto.Status.ABERTO,
    ).update(
        descricao=gasto.descricao,
        valor=gasto.valor,
        vencimento=_vencimento_do_mes(gasto, referencia),
        categoria=gasto.categoria,
        conta=gasto.conta,
    )
