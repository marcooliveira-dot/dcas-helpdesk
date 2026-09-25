from django.urls import path

from .views import (
    dashboard_redirect,
    painel_colaborador,
    painel_tecnico,
    painel_admin,

    # Chamados
    novo_chamado_unico,
    chamado_sucesso,
    finalizar_chamado,

    # Equipamentos
    equipamentos,
    controle_equipamentos,
    novo_equipamento,
    detalhe_equipamento,
    retirar_equipamento,
    devolver_equipamento,

    # Logout
    sair,
)

urlpatterns = [

    # ==========================
    # Dashboard
    # ==========================

    path(
        "",
        dashboard_redirect,
        name="dashboard"
    ),

    # ==========================
    # Painéis
    # ==========================

    path(
        "painel-colaborador/",
        painel_colaborador,
        name="painel_colaborador"
    ),

    path(
        "painel-tecnico/",
        painel_tecnico,
        name="painel_tecnico"
    ),

    path(
        "painel-admin/",
        painel_admin,
        name="painel_admin"
    ),

    # ==========================
    # Chamados
    # ==========================

    path(
        "chamado/novo/",
        novo_chamado_unico,
        name="novo_chamado"
    ),

    path(
        "chamado/sucesso/",
        chamado_sucesso,
        name="chamado_sucesso"
    ),

    path(
        "chamado/finalizar/<int:id>/",
        finalizar_chamado,
        name="finalizar_chamado"
    ),

    # ==========================
    # Equipamentos
    # ==========================

    path(
        "equipamentos/",
        equipamentos,
        name="equipamentos"
    ),

    path(
        "equipamentos/dashboard/",
        controle_equipamentos,
        name="controle_equipamentos"
    ),

    path(
        "equipamentos/novo/",
        novo_equipamento,
        name="novo_equipamento"
    ),

    path(
        "equipamentos/<int:pk>/",
        detalhe_equipamento,
        name="detalhe_equipamento"
    ),

    path(
        "equipamentos/retirar/<int:id>/",
        retirar_equipamento,
        name="retirar_equipamento"
    ),

    path(
        "equipamentos/devolver/<int:id>/",
        devolver_equipamento,
        name="devolver_equipamento"
    ),

    # ==========================
    # Logout
    # ==========================

    path(
        "sair/",
        sair,
        name="sair"
    ),

]

from . import revisao_views

urlpatterns += [
    path('chamados/', revisao_views.lista_chamados, name='lista_chamados'),
    path('chamado/<int:pk>/', revisao_views.detalhe_chamado, name='detalhe_chamado'),
    path('movimentacoes/', revisao_views.registros, {'tipo': 'movimentacoes'}, name='movimentacoes'),
    path('manutencoes/', revisao_views.registros, {'tipo': 'manutencoes'}, name='manutencoes'),
    path('manutencoes/nova/', revisao_views.editar_registro, {'tipo': 'manutencoes'}, name='nova_manutencao'),
    path('manutencoes/<int:pk>/', revisao_views.editar_registro, {'tipo': 'manutencoes'}, name='editar_manutencao'),
    path('defeitos/', revisao_views.registros, {'tipo': 'defeitos'}, name='defeitos'),
    path('defeitos/novo/', revisao_views.editar_registro, {'tipo': 'defeitos'}, name='novo_defeito'),
    path('defeitos/<int:pk>/', revisao_views.editar_registro, {'tipo': 'defeitos'}, name='editar_defeito'),
    path('relatorios/', revisao_views.relatorios, name='relatorios'),
]

urlpatterns += [
    path('chamado/<int:pk>/anexo/', revisao_views.arquivo_chamado, name='arquivo_chamado'),
    path('chamado/<int:pk>/respostas/<int:resposta_pk>/anexo/', revisao_views.arquivo_chamado, name='arquivo_resposta'),
    path('equipamentos/<int:pk>/foto/', revisao_views.foto_equipamento, {'tipo': 'foto'}, name='foto_equipamento'),
    path('equipamentos/<int:pk>/qrcode/', revisao_views.foto_equipamento, {'tipo': 'qr_code'}, name='qrcode_equipamento'),
]

from . import acessos
urlpatterns += [path('usuarios/', acessos.usuarios, name='usuarios'), path('usuarios/novo/', acessos.usuario_editar, name='usuario_novo'), path('usuarios/<int:pk>/', acessos.usuario_editar, name='usuario_editar')]

from . import notificacoes
urlpatterns += [path('notificacoes/', notificacoes.lista, name='notificacoes'), path('notificacoes/contador/', notificacoes.contador, name='notificacoes_contador'), path('notificacoes/ler/', notificacoes.ler, name='notificacoes_ler')]

from . import termos
urlpatterns += [path('equipamentos/<int:pk>/termo/', termos.termo_equipamento, name='termo_equipamento')]

from .equipamento_edicao import editar_equipamento
urlpatterns += [path('equipamentos/<int:pk>/editar/', editar_equipamento, name='editar_equipamento')]

from . import fichas
urlpatterns += [
 path('usuarios/<int:pk>/ficha/',fichas.ficha,name='usuario_ficha'),
 path('usuarios/<int:pk>/foto/',fichas.foto_perfil,name='usuario_foto'),
 path('usuarios/<int:pk>/vincular/',fichas.vincular,name='usuario_vincular'),
 path('equipamentos/<int:pk>/imagem/',fichas.foto_pc,name='imagem_pc'),
 path('equipamentos/<int:pk>/imagem/editar/',fichas.imagem_editar,name='imagem_pc_editar'),
 path('equipamentos/<int:pk>/transferir/',fichas.transferir,name='transferir_equipamento'),
]
