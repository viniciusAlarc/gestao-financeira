"""Filtros de template do app.

`dinheiro` formata Decimal como moeda pt-BR: 1234.56 vira "R$ 1.234,56" e
-1234.56 vira "-R$ 1.234,56". Existe porque o WSL não tem o locale pt_BR
instalado, então o `localize` do Django não garante vírgula decimal.
"""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def dinheiro(valor):
    """Decimal → "R$ 1.234,56". Valor fora do formato vira string vazia."""
    try:
        numero = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        return ""
    sinal = "-" if numero < 0 else ""
    inteiro, _, centavos = f"{abs(numero):.2f}".partition(".")
    milhar = f"{int(inteiro):,}".replace(",", ".")
    return f"{sinal}R$ {milhar},{centavos}"
