"""Modelo de dado da v1.

Quatro peças, fechadas na fase 0 em 2026-11-01: Conta, Categoria, Movimento e Previsto.

Regras de dinheiro que valem aqui dentro:
- `Decimal` com 2 casas, nunca `float`.
- Valor sempre positivo, e o sinal vem do `tipo` (receita soma, despesa subtrai).
- Saldo é **calculado** a cada leitura, nunca guardado em campo: campo de saldo à mão mente.
- Nada de exclusão física de movimento; o histórico é o produto. O desfazer é lógico
  (`cancelado` + quem/quando) e o registro sai de todos os totais, mas continua no banco.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Sum

VALOR_MINIMO = Decimal("0.01")


class TipoValor(models.TextChoices):
    """Vocabulário único de sinal, compartilhado por Categoria, Movimento e Previsto."""

    RECEITA = "receita", "Receita"
    DESPESA = "despesa", "Despesa"


class Conta(models.Model):
    """Onde o dinheiro está: carteira, conta corrente. O saldo sai da soma dos movimentos."""

    class Tipo(models.TextChoices):
        CARTEIRA = "carteira", "Carteira"
        CORRENTE = "corrente", "Conta corrente"

    nome = models.CharField("nome", max_length=60, unique=True)
    tipo = models.CharField(
        "tipo", max_length=10, choices=Tipo.choices, default=Tipo.CORRENTE
    )
    saldo_inicial = models.DecimalField(
        "saldo inicial", max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    ativa = models.BooleanField("ativa", default=True)
    padrao = models.BooleanField(
        "padrão",
        default=False,
        help_text="Conta usada pelo lançamento rápido. Só uma pode ser padrão.",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "conta"
        verbose_name_plural = "contas"
        constraints = [
            models.UniqueConstraint(
                fields=["padrao"],
                condition=Q(padrao=True),
                name="conta_padrao_unica",
            )
        ]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        """Marcar uma conta como padrão desmarca as outras (só uma é padrão)."""
        if self.padrao:
            outras = Conta.objects.filter(padrao=True)
            if self.pk:
                outras = outras.exclude(pk=self.pk)
            outras.update(padrao=False)
        super().save(*args, **kwargs)

    @property
    def saldo(self) -> Decimal:
        """Saldo inicial, mais receitas, menos despesas. Calculado, nunca guardado.

        Movimento desfeito não conta: o cancelamento é lógico, mas o efeito no saldo não.
        """
        totais = self.movimentos.filter(cancelado=False).aggregate(
            receitas=Sum("valor", filter=Q(tipo=TipoValor.RECEITA)),
            despesas=Sum("valor", filter=Q(tipo=TipoValor.DESPESA)),
        )
        return (
            self.saldo_inicial
            + (totais["receitas"] or Decimal("0.00"))
            - (totais["despesas"] or Decimal("0.00"))
        )


class Categoria(models.Model):
    """Para onde o dinheiro foi. Lista manual e curta (D3), sem regra automática."""

    nome = models.CharField("nome", max_length=60)
    tipo = models.CharField("tipo", max_length=10, choices=TipoValor.choices)
    ativa = models.BooleanField("ativa", default=True)
    entra_no_gasto = models.BooleanField(
        "entra no gasto",
        default=True,
        help_text=(
            "Desligado, a categoria continua no saldo, mas fica fora do "
            "\"gasto do mês\" e do relatório (ex.: Investimento)."
        ),
    )

    class Meta:
        ordering = ["tipo", "nome"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        constraints = [
            models.UniqueConstraint(
                fields=["nome", "tipo"], name="categoria_nome_e_tipo_unicos"
            )
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.get_tipo_display().lower()})"


class Movimento(models.Model):
    """Uma receita ou despesa que já aconteceu. É a base do "gasto atual"."""

    class Origem(models.TextChoices):
        MANUAL = "manual", "Manual"
        PLUGGY = "pluggy", "Pluggy"
        # Mantido porque movimentos já importados na fase 7 podem ter este valor.
        INTER = "inter", "Inter"

    data = models.DateField("data")
    valor = models.DecimalField(
        "valor",
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(VALOR_MINIMO)],
    )
    tipo = models.CharField("tipo", max_length=10, choices=TipoValor.choices)
    conta = models.ForeignKey(
        Conta, on_delete=models.PROTECT, related_name="movimentos", verbose_name="conta"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="movimentos",
        verbose_name="categoria",
    )
    descricao = models.CharField("descrição", max_length=120, blank=True)
    origem = models.CharField(
        "origem", max_length=10, choices=Origem.choices, default=Origem.MANUAL
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimentos",
        verbose_name="criado por",
    )
    id_externo = models.CharField(
        "id externo",
        max_length=100,
        null=True,
        blank=True,
        help_text=(
            "Id da transação na origem (ex.: idTransacao do Inter). "
            "Vazio em lançamento manual."
        ),
    )
    cancelado = models.BooleanField("cancelado", default=False)
    cancelado_em = models.DateTimeField("cancelado em", null=True, blank=True)
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimentos_cancelados",
        verbose_name="cancelado por",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ["-data", "-id"]
        verbose_name = "movimento"
        verbose_name_plural = "movimentos"
        indexes = [
            models.Index(fields=["data"], name="movimento_data_idx"),
            models.Index(fields=["tipo", "data"], name="movimento_tipo_data_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["conta", "id_externo"],
                condition=Q(id_externo__isnull=False),
                name="movimento_id_externo_unico_por_conta",
            ),
            models.CheckConstraint(
                condition=Q(cancelado=False)
                | Q(cancelado_em__isnull=False, cancelado_por__isnull=False),
                name="movimento_cancelado_tem_quem_e_quando",
            ),
        ]

    def __str__(self) -> str:
        rotulo = self.descricao or self.categoria.nome
        return f"{self.data:%d/%m/%Y} · {rotulo} · {self.valor}"

    @property
    def pode_ser_editado(self) -> bool:
        """Editar só lançamento manual e ativo, e nunca o que veio de um previsto pago.

        Editar um pagamento desalinharia `Previsto.valor` do `Movimento.valor`; para
        corrigir esse caso, o caminho é desfazer o pagamento e lançar de novo.
        """
        return (
            self.origem == self.Origem.MANUAL
            and not self.cancelado
            and getattr(self, "previsto", None) is None
        )

    @property
    def pode_ser_desfeito(self) -> bool:
        """Só lançamento manual ativo. Importado do Inter não: o banco é a fonte."""
        return self.origem == self.Origem.MANUAL and not self.cancelado


class GastoFixo(models.Model):
    """Gasto mensal fixo cadastrado uma vez (decisão de 2026-11-08).

    Cada mês gera um `Previsto` a partir deste cadastro. Editar atualiza o mês
    corrente se ele ainda estiver aberto; desativar para de gerar os seguintes.
    O cadastro não é apagado: o histórico dos meses já gerados fica.
    """

    descricao = models.CharField("descrição", max_length=120)
    valor = models.DecimalField(
        "valor",
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(VALOR_MINIMO)],
    )
    dia_vencimento = models.PositiveSmallIntegerField(
        "dia do vencimento",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Dia do mês (1 a 31); em mês mais curto, cai no último dia.",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="gastos_fixos",
        verbose_name="categoria",
    )
    conta = models.ForeignKey(
        Conta,
        on_delete=models.PROTECT,
        related_name="gastos_fixos",
        verbose_name="conta",
    )
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ["descricao"]
        verbose_name = "gasto fixo"
        verbose_name_plural = "gastos fixos"

    def __str__(self) -> str:
        return f"{self.descricao} · todo dia {self.dia_vencimento} · {self.valor}"


class Previsto(models.Model):
    """Conta a pagar com vencimento (D2). É o "comprometido à frente".

    Máquina de estados (G10):
    - aberto → pago: cria exatamente um movimento; desfazer o movimento volta para aberto.
    - aberto → ignorado: sai da lista e do total em aberto sem criar movimento; reabrir
      volta para aberto.
    A restrição do banco garante que "pago" sem movimento não existe.
    """

    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        PAGO = "pago", "Pago"
        IGNORADO = "ignorado", "Ignorado"

    descricao = models.CharField("descrição", max_length=120)
    valor = models.DecimalField(
        "valor",
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(VALOR_MINIMO)],
    )
    vencimento = models.DateField("vencimento")
    tipo = models.CharField(
        "tipo", max_length=10, choices=TipoValor.choices, default=TipoValor.DESPESA
    )
    fixo = models.ForeignKey(
        GastoFixo,
        on_delete=models.PROTECT,
        related_name="previstos",
        verbose_name="gasto fixo",
        null=True,
        blank=True,
        help_text="Preenchido quando o previsto foi gerado de um gasto fixo.",
    )
    competencia = models.DateField(
        "competência",
        null=True,
        blank=True,
        help_text="Primeiro dia do mês gerado; vazio no previsto avulso.",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="previstos",
        verbose_name="categoria",
    )
    conta = models.ForeignKey(
        Conta, on_delete=models.PROTECT, related_name="previstos", verbose_name="conta"
    )
    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.ABERTO
    )
    movimento = models.OneToOneField(
        Movimento,
        on_delete=models.PROTECT,
        related_name="previsto",
        verbose_name="movimento",
        null=True,
        blank=True,
        help_text="Preenchido quando o previsto é marcado como pago.",
    )

    class Meta:
        ordering = ["vencimento", "id"]
        verbose_name = "previsto"
        verbose_name_plural = "previstos"
        indexes = [
            models.Index(
                fields=["status", "vencimento"], name="previsto_status_venc_idx"
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status="pago", movimento__isnull=False) | ~Q(status="pago"),
                name="previsto_pago_tem_movimento",
            ),
            models.UniqueConstraint(
                fields=["fixo", "competencia"],
                condition=Q(fixo__isnull=False),
                name="previsto_fixo_competencia_unica",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.descricao} · vence {self.vencimento:%d/%m/%Y} · {self.valor}"
