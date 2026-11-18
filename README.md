TESTE TESTE

## Controle de aparelhos por base

A aba **Controle de aparelhos** reaproveita as localizações existentes como bases e lista patrimônio, aparelho, base, responsável e status. É possível buscar por nome, patrimônio ou série e filtrar por base ou por aparelhos sem base definida. Administradores cadastram bases; administradores e técnicos podem alterar vínculos e consultar as últimas mudanças. Alterar a base não muda o responsável nem o status do equipamento. Não exige nova migração.

## Central de atendimento: filas, prazos e catálogo

- Administradores e técnicos podem acompanhar chamados ativos **Comigo**, **Sem responsável**, **Urgentes** e com **Prazo vencido**. Os indicadores contam toda a fila ativa; a pesquisa e o filtro por status afetam apenas a lista exibida.
- **Assumir chamado** atribui um chamado ativo sem responsável ao técnico ou administrador conectado, sem sobrescrever o trabalho de outro agente.
- Os prazos iniciais são metas internas em horas corridas desde a abertura: urgente = 4 h, alta = 24 h, média = 48 h e baixa = 72 h. A prioridade atual define a meta; aguardar o cliente não pausa o relógio. Chamados resolvidos e fechados não entram na fila de vencidos. Para ajustar as metas, configure `HELPDESK_PRAZOS_HORAS` nas configurações Django (por exemplo, `{"urgente": 2, "alta": 12, "media": 24, "baixa": 48}`). Não há calendário de dias úteis nem escalonamento automático.
- Na abertura, o catálogo sugere a categoria e mostra orientações sobre o que informar, mantendo a opção manual.

Não exige migração. Atualize o código e reinicie a aplicação.

Referências de produto: [InvGate Service Management](https://invgate.com/service-management) e [Freshservice](https://www.freshworks.com/freshservice/features/).

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

## Cadastro de equipamentos em etapas — 05/11/2026

O cadastro reúne dados da pessoa, do equipamento, fotos e termo de responsabilidade. Vincular um usuário ativo registra a entrega; deixar o vínculo vazio mantém o equipamento em estoque. O termo é opcional e o CPF informado é usado somente para gerar o PDF, sem ser gravado no cadastro.

A galeria mantém a foto anterior e aceita novos envios de até 10 imagens JPEG, PNG ou WebP (8 MB por imagem e 32 MB somados). As fotos novas ficam em `private_uploads/` por padrão, fora de `MEDIA_ROOT`, e são servidas pelas rotas autenticadas do Django.

O termo de responsabilidade pode reunir o equipamento principal e até 50 itens adicionais ativos e em uso pelo mesmo colaborador. Selecione-os na última etapa de um novo cadastro ou em **Gerar termo de responsabilidade**, nos detalhes de um equipamento existente. O PDF lista todos os patrimônios no Anexo A, integrante do mesmo termo. Esta alteração não exige nova migração.

Para atualizar o servidor, faça backup do banco, aplique `python manage.py migrate` e reinicie a aplicação. Garanta acesso de escrita ao diretório privado pelo processo Django, inclua-o no backup e não o exponha no nginx. Se necessário, ajuste o limite do corpo da requisição no proxy para permitir os uploads previstos.
