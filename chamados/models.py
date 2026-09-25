from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


# ==========================================================
# PERFIL
# ==========================================================

class Perfil(models.Model):
    foto_perfil = models.ImageField(upload_to="perfis/", blank=True, null=True)

    TIPO = (
        ("colaborador", "Colaborador"),
        ("tecnico", "Técnico"),
        ("admin", "Administrador"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO,
        default="colaborador"
    )

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.tipo})"


# ==========================================================
# CHAMADOS
# ==========================================================

class Chamado(models.Model):

    STATUS = (
        ("aberto", "Aberto"),
        ("em_andamento", "Em andamento"),
        ("aguardando", "Aguardando Cliente"),
        ("resolvido", "Resolvido"),
        ("fechado", "Fechado"),
    )

    PRIORIDADE = (
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    )
    CATEGORIAS = (
        ("hardware", "Hardware"),
        ("software", "Software"),
        ("rede", "Rede / Internet"),
        ("email", "Email"),
        ("sistema_interno", "Sistema Interno"),
    )

    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS,
        blank=True,
        default="",
    )
    ticket = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    titulo = models.CharField(
        max_length=200
    )

    descricao = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="aberto"
    )

    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE,
        default="media"
    )

    criado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chamados_criados"
    )

    atribuido_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_atribuidos"
    )

    anexo = models.FileField(
        upload_to="anexos/",
        blank=True,
        null=True
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["-data_criacao"]

    def save(self, *args, **kwargs):

        if not self.ticket:

            ultimo = Chamado.objects.order_by("id").last()

            numero = ultimo.id + 1 if ultimo else 1

            self.ticket = f"TK-{numero:06d}"

        super().save(*args, **kwargs)

    def __str__(self):

        return self.ticket


# ==========================================================
# RESPOSTAS DOS CHAMADOS
# ==========================================================

class RespostaChamado(models.Model):

    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="respostas"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    mensagem = models.TextField()

    anexo = models.FileField(
        upload_to="respostas/",
        blank=True,
        null=True
    )

    data = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["data"]

    def __str__(self):

        return f"{self.usuario} - {self.chamado.ticket}"

        # ==========================================================
# CATEGORIAS
# ==========================================================

class Categoria(models.Model):

    nome = models.CharField(
        max_length=100,
        unique=True
    )

    descricao = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


# ==========================================================
# FABRICANTES
# ==========================================================

class Fabricante(models.Model):

    nome = models.CharField(
        max_length=150,
        unique=True
    )

    site = models.URLField(
        blank=True
    )

    telefone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ==========================================================
# FORNECEDORES
# ==========================================================

class Fornecedor(models.Model):

    nome = models.CharField(max_length=150)

    cnpj = models.CharField(
        max_length=20,
        blank=True
    )

    contato = models.CharField(
        max_length=100,
        blank=True
    )

    telefone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    endereco = models.TextField(
        blank=True
    )

    observacao = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ==========================================================
# DEPARTAMENTOS
# ==========================================================

class Departamento(models.Model):

    nome = models.CharField(
        max_length=100,
        unique=True
    )

    gestor = models.CharField(
        max_length=150,
        blank=True
    )

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ==========================================================
# LOCALIZAÇÕES
# ==========================================================

class Localizacao(models.Model):

    nome = models.CharField(
        max_length=100,
        unique=True
    )

    endereco = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ==========================================================
# EQUIPAMENTOS
# ==========================================================

class Equipamento(models.Model):
    imagem_pc = models.ImageField(upload_to="equipamentos/imagens/", blank=True, null=True)

    STATUS = (

        ("disponivel", "Disponível"),

        ("em_uso", "Em Uso"),

        ("manutencao", "Em Manutenção"),

        ("defeito", "Com Defeito"),

        ("reservado", "Reservado"),

        ("baixado", "Baixado"),

    )

    TIPO = (

        ("notebook", "Notebook"),

        ("desktop", "Desktop"),

        ("monitor", "Monitor"),

        ("mouse", "Mouse"),

        ("teclado", "Teclado"),

        ("headset", "Headset"),

        ("impressora", "Impressora"),

        ("tablet", "Tablet"),

        ("celular", "Celular"),

        ("switch", "Switch"),

        ("roteador", "Roteador"),

        ("servidor", "Servidor"),

        ("nobreak", "Nobreak"),

        ("carregador", "Carregador"),

        ("outro", "Outro"),

    )

    patrimonio = models.CharField(
        max_length=50,
        unique=True
    )

    patrimonio_antigo = models.CharField(
        max_length=50,
        blank=True
    )

    numero_serie = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    nome = models.CharField(
        max_length=150
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPO
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fabricante = models.ForeignKey(
        Fabricante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    colaborador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipamentos_recebidos"
    )

    marca = models.CharField(
        max_length=100,
        blank=True
    )

    modelo = models.CharField(
        max_length=100,
        blank=True
    )

    processador = models.CharField(
        max_length=100,
        blank=True
    )

    memoria = models.CharField(
        max_length=100,
        blank=True
    )

    armazenamento = models.CharField(
        max_length=100,
        blank=True
    )

    sistema_operacional = models.CharField(
        max_length=100,
        blank=True
    )

    endereco_mac = models.CharField(
        max_length=30,
        blank=True
    )

    endereco_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    nota_fiscal = models.CharField(
        max_length=100,
        blank=True
    )

    data_compra = models.DateField(
        null=True,
        blank=True
    )

    garantia = models.DateField(
        null=True,
        blank=True
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="disponivel"
    )

    data_entrega = models.DateTimeField(
        null=True,
        blank=True
    )

    data_devolucao = models.DateTimeField(
        null=True,
        blank=True
    )

    foto = models.FileField(
        upload_to="equipamentos/",
        blank=True,
        null=True
    )

    qr_code = models.ImageField(
        upload_to="qrcode/",
        blank=True,
        null=True
    )

    observacao = models.TextField(
        blank=True
    )

    ativo = models.BooleanField(
        default=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["patrimonio"]

        verbose_name = "Equipamento"

        verbose_name_plural = "Equipamentos"

    def __str__(self):
        return f"{self.patrimonio} - {self.nome}"

        # ==========================================================
# MOVIMENTAÇÕES
# ==========================================================

class Movimentacao(models.Model):

    TIPO = (
        ("entrada", "Entrada"),
        ("saida", "Saída"),
        ("transferencia", "Transferência"),
        ("devolucao", "Devolução"),
        ("emprestimo", "Empréstimo"),
        ("manutencao", "Manutenção"),
        ("defeito", "Defeito"),
        ("baixa", "Baixa Patrimonial"),
    )

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE,
        related_name="movimentacoes"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="movimentacoes_realizadas"
    )

    colaborador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_colaborador"
    )

    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO
    )

    observacao = models.TextField(blank=True)

    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.equipamento.patrimonio} - {self.get_tipo_display()}"


