from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Perfil, Equipamento, Movimentacao, HistoricoEquipamento
from .views import perfis_permitidos


def estilizar(form):
    for field in form.fields.values():
        if not isinstance(field.widget, forms.HiddenInput):
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
    return form

class DadosForm(forms.ModelForm):
    foto_perfil = forms.ImageField(required=False, label='Foto de perfil', widget=forms.FileInput(attrs={'accept':'image/*'}))
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name':'Nome', 'last_name':'Sobrenome', 'email':'E-mail'}

class ImagemForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = ['imagem_pc']
        labels = {'imagem_pc':'Foto do computador'}
        widgets = {'imagem_pc':forms.FileInput(attrs={'accept':'image/*'})}

@login_required
@perfis_permitidos('admin')
@require_http_methods(['GET','POST'])
def ficha(request, pk):
    pessoa = get_object_or_404(User.objects.select_related('perfil'), pk=pk)
    pode_editar = not pessoa.is_superuser or request.user.is_superuser
    acao = request.POST.get('acao') if request.method == 'POST' else None
    dados = DadosForm(request.POST if acao == 'dados' else None, request.FILES if acao == 'dados' else None, instance=pessoa)
    senha = SetPasswordForm(pessoa, request.POST if acao == 'senha' else None)
    if request.method == 'POST':
        if not pode_editar:
            return HttpResponseForbidden('Conta de superusuário protegida.')
        if acao == 'dados' and dados.is_valid():
            with transaction.atomic():
                pessoa=dados.save(commit=False)
                pessoa.save(update_fields=['first_name','last_name','email'])
                if dados.cleaned_data.get('foto_perfil'):
                    perfil, _ = Perfil.objects.get_or_create(user=pessoa)
                    perfil.foto_perfil = dados.cleaned_data['foto_perfil']
                    perfil.save(update_fields=['foto_perfil'])
            messages.success(request, 'Ficha cadastral atualizada.')
            return redirect('usuario_ficha', pk=pk)
        if acao == 'senha' and senha.is_valid():
            pessoa = senha.save()
            if pessoa.pk == request.user.pk:
                update_session_auth_hash(request, pessoa)
            messages.success(request, 'Senha atualizada. A senha anterior deixou de valer.')
            return redirect('usuario_ficha', pk=pk)
        if acao not in ('dados','senha'):
            return HttpResponseForbidden('Operação inválida.')
    atuais = Equipamento.objects.filter(colaborador=pessoa).order_by('patrimonio')
    historico = Movimentacao.objects.filter(colaborador=pessoa).select_related('equipamento','usuario').order_by('-data','-pk')
    antigos = Equipamento.objects.filter(movimentacoes__colaborador=pessoa).exclude(colaborador=pessoa).distinct().order_by('patrimonio')
    return render(request, 'chamados/acessos/ficha.html', {'pessoa':pessoa, 'pode_editar':pode_editar, 'dados':estilizar(dados), 'senha':estilizar(senha), 'atuais':atuais, 'antigos':antigos, 'historico':Paginator(historico,25).get_page(request.GET.get('page'))})

@login_required
@perfis_permitidos('admin')
def foto_perfil(request, pk):
    perfil = get_object_or_404(Perfil, user_id=pk)
    return imagem_response(perfil.foto_perfil)

def imagem_response(campo):
    if not campo:
        raise Http404('Foto não cadastrada.')
    try:
        response = FileResponse(campo.open('rb'))
    except FileNotFoundError:
        raise Http404('Foto não encontrada.')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response

