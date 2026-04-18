from django.db import models
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class Hospede(LojaIsolationMixin, models.Model):
    """Cadastro de hóspedes (PF/PJ)."""

    nome = models.CharField(max_length=200)
    documento = models.CharField(max_length=30, blank=True, default='')
    telefone = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    observacoes = models.TextField(blank=True, default='')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_hospedes'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='hotel_hosp_loja_act_idx'),
            models.Index(fields=['loja_id', 'documento'], name='hotel_hosp_loja_doc_idx'),
        ]

    def __str__(self):
        return self.nome


class Quarto(LojaIsolationMixin, models.Model):
    """Unidade habitacional (apartamento/quarto)."""

    STATUS_DISPONIVEL = 'disponivel'
    STATUS_OCUPADO = 'ocupado'
    STATUS_LIMPEZA = 'limpeza'
    STATUS_MANUTENCAO = 'manutencao'
    STATUS_CHOICES = [
        (STATUS_DISPONIVEL, 'Disponível'),
        (STATUS_OCUPADO, 'Ocupado'),
        (STATUS_LIMPEZA, 'Limpeza'),
        (STATUS_MANUTENCAO, 'Manutenção'),
    ]

    numero = models.CharField(max_length=20)
    nome = models.CharField(max_length=100, blank=True, default='', help_text='Ex.: Suíte 203')
    tipo = models.CharField(max_length=80, blank=True, default='', help_text='Ex.: Standard, Luxo')
    capacidade = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL)
    observacoes = models.TextField(blank=True, default='')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_quartos'
        ordering = ['numero']
        constraints = [
            models.UniqueConstraint(fields=['loja_id', 'numero'], name='hotel_quarto_loja_numero_uniq'),
        ]
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='hotel_quarto_loja_status_idx'),
            models.Index(fields=['loja_id', 'is_active'], name='hotel_quarto_loja_act_idx'),
        ]

    def __str__(self):
        return self.nome or f'Quarto {self.numero}'


class Tarifa(LojaIsolationMixin, models.Model):
    """Tarifário base (ex.: diária padrão por tipo de quarto)."""

    nome = models.CharField(max_length=120)
    tipo_quarto = models.CharField(max_length=80, blank=True, default='')
    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_tarifas'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='hotel_tarifa_loja_act_idx'),
        ]

    def __str__(self):
        return self.nome


class Reserva(LojaIsolationMixin, models.Model):
    """Reserva (antes ou durante a hospedagem)."""

    STATUS_PENDENTE = 'pendente'
    STATUS_CONFIRMADA = 'confirmada'
    STATUS_CHECKIN = 'checkin'
    STATUS_CHECKOUT = 'checkout'
    STATUS_CANCELADA = 'cancelada'
    STATUS_NO_SHOW = 'no_show'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_CONFIRMADA, 'Confirmada'),
        (STATUS_CHECKIN, 'Check-in'),
        (STATUS_CHECKOUT, 'Check-out'),
        (STATUS_CANCELADA, 'Cancelada'),
        (STATUS_NO_SHOW, 'No-show'),
    ]

    hospede = models.ForeignKey(Hospede, on_delete=models.PROTECT, related_name='reservas')
    quarto = models.ForeignKey(Quarto, on_delete=models.PROTECT, related_name='reservas')
    tarifa = models.ForeignKey(Tarifa, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')

    data_checkin = models.DateField()
    data_checkout = models.DateField()
    adultos = models.IntegerField(default=2)
    criancas = models.IntegerField(default=0)
    canal = models.CharField(max_length=50, blank=True, default='', help_text='Ex.: Direto, Booking, Expedia')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)

    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True, default='')

    # Assinatura digital
    STATUS_ASSINATURA_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aguardando_hospede', 'Aguardando Hóspede'),
        ('aguardando_funcionario', 'Aguardando Funcionário'),
        ('concluido', 'Concluído'),
    ]
    status_assinatura = models.CharField(max_length=25, choices=STATUS_ASSINATURA_CHOICES, default='rascunho')
    conteudo_confirmacao = models.TextField(blank=True, default='', help_text='Texto da confirmação enviada ao hóspede')
    nome_hospede_assinatura = models.CharField(max_length=200, blank=True, default='')
    nome_funcionario_assinatura = models.CharField(max_length=200, blank=True, default='')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_reservas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='hotel_reserva_loja_status_idx'),
            models.Index(fields=['loja_id', 'data_checkin'], name='hotel_reserva_loja_in_idx'),
            models.Index(fields=['loja_id', 'data_checkout'], name='hotel_reserva_loja_out_idx'),
            models.Index(fields=['loja_id', 'is_active'], name='hotel_reserva_loja_act_idx'),
        ]

    def __str__(self):
        return f'Reserva {self.hospede.nome} - {self.quarto.numero}'


