from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from chamados.models import Chamado


class AtendimentoFilaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        usuarios = get_user_model().objects
        cls.admin = usuarios.create_user("gestor-fila", is_superuser=True)
        cls.tecnico = usuarios.create_user("tecnico-fila")
        cls.tecnico.perfil.tipo = "tecnico"
        cls.tecnico.perfil.save()
        cls.solicitante = usuarios.create_user("solicitante-fila")
        cls.outro = usuarios.create_user("outro-fila")
        cls.vencido = cls.criar_chamado("Sem responsável", horas=5, prioridade="urgente")
        cls.assumido = cls.criar_chamado("Com técnico", horas=1, atribuido_a=cls.tecnico)
        cls.encerrado = cls.criar_chamado("Resolvido", horas=8, prioridade="urgente", status="resolvido")

    @classmethod
    def criar_chamado(cls, titulo, horas, **dados):
        chamado = Chamado.objects.create(titulo=titulo, descricao="Teste", criado_por=cls.solicitante, **dados)
        Chamado.objects.filter(pk=chamado.pk).update(data_criacao=timezone.now() - timedelta(hours=horas))
        return chamado

    def test_fila_vencida_funciona_no_painel_e_na_central(self):
        self.client.force_login(self.admin)
        for nome in ("painel_admin", "lista_chamados"):
            with self.subTest(nome=nome):
                resposta = self.client.get(reverse(nome), {"fila": "atrasados"})
                self.assertContains(resposta, "Prazo vencido")
                self.assertEqual([item.pk for item in resposta.context["pagina"]], [self.vencido.pk])
                totais = {chave: total for chave, _, _, total in resposta.context["fila_visoes"]}
                self.assertEqual(totais, {"": 2, "meus": 0, "sem_responsavel": 1, "urgentes": 1, "atrasados": 1})

    @override_settings(HELPDESK_PRAZOS_HORAS={"urgente": 6})
    def test_prazo_personalizado(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("lista_chamados"), {"fila": "atrasados"})
        self.assertEqual(list(resposta.context["pagina"]), [])

    def test_tecnico_ve_apenas_seus_chamados_na_fila_comigo(self):
        self.client.force_login(self.tecnico)
        resposta = self.client.get(reverse("lista_chamados"), {"fila": "meus"})
        self.assertEqual([item.pk for item in resposta.context["pagina"]], [self.assumido.pk])

    def test_assumir_preserva_chamado_de_outro_tecnico_e_encerrado(self):
        self.client.force_login(self.admin)
        for item in (self.vencido, self.assumido, self.encerrado):
            url = reverse("assumir_chamado", args=[item.pk])
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertRedirects(self.client.post(url), reverse("detalhe_chamado", args=[item.pk]))
            item.refresh_from_db()
        self.assertEqual(self.vencido.atribuido_a, self.admin)
        self.assertEqual(self.assumido.atribuido_a, self.tecnico)
        self.assertIsNone(self.encerrado.atribuido_a)

    def test_colaborador_nao_pode_assumir_ou_ver_fila_interna(self):
        self.client.force_login(self.outro)
        resposta = self.client.post(reverse("assumir_chamado", args=[self.vencido.pk]))
        self.assertRedirects(resposta, reverse("dashboard"), fetch_redirect_response=False)
        self.vencido.refresh_from_db()
        self.assertIsNone(self.vencido.atribuido_a)
        resposta = self.client.get(reverse("lista_chamados"), {"fila": "atrasados"})
        self.assertNotContains(resposta, "Prazo interno")
        self.assertEqual(list(resposta.context["pagina"]), [])

    def test_catalogo_sugere_categoria_sem_impedir_edicao(self):
        self.client.force_login(self.solicitante)
        url = reverse("novo_chamado")
        resposta = self.client.get(url, {"servico": "email"})
        self.assertContains(resposta, "Catálogo de suporte")
        self.assertEqual(resposta.context["form"]["categoria"].value(), "email")
        resposta = self.client.post(f"{url}?servico=email", {
            "titulo": "Problema na rede", "descricao": "Sem conexão", "categoria": "rede", "prioridade": "media",
        })
        self.assertRedirects(resposta, reverse("chamado_sucesso"))
        self.assertEqual(Chamado.objects.get(titulo="Problema na rede").categoria, "rede")