@login_required
@perfis_permitidos('admin','tecnico')
def foto_pc(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    return imagem_response(equipamento.imagem_pc)

@login_required
@perfis_permitidos('admin','tecnico')
@require_http_methods(['GET','POST'])
def imagem_editar(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    form = ImagemForm(request.POST if request.method=='POST' else None, request.FILES if request.method=='POST' else None, instance=equipamento)
    if request.method=='POST' and form.is_valid():
        if form.has_changed():
            with transaction.atomic():
                equipamento=form.save(commit=False)
                equipamento.save(update_fields=['imagem_pc','atualizado_em'])
                HistoricoEquipamento.objects.create(equipamento=equipamento,usuario=request.user,acao='Foto atualizada')
        messages.success(request,'Foto do computador atualizada.')
        return redirect('detalhe_equipamento',pk=pk)
    return render(request,'chamados/acessos/operacao.html',{'form':estilizar(form),'titulo':'Foto do computador','equipamento':equipamento,'botao':'Salvar foto'})

class DestinoChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.get_full_name() or obj.username} ({obj.username})'

class TransferirForm(forms.Form):
    destino = DestinoChoice(queryset=User.objects.filter(is_active=True).order_by('first_name','username'),label='Novo responsável',empty_label='Selecione o usuário')
    observacao = forms.CharField(required=False,max_length=1000,label='Observação da movimentação',widget=forms.Textarea(attrs={'rows':3}))
    estado = forms.CharField(widget=forms.HiddenInput)

@login_required
@perfis_permitidos('admin','tecnico')
@require_http_methods(['GET','POST'])
def transferir(request, pk):
    equipamento = get_object_or_404(Equipamento.objects.select_related('colaborador'),pk=pk)
    estado = signing.dumps([pk,equipamento.colaborador_id,equipamento.status,equipamento.atualizado_em.isoformat()],salt='transferir-equipamento')
    form = TransferirForm(request.POST if request.method=='POST' else None, initial={'estado':estado,'destino':request.GET.get('destino')})
    if request.method=='POST' and form.is_valid():
        try:
            esperado=signing.loads(form.cleaned_data['estado'],salt='transferir-equipamento',max_age=86400)
        except signing.BadSignature:
            esperado=None
        atual=[pk,equipamento.colaborador_id,equipamento.status,equipamento.atualizado_em.isoformat()]
        destino=form.cleaned_data['destino']
        if esperado != atual:
            form.add_error(None,'O equipamento foi alterado. Reabra esta página e confira o responsável atual.')
        elif equipamento.status not in ('disponivel','em_uso'):
            form.add_error(None,'Somente equipamentos disponíveis ou em uso podem ser transferidos.')
        elif equipamento.colaborador_id == destino.pk:
            form.add_error('destino','Este usuário já é o responsável pelo equipamento.')
        else:
            with transaction.atomic():
                destino=User.objects.select_for_update().get(pk=destino.pk)
                if not destino.is_active:
                    form.add_error('destino','O usuário está desativado.')
                else:
                    agora=timezone.now()
                    alterados=Equipamento.objects.filter(pk=pk,colaborador_id=equipamento.colaborador_id,status=equipamento.status,atualizado_em=equipamento.atualizado_em).update(colaborador=destino,status='em_uso',data_entrega=agora,data_devolucao=None,atualizado_em=agora)
                    if not alterados:
                        form.add_error(None,'Outra movimentação ocorreu. Reabra a página antes de continuar.')
                    else:
                        anterior=equipamento.colaborador
                        nota=f'Transferência de {anterior.username if anterior else "Estoque"} para {destino.username}. '+form.cleaned_data['observacao']
                        if anterior:
                            Movimentacao.objects.create(equipamento=equipamento,usuario=request.user,colaborador=anterior,tipo='devolucao',observacao=nota)
                        Movimentacao.objects.create(equipamento=equipamento,usuario=request.user,colaborador=destino,tipo='saida',observacao=nota)
                        HistoricoEquipamento.objects.create(equipamento=equipamento,usuario=request.user,acao='Transferência de responsável',descricao=nota)
                        messages.success(request,'Equipamento transferido e histórico atualizado nos dois usuários.')
                        return redirect('detalhe_equipamento',pk=pk)
    return render(request,'chamados/acessos/operacao.html',{'form':estilizar(form),'titulo':'Transferir equipamento','equipamento':equipamento,'botao':'Confirmar transferência'})

@login_required
@perfis_permitidos('admin')
def vincular(request, pk):
    pessoa=get_object_or_404(User,pk=pk)
    equipamentos=Equipamento.objects.filter(status__in=['disponivel','em_uso']).exclude(colaborador=pessoa).select_related('colaborador').order_by('patrimonio')
    busca=request.GET.get('busca','').strip()
    if busca:
        from django.db.models import Q
        equipamentos=equipamentos.filter(Q(nome__icontains=busca)|Q(patrimonio__icontains=busca)|Q(numero_serie__icontains=busca))
    return render(request,'chamados/acessos/vincular.html',{'pessoa':pessoa,'equipamentos':Paginator(equipamentos,20).get_page(request.GET.get('page')),'busca':busca})
