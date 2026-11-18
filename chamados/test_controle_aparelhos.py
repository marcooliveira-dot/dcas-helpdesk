from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from chamados.models import Equipamento, Localizacao


class ControleAparelhosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        usuarios = get_user_model().objects
        cls.admin = usuarios.create_user("admin-bases", is_superuser=True)
        cls.tecnico = usuarios.create_user("tecnico-bases")
        cls.tecnico.perfil.tipo = "tecnico"
        cls.tecnico.perfil.save()
        cls.colaborador = usuarios.create_user("colaborador-bases")
        cls.sede = Localizacao.objects.create(nome="Sede")
        cls.filial = Localizacao.objects.create(nome="Filial")
        cls.aparelho = Equipamento.objects.create(
            patrimonio="PC-100", nome="Notebook", tipo="notebook", numero_serie="SERIE-100",
            localizacao=cls.sede, colaborador=cls.colaborador, status="em_uso",
        )
        cls.sem_base = Equipamento.objects.create(patrimonio="MON-200", nome="Monitor", tipo="monitor")

    def setUp(self):
        self.client.force_login(self.admin)
        self.controle = reverse("controle_equipamentos")
        self.alterar = reverse("alterar_base_aparelho", args=[self.aparelho.pk])

    def test_lista_exibe_base_e_permite_filtrar_e_buscar(self):
        resposta = self.client.get(self.controle)
        self.assertContains(resposta, "Controle de aparelhos")
        self.assertContains(resposta, "Sede")
        self.assertEqual(resposta.context["total"], 2)
        self.assertEqual(resposta.context["com_base"], 1)
        self.assertEqual(resposta.context["sem_base"], 1)
        for parametros, esperado in [
            ({"base": self.sede.pk, "busca": "serie-100"}, [self.aparelho.pk]),
            ({"base": "sem-base"}, [self.sem_base.pk]),
            ({"base": self.filial.pk}, []),
        ]:
            with self.subTest(parametros=parametros):
                resposta = self.client.get(self.controle, parametros)
                self.assertEqual([item.pk for item in resposta.context["pagina"]], esperado)

    def test_tecnico_altera_base_sem_mudar_responsavel_e_registra_historico(self):
        self.client.force_login(self.tecnico)
        for destino in [self.filial.pk, self.filial.pk, ""]:
            resposta = self.client.post(self.alterar, {"base": destino})
            self.assertRedirects(resposta, self.controle)
        self.aparelho.refresh_from_db()
        self.assertIsNone(self.aparelho.localizacao_id)
        self.assertEqual(self.aparelho.colaborador_id, self.colaborador.pk)
        self.assertEqual(self.aparelho.status, "em_uso")
        self.assertEqual(self.aparelho.historico.count(), 2)
        self.assertContains(self.client.get(self.alterar), "Sede → Filial")

    def test_base_invalida_nao_altera_aparelho(self):
        resposta = self.client.post(self.alterar, {"base": 99999})
        self.assertIn("base", resposta.context["form"].errors)
        self.aparelho.refresh_from_db()
        self.assertEqual(self.aparelho.localizacao_id, self.sede.pk)
        self.assertFalse(self.aparelho.historico.exists())

    def test_apenas_admin_cadastra_base_e_nome_nao_pode_repetir(self):
        url = reverse("nova_base")
        resposta = self.client.post(url, {"nome": " sede "})
        self.assertIn("nome", resposta.context["form"].errors)
        self.assertRedirects(self.client.post(url, {"nome": "Unidade Norte"}), self.controle)
        self.client.force_login(self.tecnico)
        resposta = self.client.post(url, {"nome": "Unidade Sul"})
        self.assertRedirects(resposta, reverse("dashboard"), fetch_redirect_response=False)
        self.assertFalse(Localizacao.objects.filter(nome="Unidade Sul").exists())

    def test_colaborador_nao_pode_consultar_ou_alterar_base(self):
        self.client.force_login(self.colaborador)
        self.assertEqual(self.client.get(self.controle).status_code, 302)
        self.assertEqual(self.client.post(self.alterar, {"base": self.filial.pk}).status_code, 302)
        self.aparelho.refresh_from_db()
        self.assertEqual(self.aparelho.localizacao_id, self.sede.pk)
