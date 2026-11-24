"""Admin do Django como tela provisória da fase 1.

A tela de verdade vem nas fases 2 e 3. Até lá, é aqui que o modelo é testado com dado real.
"""

from django.contrib import admin

from .models import (
    Categoria,
    ConclusaoTarefa,
    Conta,
    GastoFixo,
    Movimento,
    Previsto,
    Tarefa,
)


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "tipo",
        "saldo_inicial",
        "ativa",
        "padrao",
        "saldo_calculado",
    )
    list_filter = ("tipo", "ativa", "padrao")

    @admin.display(description="saldo calculado")
    def saldo_calculado(self, obj: Conta):
        return obj.saldo


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "ativa", "entra_no_gasto")
    list_filter = ("tipo", "ativa", "entra_no_gasto")
    search_fields = ("nome",)


@admin.register(Movimento)
class MovimentoAdmin(admin.ModelAdmin):
    list_display = (
        "data",
        "tipo",
        "descricao",
        "categoria",
        "conta",
        "valor",
        "origem",
        "cancelado",
    )
    list_filter = ("tipo", "origem", "cancelado", "conta", "categoria")
    date_hierarchy = "data"
    exclude = (
        "criado_por",
        "id_externo",
        "cancelado",
        "cancelado_em",
        "cancelado_por",
    )

    def save_model(self, request, obj, form, change):
        # Quem lançou sai da sessão, nunca de um campo digitado (D5).
        if not obj.criado_por_id:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(GastoFixo)
class GastoFixoAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "dia_vencimento",
        "valor",
        "categoria",
        "conta",
        "ativo",
    )
    list_filter = ("ativo", "categoria", "conta")
    search_fields = ("descricao",)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "dono", "criada_em")
    list_filter = ("dono",)
    search_fields = ("titulo",)


@admin.register(ConclusaoTarefa)
class ConclusaoTarefaAdmin(admin.ModelAdmin):
    list_display = ("tarefa", "data", "concluida_em")
    list_filter = ("data", "tarefa__dono")
    date_hierarchy = "data"


@admin.register(Previsto)
class PrevistoAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "vencimento",
        "valor",
        "tipo",
        "status",
        "fixo",
        "categoria",
        "conta",
    )
    list_filter = ("status", "tipo", "fixo", "conta", "categoria")
    date_hierarchy = "vencimento"
