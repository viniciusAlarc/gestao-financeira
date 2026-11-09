"""Formulários do app.

O formulário rápido da fase 3 lança com **valor e categoria**. O formulário da
fase 4 cria gastos previstos com descrição, vencimento, valor e categoria.
"""

from decimal import Decimal

from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Categoria, GastoFixo, Movimento, Previsto, TipoValor


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

    def prepare_value(self, value):
        """Mostra Decimal com vírgula (ex.: edição de lançamento); entrada aceita os dois."""
        if isinstance(value, Decimal):
            return f"{value:.2f}".replace(".", ",")
        return super().prepare_value(value)


class MovimentoRapidoForm(forms.ModelForm):
    data = forms.DateField(
        label="Data",
        required=False,
        initial=timezone.localdate,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"class": "campo", "type": "date"}, format="%Y-%m-%d"
        ),
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
        model = Movimento
        fields = ["data", "valor", "categoria"]
        labels = {"categoria": "Categoria"}
        widgets = {"categoria": forms.Select(attrs={"class": "campo"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categorias = Categoria.objects.filter(ativa=True)
        # Na edição, a categoria atual continua disponível mesmo se foi desativada
        # depois do lançamento; sem isso, o form obrigaria a trocar de categoria.
        if self.instance.pk and self.instance.categoria_id:
            categorias = Categoria.objects.filter(
                Q(ativa=True) | Q(pk=self.instance.categoria_id)
            )
        self.fields["categoria"].queryset = categorias
        self.fields["categoria"].empty_label = "Escolha a categoria"


class GastoFixoForm(forms.ModelForm):
    """Cadastro do gasto mensal fixo; o previsto do mês nasce dele (2026-11-08)."""

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
        model = GastoFixo
        fields = ["descricao", "valor", "dia_vencimento", "categoria", "ativo"]
        labels = {
            "descricao": "Descrição",
            "dia_vencimento": "Dia do vencimento",
            "categoria": "Categoria",
            "ativo": "Ativo",
        }
        widgets = {
            "descricao": forms.TextInput(attrs={"class": "campo"}),
            "dia_vencimento": forms.NumberInput(
                attrs={
                    "class": "campo",
                    "inputmode": "numeric",
                    "min": 1,
                    "max": 31,
                }
            ),
            "categoria": forms.Select(attrs={"class": "campo"}),
            "ativo": forms.CheckboxInput(attrs={"class": "caixa"}),
        }
        help_texts = {
            "dia_vencimento": "Em mês mais curto, cai no último dia.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categorias = Categoria.objects.filter(
            ativa=True, tipo=TipoValor.DESPESA
        )
        if self.instance.pk and self.instance.categoria_id:
            categorias = Categoria.objects.filter(
                Q(ativa=True, tipo=TipoValor.DESPESA)
                | Q(pk=self.instance.categoria_id)
            )
        self.fields["categoria"].queryset = categorias
        self.fields["categoria"].empty_label = "Escolha a categoria"


AJUDA_ENTRA_NO_GASTO = (
    "Desmarque para investimento e outros valores que saem do saldo, "
    "mas não são gasto do mês."
)


class CategoriaForm(forms.ModelForm):
    """Cria categoria (decisão de 2026-11-08: o tipo é escolhido aqui e fica fixo)."""

    class Meta:
        model = Categoria
        fields = ["nome", "tipo", "entra_no_gasto", "ativa"]
        labels = {
            "nome": "Nome",
            "tipo": "Tipo",
            "entra_no_gasto": "Entra no gasto do mês",
            "ativa": "Ativa",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "campo"}),
            "tipo": forms.Select(attrs={"class": "campo"}),
            "entra_no_gasto": forms.CheckboxInput(attrs={"class": "caixa"}),
            "ativa": forms.CheckboxInput(attrs={"class": "caixa"}),
        }
        help_texts = {"entra_no_gasto": AJUDA_ENTRA_NO_GASTO}


class CategoriaEdicaoForm(forms.ModelForm):
    """Edita nome, ativa e 'entra no gasto'; o tipo não muda depois de criada."""

    class Meta:
        model = Categoria
        fields = ["nome", "entra_no_gasto", "ativa"]
        labels = {
            "nome": "Nome",
            "entra_no_gasto": "Entra no gasto do mês",
            "ativa": "Ativa",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "campo"}),
            "entra_no_gasto": forms.CheckboxInput(attrs={"class": "caixa"}),
            "ativa": forms.CheckboxInput(attrs={"class": "caixa"}),
        }
        help_texts = {"entra_no_gasto": AJUDA_ENTRA_NO_GASTO}

    def clean_nome(self):
        """O tipo fica fora do form; a checagem de duplicidade tem que ser manual.

        Sem isso, renomear para um nome que já existe no mesmo tipo chegaria ao
        banco e estouraria a restrição única em vez de virar erro de campo.
        """
        nome = self.cleaned_data["nome"]
        iguais = Categoria.objects.filter(
            nome=nome, tipo=self.instance.tipo
        ).exclude(pk=self.instance.pk)
        if iguais.exists():
            raise forms.ValidationError(
                "Já existe uma categoria com esse nome e tipo."
            )
        return nome


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
