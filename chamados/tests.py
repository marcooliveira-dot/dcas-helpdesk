import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from chamados.models import Chamado, RespostaChamado


@override_settings(HELPDESK_EMAIL_ENABLED=False)
class ChamadosUpdateTests(TestCase):
    def setUp(self):
        media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('owner')
        cls.other = User.objects.create_user('other')
        cls.admin = User.objects.create_user('admin', is_superuser=True)
        cls.technician = User.objects.create_user('technician')
        cls.technician.perfil.tipo = 'tecnico'
        cls.technician.perfil.save()
        cls.tickets = {
            status: Chamado.objects.create(
                titulo=f'Chamado {status}', descricao='Teste',
                criado_por=cls.owner, status=status,
            )
            for status, label in Chamado.STATUS
        }

    def test_main_pages_show_active_tickets(self):
        for user, page in [
            (self.admin, 'painel_admin'),
            (self.technician, 'painel_tecnico'),
            (self.owner, 'painel_colaborador'),
            (self.admin, 'lista_chamados'),
        ]:
            with self.subTest(page=page):
                self.client.force_login(user)
                response = self.client.get(reverse(page))
                self.assertEqual(response.status_code, 200)
                results = response.context['chamados'] if page == 'painel_tecnico' else response.context['pagina']
                self.assertEqual({ticket.status for ticket in results}, {'aberto', 'em_andamento', 'aguardando'})
                self.assertContains(response, 'data-chamado-url=')

    def test_resolved_tickets_remain_available_in_filters(self):
        for user, page in [(self.admin, 'painel_admin'), (self.admin, 'lista_chamados'), (self.owner, 'painel_colaborador')]:
            with self.subTest(page=page):
                self.client.force_login(user)
                response = self.client.get(reverse(page), {'status': 'resolvido'})
                self.assertEqual([ticket.status for ticket in response.context['pagina']], ['resolvido'])

    def test_resolving_ticket_redirects_to_main_area_and_keeps_history(self):
        self.client.force_login(self.admin)
        ticket = self.tickets['aberto']
        response = self.client.post(reverse('detalhe_chamado', args=[ticket.pk]), {
            'acao': 'atendimento', 'status': 'resolvido',
            'prioridade': 'media', 'atribuido_a': '',
        })
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolvido')
        main = self.client.get(reverse('painel_admin'))
        self.assertNotIn(ticket.pk, [item.pk for item in main.context['pagina']])
        self.assertEqual(self.client.get(reverse('detalhe_chamado', args=[ticket.pk])).status_code, 200)

    def test_finalizing_from_list_removes_ticket(self):
        self.client.force_login(self.admin)
        ticket = self.tickets['em_andamento']
        self.client.post(reverse('finalizar_chamado', args=[ticket.pk]))
        response = self.client.get(reverse('painel_admin'))
        self.assertNotIn(ticket.pk, [item.pk for item in response.context['pagina']])

    def test_pdf_attachment_opens_inline_and_retains_permissions(self):
        ticket = self.tickets['aberto']
        ticket.anexo.save('evidencia.pdf', SimpleUploadedFile('evidencia.pdf', b'%PDF-1.4\n', content_type='application/pdf'))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('arquivo_chamado', args=[ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('inline;'))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        response.close()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('arquivo_chamado', args=[ticket.pk])).status_code, 404)

    def test_response_image_opens_inline(self):
        ticket = self.tickets['aberto']
        reply = RespostaChamado.objects.create(chamado=ticket, usuario=self.owner, mensagem='Evidência')
        reply.anexo.save('foto.png', SimpleUploadedFile('foto.png', b'test-image', content_type='image/png'))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('arquivo_resposta', args=[ticket.pk, reply.pk]))
        self.assertTrue(response['Content-Disposition'].startswith('inline;'))
        self.assertEqual(response['Content-Type'], 'image/png')
        response.close()
        detail = self.client.get(reverse('detalhe_chamado', args=[ticket.pk]))
        self.assertContains(detail, 'target="_blank" rel="noopener noreferrer"')

    def test_html_attachment_cannot_execute_on_app_origin(self):
        ticket = self.tickets['aberto']
        ticket.anexo.save('pagina.html', SimpleUploadedFile('pagina.html', b'<script>alert(1)</script>'))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('arquivo_chamado', args=[ticket.pk]))
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        response.close()

    def test_collaborator_cannot_see_other_users_tickets(self):
        self.client.force_login(self.other)
        for page in ['lista_chamados', 'painel_colaborador']:
            response = self.client.get(reverse(page))
            self.assertEqual(list(response.context['pagina']), [])
