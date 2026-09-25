from django.contrib import admin

from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import display

from .models import (
    Categoria,
    Chamado,
    Defeito,
    Departamento,
    Equipamento,
    Fabricante,
    Fornecedor,
    HistoricoEquipamento,
    Localizacao,
    Manutencao,
    Movimentacao,
    Perfil,
    RespostaChamado,
    TermoResponsabilidade,
)


class SomenteLeituraInlineMixin:
    can_delete = False
    extra = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class MovimentacaoInline(SomenteLeituraInlineMixin, TabularInline):
    model = Movimentacao
    readonly_fields = (
        "tipo",
        "usuario",
        "colaborador",
        "data",
        "observacao",
    )
    ordering = ("-data",)
    tab = True
    show_count = True


class HistoricoEquipamentoInline(SomenteLeituraInlineMixin, TabularInline):
    model = HistoricoEquipamento
    readonly_fields = (
        "acao",
        "usuario",
        "data",
        "descricao",
    )
    ordering = ("-data",)
    tab = True
    show_count = True


class ManutencaoInline(TabularInline):
    model = Manutencao
    extra = 0
    show_change_link = True
    tab = True
    show_count = True


class DefeitoInline(TabularInline):
    model = Defeito
    extra = 0
    show_change_link = True
    tab = True
    show_count = True


class RespostaChamadoInline(StackedInline):
    model = RespostaChamado
    extra = 1
    show_change_link = True
    tab = True
    show_count = True
    collapsible = True


@admin.register(Perfil)
class PerfilAdmin(ModelAdmin):
    list_display = ("user", "tipo")
    list_filter = ("tipo",)
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    list_select_related = ("user",)
    ordering = ("user__username",)
    list_per_page = 30


@admin.register(Chamado)
class ChamadoAdmin(ModelAdmin):
    list_display = (
        "ticket",
        "titulo",
        "exibir_status",
        "exibir_prioridade",
        "criado_por",
        "atribuido_a",
        "data_criacao",
    )
    list_filter = (
        "status",
        "prioridade",
        "data_criacao",
    )
    search_fields = (
        "ticket",
        "titulo",
        "descricao",
        "criado_por__username",
        "atribuido_a__username",
    )
    list_select_related = (
        "criado_por",
        "atribuido_a",
    )
    ordering = ("-data_criacao",)
    date_hierarchy = "data_criacao"
    list_per_page = 30
    save_on_top = True
    warn_unsaved_form = True
    inlines = (RespostaChamadoInline,)

    @display(description="Status", ordering="status", label=True)
    def exibir_status(self, obj):
        return obj.get_status_display()

    @display(description="Prioridade", ordering="prioridade", label=True)
    def exibir_prioridade(self, obj):
        return obj.get_prioridade_display()


@admin.register(Equipamento)
class EquipamentoAdmin(ModelAdmin):
    list_display = (
        "patrimonio",
        "nome",
        "tipo",
        "marca",
        "modelo",
        "status",
        "colaborador",
        "departamento",
        "localizacao",
    )
    list_filter = (
        "status",
        "tipo",
        "categoria",
        "departamento",
        "localizacao",
        "fabricante",
    )
    search_fields = (
        "patrimonio",
        "numero_serie",
        "nome",
        "marca",
        "modelo",
        "colaborador__username",
    )
    list_select_related = (
        "categoria",
        "fabricante",
        "colaborador",
        "departamento",
        "localizacao",
    )
    readonly_fields = ("criado_em", "atualizado_em")
    ordering = ("patrimonio",)
    list_per_page = 30
    save_on_top = True
    warn_unsaved_form = True
    inlines = (
        MovimentacaoInline,
        ManutencaoInline,
        DefeitoInline,
        HistoricoEquipamentoInline,
    )


@admin.register(
    Categoria,
    Fabricante,
    Fornecedor,
    Departamento,
    Localizacao,
    RespostaChamado,
    Movimentacao,
    Manutencao,
    Defeito,
    TermoResponsabilidade,
    HistoricoEquipamento,
)
class RegistroSimplesAdmin(ModelAdmin):
    list_per_page = 30
