from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from chamados.models import Equipamento, FotoEquipamento


def foto_teste(nome):
    dados = BytesIO()
    Image.new("RGB", (10, 10), "blue").save(dados, format="PNG")
    return SimpleUploadedFile(nome, dados.getvalue(), content_type="image/png")


class CadastroEquipamentoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin-equipamentos", is_superuser=True)
        cls.pessoa = User.objects.create_user("colaboradora", first_name="Pessoa", last_name="Teste")

    def setUp(self):
        self.client.force_login(self.admin)
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        storage = patch.object(FotoEquipamento._meta.get_field("imagem"), "storage", FileSystemStorage(location=pasta.name))
        storage.start()
        self.addCleanup(storage.stop)
        self.url = reverse("novo_equipamento")
        self.dados = {"patrimonio": "PC-001", "nome": "Notebook Teste", "tipo": "notebook"}

    def test_estoque_sem_termo(self):
        resposta = self.client.post(self.url, self.dados)
        equipamento = Equipamento.objects.get()
        self.assertRedirects(resposta, reverse("detalhe_equipamento", args=[equipamento.pk]))
        self.assertEqual(equipamento.status, "disponivel")
        self.assertIsNone(equipamento.colaborador_id)
        self.assertEqual(list(equipamento.movimentacoes.values_list("tipo", flat=True)), ["entrada"])

    def test_cadastro_com_entrega_fotos_e_pdf(self):
        resposta = self.client.post(self.url, {
            **self.dados, "acao": "termo", "colaborador": self.pessoa.pk,
            "termo-cpf": "52998224725",
            "fotos": [foto_teste("frente.png"), foto_teste("etiqueta.png")],
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertTrue(resposta["Content-Disposition"].startswith("inline;"))
        self.assertIn("no-store", resposta["Cache-Control"])
        self.assertTrue(resposta.content.startswith(b"%PDF-"))
        equipamento = Equipamento.objects.get()
        self.assertEqual(equipamento.colaborador_id, self.pessoa.pk)
        self.assertEqual(equipamento.status, "em_uso")
        self.assertIsNotNone(equipamento.data_entrega)
        self.assertCountEqual(equipamento.movimentacoes.values_list("tipo", flat=True), ["entrada", "saida"])
        self.assertEqual(equipamento.fotos_pc.count(), 2)
        self.assertNotIn("52998224725", str(self.client.session.items()))

    def test_cpf_invalido_volta_para_pessoa_sem_salvar(self):
        resposta = self.client.post(self.url, {
            **self.dados, "acao": "termo", "termo-nome": "Pessoa Teste", "termo-cpf": "00000000000",
        })
        self.assertEqual(resposta.context["etapa"], 1)
        self.assertIn("cpf", resposta.context["termo"].errors)
        self.assertFalse(Equipamento.objects.exists())

    def test_foto_invalida_rejeita_o_envio_inteiro(self):
        resposta = self.client.post(self.url, {
            **self.dados, "fotos": [foto_teste("frente.png"), SimpleUploadedFile("falsa.png", b"texto")],
        })
        self.assertEqual(resposta.context["etapa"], 3)
        self.assertIn("fotos", resposta.context["galeria"].errors)
        self.assertFalse(Equipamento.objects.exists())
        self.assertFalse(FotoEquipamento.objects.exists())

    def test_erro_no_pdf_nao_cria_equipamento(self):
        with patch("chamados.termos.preparar_termo", side_effect=ValueError("Modelo inválido")):
            resposta = self.client.post(self.url, {
                **self.dados, "acao": "termo", "termo-nome": "Pessoa Teste", "termo-cpf": "52998224725",
            })
        self.assertEqual(resposta.context["etapa"], 4)
        self.assertContains(resposta, "Modelo inválido")
        self.assertFalse(Equipamento.objects.exists())

    def test_galeria_acrescenta_fotos_sem_substituir_a_original(self):
        equipamento = Equipamento.objects.create(**self.dados, imagem_pc="equipamentos/imagens/original.png")
        url = reverse("imagem_pc_editar", args=[equipamento.pk])
        resposta = self.client.post(url, {"fotos": [foto_teste("frente.png"), foto_teste("lado.png")]})
        self.assertRedirects(resposta, reverse("detalhe_equipamento", args=[equipamento.pk]))
        equipamento.refresh_from_db()
        self.assertEqual(equipamento.imagem_pc.name, "equipamentos/imagens/original.png")
        self.assertEqual(equipamento.fotos_pc.count(), 2)
        foto = equipamento.fotos_pc.first()
        url_foto = reverse("imagem_pc_adicional", args=[equipamento.pk, foto.pk])
        resposta = self.client.get(url_foto)
        self.assertEqual(resposta["Content-Type"], "image/png")
        self.assertIn("no-store", resposta["Cache-Control"])
        resposta.close()
        outro = Equipamento.objects.create(**{**self.dados, "patrimonio": "PC-002"})
        self.assertEqual(self.client.get(reverse("imagem_pc_adicional", args=[outro.pk, foto.pk])).status_code, 404)
        self.client.force_login(self.pessoa)
        self.assertEqual(self.client.get(url_foto).status_code, 302)
