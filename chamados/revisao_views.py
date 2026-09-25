from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import Chamado, RespostaChamado, Movimentacao, Manutencao, Defeito, Equipamento
from .views import perfis_permitidos, _obter_perfil


def gestor(user):
    return user.is_superuser or _obter_perfil(user).tipo in ('admin', 'tecnico')


def formatar(form):
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
    return form


def paginar(request, qs):
    from django.db.models import Exists, OuterRef
    from .notificacoes import permitidas
    if qs.model is Chamado:
        qs = qs.annotate(nova_mensagem=Exists(permitidas(request.user).filter(chamado_id=OuterRef('pk'), lida=False)))
    params = request.GET.copy()
    params.pop('page', None)
    return {'pagina': Paginator(qs, 15).get_page(request.GET.get('page')), 'filtros_url': params.urlencode()}


@login_required
def lista_chamados(request):
    qs = Chamado.objects.select_related('criado_por', 'atribuido_a').order_by('-data_criacao')
    if not gestor(request.user):
        qs = qs.filter(criado_por=request.user)
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '')
    if busca:
        qs = qs.filter(Q(ticket__icontains=busca) | Q(titulo__icontains=busca))
    if status in dict(Chamado.STATUS):
        qs = qs.filter(status=status)
    else:
        status = ''
    return render(request, 'chamados/revisao/chamados.html', {**paginar(request, qs), 'busca': busca, 'status': status, 'status_opcoes': Chamado.STATUS})


class RespostaForm(forms.ModelForm):
    class Meta:
        model = RespostaChamado
        fields = ['mensagem', 'anexo']
        widgets = {'mensagem': forms.Textarea(attrs={'rows': 4})}


class AtendimentoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['status', 'prioridade', 'atribuido_a']
        labels = {'atribuido_a': 'Responsável'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atribuido_a'].queryset = User.objects.filter(is_active=True).filter(Q(is_superuser=True) | Q(perfil__tipo__in=['admin', 'tecnico'])).distinct()


@login_required
def detalhe_chamado(request, pk):
    qs = Chamado.objects.select_related('criado_por', 'atribuido_a')
    pode_gerenciar = gestor(request.user)
    if not pode_gerenciar:
        qs = qs.filter(criado_por=request.user)
    chamado = get_object_or_404(qs, pk=pk)
    resposta = RespostaForm()
    atendimento = AtendimentoForm(instance=chamado) if pode_gerenciar else None
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'atendimento':
            if not pode_gerenciar:
                return HttpResponseForbidden('Apenas a equipe de suporte pode alterar o atendimento.')
            atendimento = AtendimentoForm(request.POST, instance=chamado)
            if atendimento.is_valid():
                atendimento.save()
                messages.success(request, 'Atendimento atualizado.')
                return redirect('detalhe_chamado', pk=pk)
        elif acao == 'resposta':
            resposta = RespostaForm(request.POST, request.FILES)
            if resposta.is_valid():
                obj = resposta.save(commit=False)
                obj.chamado = chamado
                obj.usuario = request.user
                obj.save()
                messages.success(request, 'Resposta registrada.')
                return redirect('detalhe_chamado', pk=pk)
    return render(request, 'chamados/revisao/detalhe_chamado.html', {'chamado': chamado, 'respostas': chamado.respostas.select_related('usuario').order_by('data'), 'form': formatar(resposta), 'atendimento': formatar(atendimento) if atendimento else None})


class ManutencaoForm(forms.ModelForm):
    class Meta:
        model = Manutencao
        fields = ['equipamento', 'empresa', 'tecnico', 'problema', 'solucao', 'custo', 'data_envio', 'data_retorno', 'status', 'laudo', 'observacao']
        widgets = {'data_envio': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}), 'data_retorno': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def clean(self):
        data = super().clean()
        if data.get('custo') is not None and data['custo'] < 0:
            self.add_error('custo', 'O custo não pode ser negativo.')
        if data.get('data_retorno') and data.get('data_envio') and data['data_retorno'] < data['data_envio']:
            self.add_error('data_retorno', 'A data de retorno não pode anteceder o envio.')
        return data


