"""Formulários do app.

O formulário rápido da fase 3 lança com **valor e categoria**. O formulário da
fase 4 cria gastos previstos com descrição, vencimento, valor e categoria.
"""

from decimal import Decimal

from django import forms

from .models import Categoria, Movimento, Previsto, TipoValor


class ValorBrasileiroField(forms.DecimalField):
    """Aceita "30,50" e "30.50".

    O locale pt_BR não está instalado no WSL, então a conversão é feita aqui:
    com vírgula, o ponto de milhar some e a vírgula vira ponto decimal.
    """

    def to_python(self, value):
        if isinstance(value, str):
            texto = value.strip()
            if "," in texto:
                texto = texto.replace(".", "").replace(",", ".")
            value = texto
        return super().to_python(value)


class MovimentoRapidoForm(forms.ModelForm):
    valor = ValorBrasileiroField(
        label="Valor",
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.TextInput(
            attrs={
                "class": "campo",
                "inputmode": "decimal",
                "autocomplete": "off",
                "placeholder": "0,00",
            }
        ),
    )

    class Meta:
        model = Movimento
        fields = ["valor", "categoria"]
        labels = {"categoria": "Categoria"}
        widgets = {"categoria": forms.Select(attrs={"class": "campo"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(ativa=True)
        self.fields["categoria"].empty_label = "Escolha a categoria"


class PrevistoForm(forms.ModelForm):
    descricao = forms.CharField(
        label="Descrição",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "campo"}),
    )
    vencimento = forms.DateField(
        label="Vencimento",
        widget=forms.DateInput(attrs={"class": "campo", "type": "date"}),
    )
    valor = ValorBrasileiroField(
        label="Valor",
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.TextInput(
            attrs={
                "class": "campo",
                "inputmode": "decimal",
                "autocomplete": "off",
                "placeholder": "0,00",
            }
        ),
    )

    class Meta:
        model = Previsto
        fields = ["descricao", "vencimento", "valor", "categoria"]
        labels = {"categoria": "Categoria"}
        widgets = {"categoria": forms.Select(attrs={"class": "campo"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(
            ativa=True, tipo=TipoValor.DESPESA
        )
        self.fields["categoria"].empty_label = "Escolha a categoria"
