from datetime import timedelta

from django.conf import settings
from django.db.models import Case, Count, DateTimeField, F, Q, Value, When
from django.utils import timezone


ENCERRADOS = ("resolvido", "fechado")
VISOES = (
    ("", "Todos ativos", "bi-inboxes"),
    ("meus", "Comigo", "bi-person-check"),
    ("sem_responsavel", "Sem responsável", "bi-person-dash"),
    ("urgentes", "Urgentes", "bi-exclamation-circle"),
    ("atrasados", "Prazo vencido", "bi-clock-history"),
)


def com_prazo(chamados):
    metas = {"urgente": 4, "alta": 24, "media": 48, "baixa": 72}
    metas.update(getattr(settings, "HELPDESK_PRAZOS_HORAS", {}))
    return chamados.annotate(
        prazo=Case(
            *[
                When(prioridade=prioridade, then=F("data_criacao") + Value(timedelta(hours=horas)))
                for prioridade, horas in metas.items()
            ],
            output_field=DateTimeField(),
        ),
    )


def recortes(usuario, agora):
    return {
        "meus": Q(atribuido_a=usuario),
        "sem_responsavel": Q(atribuido_a__isnull=True),
        "urgentes": Q(prioridade="urgente"),
        "atrasados": Q(prazo__lte=agora),
    }


def visoes_fila(chamados, usuario, agora):
    totais = chamados.exclude(status__in=ENCERRADOS).aggregate(
        ativos=Count("pk"),
        **{nome: Count("pk", filter=filtro) for nome, filtro in recortes(usuario, agora).items()},
    )
    return [(nome, rotulo, icone, totais[nome or "ativos"]) for nome, rotulo, icone in VISOES]


def aplicar_visao(chamados, visao, usuario, agora):
    filtro = recortes(usuario, agora).get(visao)
    if filtro is None:
        return chamados
    chamados = chamados.exclude(status__in=ENCERRADOS).filter(filtro)
    if visao in ("atrasados", "urgentes"):
        return chamados.order_by("prazo", "pk")
    return chamados
