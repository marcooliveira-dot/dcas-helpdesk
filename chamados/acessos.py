from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.deprecation import MiddlewareMixin
from .models import Perfil
from .views import perfis_permitidos
from .revisao_views import formatar, paginar

ROLES = [('colaborador', 'Solicitante'), ('tecnico', 'Técnico'), ('admin', 'Administrador')]

class AdminRoleMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.resolver_match and 'admin' in request.resolver_match.namespaces and request.user.is_authenticated:
            if not request.user.is_superuser and not Perfil.objects.filter(user=request.user, tipo='admin').exists():
                return HttpResponseForbidden('A administração é restrita aos administradores.')

class UsuarioForm(forms.ModelForm):
    perfil = forms.ChoiceField(choices=ROLES, initial='colaborador', label='Perfil de acesso')
    senha = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label='Senha', help_text='Obrigatória para novo usuário. Ao editar, deixe em branco para manter a senha.')
    confirmar_senha = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label='Confirmar senha')
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {'username': 'Login', 'first_name': 'Nome', 'last_name': 'Sobrenome', 'email': 'E-mail', 'is_active': 'Acesso ativo'}
    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        if self.instance.pk:
            self.fields['perfil'].initial = Perfil.objects.filter(user=self.instance).values_list('tipo', flat=True).first() or 'colaborador'
    def clean(self):
        data = super().clean()
        senha = data.get('senha')
        if not self.instance.pk and not senha:
            self.add_error('senha', 'Informe uma senha para o novo usuário.')
        if senha != data.get('confirmar_senha'):
            self.add_error('confirmar_senha', 'As senhas não conferem.')
        if senha:
            candidato = User(username=data.get('username', ''), first_name=data.get('first_name', ''), last_name=data.get('last_name', ''), email=data.get('email', ''))
            try:
                validate_password(senha, candidato)
            except forms.ValidationError as error:
                self.add_error('senha', error)
        if self.instance.pk == self.actor.pk and (not data.get('is_active') or data.get('perfil') != 'admin'):
            raise forms.ValidationError('Você não pode desativar ou remover seu próprio acesso administrativo.')
        return data

@login_required
@perfis_permitidos('admin')
def usuarios(request):
    qs = User.objects.select_related('perfil').order_by('username')
    busca = request.GET.get('busca', '').strip()
    if busca:
        qs = qs.filter(Q(username__icontains=busca) | Q(first_name__icontains=busca) | Q(last_name__icontains=busca) | Q(email__icontains=busca))
    return render(request, 'chamados/acessos/usuarios.html', {**paginar(request, qs), 'busca': busca})

@login_required
@perfis_permitidos('admin')
def usuario_editar(request, pk=None):
    obj = get_object_or_404(User, pk=pk) if pk else None
    if obj and obj.is_superuser:
        return HttpResponseForbidden('Contas de superusuário são protegidas. Use a administração Django com uma conta de superusuário.')
    form = UsuarioForm(request.POST if request.method == 'POST' else None, instance=obj, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            usuario = form.save(commit=False)
            if form.cleaned_data['senha']:
                usuario.set_password(form.cleaned_data['senha'])
            # O painel de usuários não concede permissões de superusuário ou de staff.
            usuario.is_staff = False
            usuario.save()
            usuario.groups.clear()
            usuario.user_permissions.clear()
            Perfil.objects.update_or_create(user=usuario, defaults={'tipo': form.cleaned_data['perfil']})
        messages.success(request, 'Usuário e perfil de acesso salvos.')
        return redirect('usuarios')
    form = formatar(form)
    form.fields['is_active'].widget.attrs['class'] = 'form-check-input'
    return render(request, 'chamados/acessos/form.html', {'form': form, 'titulo': 'Editar usuário' if pk else 'Novo usuário'})
