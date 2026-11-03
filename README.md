TESTE TESTE

## Ajustes de chamados — 06/10/2026

- Anexos PDF, imagens e textos compatíveis abrem no navegador em uma nova aba. Os demais formatos usam download conforme o suporte do navegador.
- Clicar na linha ou no título de um chamado abre a conversa. Botões de atendimento continuam executando sua própria ação.
- A área principal mostra chamados ativos. Resolvidos e fechados permanecem consultáveis pelo filtro de status.
- Ao marcar um atendimento como resolvido ou fechado, o sistema retorna ao painel principal.

Para aplicar em outra instalação, atualize os arquivos deste commit e reinicie o serviço da aplicação Django. Esta alteração não exige migrações de banco de dados.

Verificação: `python manage.py test chamados` executa oito testes das listas, filtros, finalização, visualização de anexos e permissões.

## Visual modernizado — 03/11/2026

O sistema recebe uma identidade visual unificada: navegação lateral com indicação da página atual, cabeçalho com perfil e notificações, indicadores de atendimento, tabelas e formulários com melhor hierarquia visual. A nova tela de entrada permite mostrar ou ocultar a senha. O layout se adapta a computadores e celulares e respeita a preferência por movimento reduzido.

As regras de acesso, abertura de anexos e filtros de chamados ativos permanecem as mesmas. A atualização é de apresentação e não exige migração do banco de dados.

### Aplicar no servidor

1. Atualize os arquivos do repositório, incluindo `static/css/modern.css` e os templates modificados.
2. No ambiente virtual da aplicação, execute `python manage.py collectstatic --noinput` para publicar o novo CSS.
3. Reinicie o serviço da aplicação usando o procedimento já adotado no servidor.

Se o visual antigo ainda aparecer, recarregue a página sem usar o cache. O CSS novo usa a versão `20261103` na URL.