responsavel = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="movimentacoes_responsavel"
)

arquivo = models.FileField(
    upload_to="termos/",
    blank=True,
    null=True
)

# ==========================================================
# MANUTENÇÕES
# ==========================================================

class Manutencao(models.Model):

    STATUS = (
        ("aberta", "Aberta"),
        ("andamento", "Em andamento"),
        ("aguardando", "Aguardando Peças"),
        ("concluida", "Concluída"),
        ("cancelada", "Cancelada"),
    )

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE,
        related_name="manutencoes"
    )

    empresa = models.CharField(max_length=150)

    tecnico = models.CharField(
        max_length=150,
        blank=True
    )

    problema = models.TextField()

    solucao = models.TextField(blank=True)

    custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    data_envio = models.DateField()

    data_retorno = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="aberta"
    )

    laudo = models.FileField(
        upload_to="laudos/",
        blank=True,
        null=True
    )

    observacao = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.equipamento.patrimonio}"


# ==========================================================
# DEFEITOS
# ==========================================================

class Defeito(models.Model):

    PRIORIDADE = (
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    )

    STATUS = (
        ("aberto", "Aberto"),
        ("analise", "Em análise"),
        ("resolvido", "Resolvido"),
    )

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE,
        related_name="defeitos"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    descricao = models.TextField()

    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE,
        default="media"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="aberto"
    )

    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return self.equipamento.patrimonio


# ==========================================================
# TERMO DE RESPONSABILIDADE
# ==========================================================

class TermoResponsabilidade(models.Model):

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE
    )

    colaborador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="termos_recebidos"
    )

    entregue_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="termos_entregues"
    )

    data_entrega = models.DateTimeField(default=timezone.now)

    data_devolucao = models.DateTimeField(
        null=True,
        blank=True
    )

    assinado = models.BooleanField(default=False)

    pdf = models.FileField(
        upload_to="termos/",
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-data_entrega"]

    def __str__(self):
        return f"{self.colaborador} - {self.equipamento}"


# ==========================================================
# HISTÓRICO
# ==========================================================

class HistoricoEquipamento(models.Model):

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE,
        related_name="historico"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    acao = models.CharField(max_length=200)

    descricao = models.TextField(blank=True)

    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.equipamento.patrimonio} - {self.acao}"


# ==========================================================
# SIGNALS
# ==========================================================

@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):

    if created:
        Perfil.objects.create(
            user=instance,
            tipo="colaborador"
        )


@receiver(post_save, sender=Movimentacao)
def criar_historico(sender, instance, created, **kwargs):

    if created:

        HistoricoEquipamento.objects.create(

            equipamento=instance.equipamento,

            usuario=instance.usuario,

            acao=instance.get_tipo_display(),

            descricao=instance.observacao

        )
class Notificacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avisos_helpdesk')
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='avisos')
    texto = models.CharField(max_length=120)
    criada_em = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    email_enviado = models.BooleanField(default=False)
    class Meta:
        indexes = [models.Index(fields=['usuario', 'lida'], name='aviso_usuario_lida_idx')]
