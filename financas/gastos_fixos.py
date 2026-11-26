"""Regras dos gastos fixos mensais e das entradas fixas (2026-11-08/22).

O cadastro (`GastoFixo` e `EntradaFixa`) é a fonte; o `Previsto` de cada mês
nasce dele. A geração é idempotente: a restrição única `(fixo, competencia)` ou
`(entrada_fixa, competencia)` é a última linha de defesa, e `get_or_create`
cobre o caso normal.

Decisão do dono de 2026-11-22: a entrada fixa gera um previsto de **receita**
por mês; ela não entra no gasto do mês nem no previsto em aberto de despesas.
"""

import calendar
from datetime import date

from django.utils import timezone

from .models import EntradaFixa, GastoFixo, Previsto, TipoValor


def _dia_no_mes(dia: int, referencia: date) -> date:
    """Dia pedido no mês de referência; mês curto cai no último dia."""
    ultimo_dia = calendar.monthrange(referencia.year, referencia.month)[1]
    return date(referencia.year, referencia.month, min(dia, ultimo_dia))


def garantir_previstos_do_mes(referencia: date | None = None) -> None:
    """Cria o previsto do mês de referência para cada cadastro fixo ativo.

    A referência padrão é hoje; o parâmetro existe para os testes de virada de
    mês. Chamar de novo no mesmo mês não duplica. Despesa vem do `GastoFixo`;
    receita vem da `EntradaFixa`.
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
                "vencimento": _dia_no_mes(gasto.dia_vencimento, referencia),
                "tipo": TipoValor.DESPESA,
                "categoria": gasto.categoria,
                "conta": gasto.conta,
                "status": Previsto.Status.ABERTO,
            },
        )

    entradas = EntradaFixa.objects.filter(ativo=True).select_related(
        "categoria", "conta"
    )
    for entrada in entradas:
        Previsto.objects.get_or_create(
            entrada_fixa=entrada,
            competencia=competencia,
            defaults={
                "descricao": entrada.descricao,
                "valor": entrada.valor,
                "vencimento": _dia_no_mes(entrada.dia_recebimento, referencia),
                "tipo": TipoValor.RECEITA,
                "categoria": entrada.categoria,
                "conta": entrada.conta,
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
        vencimento=_dia_no_mes(gasto.dia_vencimento, referencia),
        categoria=gasto.categoria,
        conta=gasto.conta,
    )


def atualizar_previsto_da_entrada(
    entrada: EntradaFixa, referencia: date | None = None
) -> None:
    """Faz o previsto de receita do mês, se aberto, acompanhar o cadastro.

    Mesma regra do gasto fixo: mês pago ("Pago" = `ignorado`) não muda.
    """
    referencia = referencia or timezone.localdate()
    competencia = referencia.replace(day=1)
    Previsto.objects.filter(
        entrada_fixa=entrada,
        competencia=competencia,
        status=Previsto.Status.ABERTO,
    ).update(
        descricao=entrada.descricao,
        valor=entrada.valor,
        vencimento=_dia_no_mes(entrada.dia_recebimento, referencia),
        categoria=entrada.categoria,
        conta=entrada.conta,
    )
