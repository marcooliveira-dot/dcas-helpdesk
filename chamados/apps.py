from django.apps import AppConfig


class ChamadosConfig(AppConfig):
    name = "chamados"

    def ready(self):
        from . import notificacoes
