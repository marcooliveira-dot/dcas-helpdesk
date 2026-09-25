import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import render
from django.core.mail import send_mail
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Chamado, RespostaChamado, Notificacao

logger = logging.getLogger(__name__)
def permitidas(user):
    qs = Notificacao.objects.filter(usuario=user)
    if not (user.is_superuser or getattr(getattr(user, 'perfil', None), 'tipo', '') in ['admin','tecnico']):
        qs = qs.filter(chamado__criado_por=user)
    return qs

def enviar_email(aviso_id):
    if not getattr(settings, 'HELPDESK_EMAIL_ENABLED', False):
        return
    aviso = Notificacao.objects.select_related('usuario','chamado').get(pk=aviso_id)
    if not aviso.usuario.is_active or not aviso.usuario.email or not permitidas(aviso.usuario).filter(pk=aviso.pk).exists():
        return
    url = 'https://dcasgroup2810.pythonanywhere.com' + reverse('detalhe_chamado', args=[aviso.chamado_id])
    try:
        enviado = send_mail('DCAS HelpDesk — ' + aviso.texto, 'Há uma atualização no seu atendimento. Entre no HelpDesk para visualizar:\n' + url, settings.DEFAULT_FROM_EMAIL, [aviso.usuario.email], fail_silently=False)
        if enviado:
            Notificacao.objects.filter(pk=aviso.pk).update(email_enviado=True)
    except Exception:
        logger.warning('Falha no envio do aviso %s. A notificação permanece disponível no site.', aviso.pk)

def avisar(chamado, autor_id, texto):
    equipe = Q(is_superuser=True) | Q(perfil__tipo__in=['admin','tecnico'])
    destinatarios = User.objects.filter(is_active=True).filter(equipe | Q(pk=chamado.criado_por_id)).exclude(pk=autor_id).distinct()
    for usuario in destinatarios:
        aviso = Notificacao.objects.create(usuario=usuario, chamado=chamado, texto=texto)
        transaction.on_commit(lambda pk=aviso.pk: enviar_email(pk))

@receiver(post_save, sender=Chamado, dispatch_uid='helpdesk_novo_chamado_aviso')
def novo(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        avisar(instance, instance.criado_por_id, 'Novo chamado')

@receiver(post_save, sender=RespostaChamado, dispatch_uid='helpdesk_resposta_aviso')
def resposta(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        avisar(instance.chamado, instance.usuario_id, 'Nova mensagem no chamado')

def contexto(request):
    if not request.user.is_authenticated:
        return {}
    qs = permitidas(request.user)
    result = {'avisos_nao_lidos':qs.filter(lida=False).count()}
    match = request.resolver_match
    if match and match.url_name == 'detalhe_chamado':
        result['avisos_chamado_id'] = match.kwargs['pk']
        result['avisos_limite'] = qs.filter(chamado_id=match.kwargs['pk']).order_by('-pk').values_list('pk',flat=True).first() or 0
    return result

@login_required
def lista(request):
    from django.core.paginator import Paginator
    pagina = Paginator(permitidas(request.user).select_related('chamado').order_by('-criada_em'), 20).get_page(request.GET.get('page'))
    return render(request, 'chamados/notificacoes.html', {'pagina':pagina})

@login_required
def contador(request):
    return JsonResponse({'total':permitidas(request.user).filter(lida=False).count()})

@login_required
@require_POST
def ler(request):
    try:
        chamado = int(request.POST.get('chamado', ''))
        limite = int(request.POST.get('limite', ''))
    except (TypeError, ValueError):
        return JsonResponse({'erro':'Dados inválidos'}, status=400)
    permitidas(request.user).filter(chamado_id=chamado,pk__lte=limite,lida=False).update(lida=True)
    return JsonResponse({'total':permitidas(request.user).filter(lida=False).count()})
