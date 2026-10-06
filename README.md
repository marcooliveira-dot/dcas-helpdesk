TESTE TESTE

## Ajustes de chamados — 06/10/2026

- Anexos PDF, imagens e textos compatíveis abrem no navegador em uma nova aba. Os demais formatos usam download conforme o suporte do navegador.
- Clicar na linha ou no título de um chamado abre a conversa. Botões de atendimento continuam executando sua própria ação.
- A área principal mostra chamados ativos. Resolvidos e fechados permanecem consultáveis pelo filtro de status.
- Ao marcar um atendimento como resolvido ou fechado, o sistema retorna ao painel principal.

Para aplicar em outra instalação, atualize os arquivos deste commit e reinicie o serviço da aplicação Django. Esta alteração não exige migrações de banco de dados.

Verificação: `python manage.py test chamados` executa oito testes das listas, filtros, finalização, visualização de anexos e permissões.
