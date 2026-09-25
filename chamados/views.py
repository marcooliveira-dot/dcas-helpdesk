from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from .forms import ChamadoForm, EquipamentoForm
from .models import (
    Categoria,
    Chamado,
    Defeito,
    Equipamento,
    Manutencao,
    Movimentacao,
    Perfil,
)


# ==========================================================
# AUTORIZAÇÃO E PERFIS
# ==========================================================

def _obter_perfil(user):
    """Obtém o perfil e cria um perfil de colaborador quando necessário."""
    perfil, _ = Perfil.objects.get_or_create(
        user=user,
        defaults={"tipo": "colaborador"},
    )
    return perfil


def perfis_permitidos(*tipos):
    """Restringe uma view aos perfis informados; superusuários têm acesso."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            perfil = _obter_perfil(request.user)

            if perfil.tipo in tipos:
                return view_func(request, *args, **kwargs)

            messages.error(request, "Você não tem permissão para acessar essa área.")
            return redirect("dashboard")

        return wrapper

    return decorator


# ==========================================================
# REDIRECIONAMENTO PRINCIPAL
# ==========================================================
@login_required
def dashboard_redirect(request):
    if request.user.is_superuser:
        return redirect("painel_admin")

    perfil, _ = Perfil.objects.get_or_create(
        user=request.user,
        defaults={"tipo": "colaborador"},
    )

    destinos = {
        "admin": "painel_admin",
        "tecnico": "painel_tecnico",
        "colaborador": "painel_colaborador",
    }

    return redirect(
        destinos.get(perfil.tipo, "painel_colaborador")
    )
@login_required
@perfis_permitidos("admin")
def painel_admin(request):
    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "").strip()
    prioridade = request.GET.get("prioridade", "").strip()
    categoria = request.GET.get("categoria", "").strip()

    chamados = Chamado.objects.select_related(
        "criado_por",
        "atribuido_a",
    ).order_by("-data_criacao")

    if busca:
        chamados = chamados.filter(
            Q(ticket__icontains=busca)
            | Q(titulo__icontains=busca)
            | Q(criado_por__username__icontains=busca)
            | Q(criado_por__first_name__icontains=busca)
            | Q(criado_por__last_name__icontains=busca)
        )

    if status in dict(Chamado.STATUS):
        chamados = chamados.filter(status=status)
    else:
        status = ""

    if prioridade in dict(Chamado.PRIORIDADE):
        chamados = chamados.filter(prioridade=prioridade)
    else:
        prioridade = ""

    if categoria in dict(Chamado.CATEGORIAS):
        chamados = chamados.filter(categoria=categoria)
    else:
        categoria = ""

    # Import local para não alterar os imports existentes.
    from django.core.paginator import Paginator

    pagina = Paginator(chamados, 15).get_page(
        request.GET.get("page")
    )

    parametros = request.GET.copy()
    parametros.pop("page", None)

    pendentes = Chamado.objects.exclude(
        status__in=["resolvido", "fechado"]
    )

    contexto = {
        "total_chamados": Chamado.objects.count(),
        "abertos": Chamado.objects.filter(status="aberto").count(),
        "andamento": Chamado.objects.filter(
            status="em_andamento"
        ).count(),
        "aguardando": Chamado.objects.filter(
            status="aguardando"
        ).count(),
        "resolvidos": Chamado.objects.filter(
            status="resolvido"
        ).count(),
        "fechados": Chamado.objects.filter(status="fechado").count(),
        "urgentes": pendentes.filter(prioridade="urgente").count(),
        "sem_responsavel": pendentes.filter(
            atribuido_a__isnull=True
        ).count(),

        "pagina": pagina,
        "busca": busca,
        "status": status,
        "prioridade": prioridade,
        "categoria": categoria,
        "status_opcoes": Chamado.STATUS,
        "prioridade_opcoes": Chamado.PRIORIDADE,
        "categoria_opcoes": Chamado.CATEGORIAS,
        "filtros_url": parametros.urlencode(),

        "total_equipamentos": Equipamento.objects.count(),
        "disponiveis": Equipamento.objects.filter(
            status="disponivel"
        ).count(),
        "em_uso": Equipamento.objects.filter(status="em_uso").count(),
        "em_manutencao": Equipamento.objects.filter(
            status="manutencao"
        ).count(),
        "com_defeito": Equipamento.objects.filter(
            status="defeito"
        ).count(),
        "reservados": Equipamento.objects.filter(
            status="reservado"
        ).count(),
        "baixados": Equipamento.objects.filter(status="baixado").count(),

        "manutencoes_abertas": Manutencao.objects.filter(
            status__in=["aberta", "andamento", "aguardando"]
        ).count(),
        "defeitos_abertos": Defeito.objects.filter(
            status__in=["aberto", "analise"]
        ).count(),

        "movimentacoes": (
            Movimentacao.objects
            .select_related("equipamento", "usuario", "colaborador")
            .order_by("-data")[:8]
        ),
    }

    return render(
        request,
        "chamados/dashboard/dashboard_admin.html",
        contexto,
    )
# ==========================================================
# PAINÉIS
# ==========================================================

@login_required
@perfis_permitidos("tecnico", "admin")
def painel_tecnico(request):
    chamados = (
        Chamado.objects
        .select_related("criado_por", "atribuido_a")
        .order_by("-data_criacao")
    )

    contexto = {
        "chamados": chamados,
        "abertos": chamados.filter(status="aberto").count(),
        "andamento": chamados.filter(status="em_andamento").count(),
        "aguardando": chamados.filter(status="aguardando").count(),
    }

    return render(
        request,
        "chamados/dashboard/dashboard_tecnico.html",
        contexto,
    )


@login_required
def painel_colaborador(request):
    from .revisao_views import paginar
    from django.db.models import Count
    chamados = Chamado.objects.filter(criado_por=request.user).select_related('atribuido_a').order_by('-data_criacao')
    totais = dict(chamados.order_by().values_list('status').annotate(total=Count('pk')))
    status = request.GET.get('status', '')
    if status not in dict(Chamado.STATUS):
        status = ''
    busca = request.GET.get('busca', '').strip()
    grupos = [('', 'Todos', 'primary', sum(totais.values()))]
    for valor, rotulo, cor in [('aberto','Em aberto','danger'),('em_andamento','Em andamento','warning'),('aguardando','Aguardando sua resposta','info'),('resolvido','Resolvidos','success'),('fechado','Fechados','secondary')]:
        grupos.append((valor, rotulo, cor, totais.get(valor,0)))
    if status:
        chamados = chamados.filter(status=status)
    if busca:
        chamados = chamados.filter(Q(ticket__icontains=busca) | Q(titulo__icontains=busca))
    return render(request, 'chamados/dashboard/dashboard_colaborador.html', {**paginar(request,chamados), 'grupos':grupos, 'status':status, 'busca':busca, 'status_opcoes':Chamado.STATUS})


# ==========================================================
# EQUIPAMENTOS
# ==========================================================

@login_required
@perfis_permitidos("admin", "tecnico")
def equipamentos(request):
    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "").strip()
    categoria = request.GET.get("categoria", "").strip()

    queryset = (
        Equipamento.objects
        .select_related(
            "categoria",
            "fabricante",
            "fornecedor",
            "departamento",
            "localizacao",
            "colaborador",
        )
        .order_by("patrimonio")
    )

    if busca:
        queryset = queryset.filter(
            Q(nome__icontains=busca)
            | Q(patrimonio__icontains=busca)
            | Q(numero_serie__icontains=busca)
            | Q(marca__icontains=busca)
            | Q(modelo__icontains=busca)
        )

    if status:
        queryset = queryset.filter(status=status)

    if categoria.isdigit():
        queryset = queryset.filter(categoria_id=int(categoria))

    return render(
        request,
        "chamados/equipamentos/lista.html",
        {
            "equipamentos": queryset,
            "categorias": Categoria.objects.order_by("nome"),
            "status_opcoes": Equipamento.STATUS,
            "busca": busca,
            "status": status,
            "categoria": categoria,
        },
    )


@login_required
@perfis_permitidos("tecnico", "admin")
def controle_equipamentos(request):
    return equipamentos(request)


@login_required
@perfis_permitidos("tecnico", "admin")
def novo_equipamento(request):
    if request.method == "POST":
        form = EquipamentoForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                equipamento = form.save()

                Movimentacao.objects.create(
                    equipamento=equipamento,
                    usuario=request.user,
                    tipo="entrada",
                    observacao="Equipamento cadastrado no patrimônio.",
                )

            messages.success(request, "Equipamento cadastrado com sucesso.")
            return redirect("detalhe_equipamento", pk=equipamento.pk)
    else:
        form = EquipamentoForm()

    return render(
        request,
        "chamados/equipamentos/novo.html",
        {"form": form},
    )


@login_required
@perfis_permitidos("admin", "tecnico")
def detalhe_equipamento(request, pk):
    equipamento = get_object_or_404(
        Equipamento.objects.select_related(
            "categoria",
            "fabricante",
            "fornecedor",
            "departamento",
            "localizacao",
            "colaborador",
        ),
        pk=pk,
    )

    contexto = {
        "equipamento": equipamento,
        "movimentacoes": equipamento.movimentacoes.select_related(
            "usuario",
            "colaborador",
        ).order_by("-data"),
        "manutencoes": equipamento.manutencoes.order_by("-criado_em"),
        "defeitos": equipamento.defeitos.order_by("-data"),
        "historico": equipamento.historico.order_by("-data"),
    }

    return render(
        request,
        "chamados/equipamentos/detalhes.html",
        contexto,
    )


@login_required
@perfis_permitidos("admin", "tecnico")
@require_POST
def retirar_equipamento(request, id):
    with transaction.atomic():
        equipamento = get_object_or_404(
            Equipamento.objects.select_for_update(),
            id=id,
        )

        if equipamento.status != "disponivel" or equipamento.colaborador_id:
            messages.warning(request, "Este equipamento não está disponível.")
            return redirect("detalhe_equipamento", pk=equipamento.pk)

        equipamento.status = "em_uso"
        equipamento.colaborador = request.user
        equipamento.data_entrega = timezone.now()
        equipamento.data_devolucao = None
        equipamento.save(
            update_fields=[
                "status",
                "colaborador",
                "data_entrega",
                "data_devolucao",
                "atualizado_em",
            ]
        )

        Movimentacao.objects.create(
            equipamento=equipamento,
            usuario=request.user,
            colaborador=request.user,
            tipo="saida",
            observacao="Equipamento entregue ao colaborador.",
        )

    messages.success(request, "Equipamento entregue com sucesso.")
    return redirect("detalhe_equipamento", pk=equipamento.pk)


@login_required
@perfis_permitidos("admin", "tecnico")
@require_POST
def devolver_equipamento(request, id):
    with transaction.atomic():
        equipamento = get_object_or_404(
            Equipamento.objects.select_for_update(),
            id=id,
        )

        gestor = request.user.is_superuser or _obter_perfil(request.user).tipo in {'admin', 'tecnico'}
        if not gestor and equipamento.colaborador_id != request.user.pk:
            return HttpResponseForbidden('Você só pode devolver equipamentos atribuídos a você.')
        if equipamento.status != 'em_uso' or not equipamento.colaborador_id:
            messages.warning(request, 'A devolução exige um equipamento em uso e com colaborador.')
            return redirect('detalhe_equipamento', pk=equipamento.pk)
        colaborador_anterior = equipamento.colaborador

        if equipamento.status == "disponivel" and not colaborador_anterior:
            messages.warning(request, "Este equipamento já está disponível.")
            return redirect("detalhe_equipamento", pk=equipamento.pk)

        equipamento.status = "disponivel"
        equipamento.colaborador = None
        equipamento.data_devolucao = timezone.now()
        equipamento.save(
            update_fields=[
                "status",
                "colaborador",
                "data_devolucao",
                "atualizado_em",
            ]
        )

        Movimentacao.objects.create(
            equipamento=equipamento,
            usuario=request.user,
            colaborador=colaborador_anterior,
            tipo="devolucao",
            observacao="Equipamento devolvido ao patrimônio.",
        )

    messages.success(request, "Equipamento devolvido com sucesso.")
    return redirect("detalhe_equipamento", pk=equipamento.pk)


# ==========================================================
# CHAMADOS
# ==========================================================

@login_required
def novo_chamado_unico(request):
    if request.method == "POST":
        form = ChamadoForm(request.POST, request.FILES)

        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.criado_por = request.user
            chamado.save()
            form.save_m2m()

            messages.success(request, "Chamado aberto com sucesso.")
            return redirect("chamado_sucesso")
    else:
        form = ChamadoForm()

    return render(
        request,
        "chamados/chamado/novo.html",
        {"form": form},
    )


@login_required
def chamado_sucesso(request):
    return render(request, "chamados/chamado/sucesso.html")


@login_required
@perfis_permitidos("tecnico", "admin")
@require_POST
def finalizar_chamado(request, id):
    chamado = get_object_or_404(Chamado, id=id)

    if chamado.status in {"resolvido", "fechado"}:
        messages.info(request, "Este chamado já foi finalizado.")
        return redirect("dashboard")

    chamado.status = "resolvido"
    chamado.save(update_fields=["status", "data_atualizacao"])

    messages.success(request, "Chamado finalizado com sucesso.")
    return redirect("dashboard")


# ==========================================================
# LOGOUT
# ==========================================================

@login_required
@require_POST
def sair(request):
    logout(request)
    messages.success(request, "Sessão encerrada com sucesso.")
    return redirect("login")
