from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from pypdf import PdfReader

from chamados.models import Equipamento


class TermoMultiploTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin-termos", is_superuser=True)
        cls.pessoa = User.objects.create_user("responsavel")
        cls.outra_pessoa = User.objects.create_user("outro-usuario")
        cls.principal = cls.criar_equipamento("PC-01", "Notebook", cls.pessoa)
        cls.adicional = cls.criar_equipamento("MON-02", "Monitor", cls.pessoa)
        cls.alheio = cls.criar_equipamento("PC-03", "Desktop", cls.outra_pessoa)
        cls.estoque = Equipamento.objects.create(patrimonio="PC-04", nome="Reserva", tipo="desktop")

    @staticmethod
    def criar_equipamento(patrimonio, nome, pessoa):
        return Equipamento.objects.create(
            patrimonio=patrimonio, nome=nome, tipo="outro", colaborador=pessoa, status="em_uso",
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("termo_equipamento", args=[self.principal.pk])
        self.dados = {"nome": "Pessoa de Teste", "cpf": "52998224725"}

    def test_termo_individual_mantem_uma_pagina(self):
        resposta = self.client.post(self.url, self.dados)
        pdf = PdfReader(BytesIO(resposta.content))
        self.assertEqual(len(pdf.pages), 1)
        self.assertIn("PC-01", pdf.pages[0].extract_text())

    def test_termo_inclui_patrimonios_do_mesmo_colaborador(self):
        resposta = self.client.post(self.url, {
            **self.dados, "equipamentos_adicionais": [self.adicional.pk],
        })
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertIn("no-store", resposta["Cache-Control"])
        pdf = PdfReader(BytesIO(resposta.content))
        self.assertEqual(len(pdf.pages), 2)
        self.assertIn("Anexo A", pdf.pages[0].extract_text())
        anexo = pdf.pages[1].extract_text()
        for item in ("PC-01", "Notebook", "MON-02", "Monitor"):
            self.assertIn(item, anexo)
        self.assertNotIn("PC-03", anexo)

    def test_rejeita_outro_responsavel_estoque_e_principal_duplicado(self):
        for item in (self.alheio, self.estoque, self.principal):
            with self.subTest(item=item.patrimonio):
                resposta = self.client.post(self.url, {
                    **self.dados, "equipamentos_adicionais": [item.pk],
                })
                self.assertIn("equipamentos_adicionais", resposta.context["form"].errors)

    def test_cadastro_gera_termo_com_novo_e_existente(self):
        resposta = self.client.post(reverse("novo_equipamento"), {
            "acao": "termo", "colaborador": self.pessoa.pk,
            "nome": "Novo computador", "patrimonio": "PC-05", "tipo": "notebook",
            "termo-nome": self.dados["nome"], "termo-cpf": self.dados["cpf"],
            "termo-equipamentos_adicionais": [self.adicional.pk],
        })
        pdf = PdfReader(BytesIO(resposta.content))
        texto = pdf.pages[1].extract_text()
        self.assertIn("PC-05", texto)
        self.assertIn("MON-02", texto)
        self.assertEqual(Equipamento.objects.get(patrimonio="PC-05").colaborador, self.pessoa)
        self.adicional.refresh_from_db()
        self.assertEqual(self.adicional.movimentacoes.count(), 0)

    def test_opcoes_exigem_acesso_e_filtram_por_responsavel(self):
        url = reverse("opcoes_termo")
        resposta = self.client.get(url, {"colaborador": self.pessoa.pk})
        self.assertCountEqual(
            [item["id"] for item in resposta.json()["equipamentos"]],
            [self.principal.pk, self.adicional.pk],
        )
        self.client.force_login(self.pessoa)
        self.assertEqual(self.client.get(url, {"colaborador": self.pessoa.pk}).status_code, 302)

    def test_anexo_com_muitos_equipamentos_nao_perde_a_ultima_linha(self):
        adicionais = [
            self.criar_equipamento(f"ANEXO-{indice:02}", "Monitor de teste", self.pessoa).pk
            for indice in range(50)
        ]
        resposta = self.client.post(self.url, {**self.dados, "equipamentos_adicionais": adicionais})
        pdf = PdfReader(BytesIO(resposta.content))
        self.assertGreater(len(pdf.pages), 2)
        self.assertIn("ANEXO-49", pdf.pages[-1].extract_text())