class GovernancaTarefa(LojaIsolationMixin, models.Model):
    """Pendências de governança / limpeza / manutenção associadas ao quarto."""

    TIPO_LIMPEZA = 'limpeza'
    TIPO_MANUTENCAO = 'manutencao'
    TIPO_ENXOVAL = 'enxoval'
    TIPO_OUTROS = 'outros'
    TIPO_CHOICES = [
        (TIPO_LIMPEZA, 'Limpeza'),
        (TIPO_MANUTENCAO, 'Manutenção'),
        (TIPO_ENXOVAL, 'Enxoval'),
        (TIPO_OUTROS, 'Outros'),
    ]

    STATUS_ABERTA = 'aberta'
    STATUS_EM_ANDAMENTO = 'em_andamento'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CHOICES = [
        (STATUS_ABERTA, 'Aberta'),
        (STATUS_EM_ANDAMENTO, 'Em andamento'),
        (STATUS_CONCLUIDA, 'Concluída'),
    ]

    quarto = models.ForeignKey(Quarto, on_delete=models.PROTECT, related_name='tarefas_governanca')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_LIMPEZA)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ABERTA)
    descricao = models.CharField(max_length=255, blank=True, default='')
    prioridade = models.IntegerField(default=2, help_text='1=alta, 2=média, 3=baixa')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_governanca_tarefas'
        ordering = ['status', 'prioridade', '-created_at']
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='hotel_gov_loja_status_idx'),
            models.Index(fields=['loja_id', 'tipo'], name='hotel_gov_loja_tipo_idx'),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} - Quarto {self.quarto.numero}'



class Funcionario(LojaIsolationMixin, models.Model):
    """Funcionário do hotel (recepcionista, camareira, etc.)."""

    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, default='')
    cargo = models.CharField(max_length=100, blank=True, default='')
    telefone = models.CharField(max_length=30, blank=True, default='')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_funcionarios'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='hotel_func_loja_act_idx'),
        ]

    def __str__(self):
        return self.nome


class ReservaTemplate(LojaIsolationMixin, models.Model):
    """Template de mensagem para confirmação de reserva."""

    nome = models.CharField(max_length=200)
    conteudo = models.TextField(help_text='Texto da confirmação. Use {hospede}, {quarto}, {checkin}, {checkout}, {valor_total}, {diarias} como variáveis.')
    is_padrao = models.BooleanField(default=False, help_text='Template padrão para novas confirmações')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_reserva_templates'
        ordering = ['-is_padrao', 'nome']
        indexes = [
            models.Index(fields=['loja_id', 'ativo'], name='hotel_restpl_loja_act_idx'),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.is_padrao:
            ReservaTemplate.objects.filter(loja_id=self.loja_id, is_padrao=True).exclude(pk=self.pk).update(is_padrao=False)
        super().save(*args, **kwargs)


class ReservaAssinatura(LojaIsolationMixin, models.Model):
    """Registro de assinatura digital para Reservas de hotel."""

    TIPO_CHOICES = [
        ('hospede', 'Hóspede'),
        ('funcionario', 'Funcionário'),
    ]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='assinaturas')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    nome_assinante = models.CharField(max_length=200)
    email_assinante = models.EmailField()

    ip_address = models.GenericIPAddressField(default='0.0.0.0')
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True, default='')

    token = models.CharField(max_length=255, unique=True, db_index=True)
    token_expira_em = models.DateTimeField()

    assinado = models.BooleanField(default=False)
    assinado_em = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'hotel_reserva_assinaturas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loja_id', 'token'], name='hotel_rassin_loja_tok_idx'),
            models.Index(fields=['reserva', 'tipo'], name='hotel_rassin_res_tipo_idx'),
        ]

    def __str__(self):
        status = 'Assinado' if self.assinado else 'Pendente'
        return f"{self.get_tipo_display()} - {self.nome_assinante} ({status})"

    @property
    def is_expirado(self):
        from django.utils import timezone
        return timezone.now() > self.token_expira_em