class DefeitoForm(forms.ModelForm):
    class Meta:
        model = Defeito
        fields = ['equipamento', 'descricao', 'prioridade', 'status']


@login_required
@perfis_permitidos('admin', 'tecnico')
def registros(request, tipo):
    modelos = {'movimentacoes': (Movimentacao, 'Movimentações', '-data'), 'manutencoes': (Manutencao, 'Manutenções', '-criado_em'), 'defeitos': (Defeito, 'Defeitos', '-data')}
    model, titulo, ordem = modelos[tipo]
    qs = model.objects.select_related('equipamento').order_by(ordem)
    busca = request.GET.get('busca', '').strip()
    if busca:
        qs = qs.filter(Q(equipamento__patrimonio__icontains=busca) | Q(equipamento__nome__icontains=busca))
    return render(request, 'chamados/revisao/registros.html', {**paginar(request, qs), 'tipo': tipo, 'titulo': titulo, 'busca': busca})


@login_required
@perfis_permitidos('admin', 'tecnico')
def editar_registro(request, tipo, pk=None):
    model, form_class, titulo = {'manutencoes': (Manutencao, ManutencaoForm, 'manutenção'), 'defeitos': (Defeito, DefeitoForm, 'defeito')}[tipo]
    obj = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES if request.method == 'POST' else None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        registro = form.save(commit=False)
        if tipo == 'defeitos' and obj is None:
            registro.usuario = request.user
        registro.save()
        form.save_m2m()
        messages.success(request, 'Registro salvo. O status do equipamento é controlado separadamente.')
        return redirect(tipo)
    return render(request, 'chamados/revisao/form.html', {'form': formatar(form), 'titulo': ('Editar ' if pk else 'Registrar ') + titulo, 'voltar': tipo})


@login_required
@perfis_permitidos('admin', 'tecnico')
def relatorios(request):
    chamados = Chamado.objects.values('status').annotate(total=Count('id')).order_by('status')
    equipamentos = Equipamento.objects.values('status').annotate(total=Count('id')).order_by('status')
    return render(request, 'chamados/revisao/relatorios.html', {'chamados': [(dict(Chamado.STATUS).get(x['status'], x['status']), x['total']) for x in chamados], 'equipamentos': [(dict(Equipamento.STATUS).get(x['status'], x['status']), x['total']) for x in equipamentos]})


@login_required
def arquivo_chamado(request, pk, resposta_pk=None):
    from django.http import FileResponse, Http404
    qs = Chamado.objects.all()
    if not gestor(request.user):
        qs = qs.filter(criado_por=request.user)
    chamado = get_object_or_404(qs, pk=pk)
    campo = get_object_or_404(chamado.respostas, pk=resposta_pk).anexo if resposta_pk else chamado.anexo
    if not campo:
        raise Http404('Anexo não encontrado.')
    try:
        return FileResponse(campo.open('rb'), as_attachment=True, filename=campo.name.rsplit('/', 1)[-1])
    except FileNotFoundError:
        raise Http404('Arquivo não encontrado no armazenamento.')


@login_required
@perfis_permitidos("admin", "tecnico")
def foto_equipamento(request, pk, tipo):
    from django.http import FileResponse, Http404
    equipamento = get_object_or_404(Equipamento, pk=pk)
    campo = equipamento.foto if tipo == 'foto' else equipamento.qr_code
    if not campo:
        raise Http404('Imagem não encontrada.')
    try:
        return FileResponse(campo.open('rb'), as_attachment=campo.name.lower().endswith('.pdf'), filename=campo.name.rsplit('/', 1)[-1])
    except FileNotFoundError:
        raise Http404('Imagem não encontrada no armazenamento.')
