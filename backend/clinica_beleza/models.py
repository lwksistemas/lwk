"""
Models para Clínica da Beleza
Sistema completo de gestão de clínica estética
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from core.mixins import LojaIsolationMixin, LojaIsolationManager
from agenda_base.models import ClienteBase, ProfissionalBase, ServicoBase, HorarioTrabalhoProfissionalBase, BloqueioAgendaBase

User = get_user_model()


class Patient(ClienteBase):
    """Pacientes da clínica (herda de ClienteBase)"""
    allow_whatsapp = models.BooleanField(
        default=True,
        verbose_name="Permitir WhatsApp",
        help_text="Se desmarcado, o paciente não recebe mensagens por WhatsApp (LGPD).",
    )
    convenio = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pacientes',
        verbose_name='Convênio padrão',
        help_text='Convênio sugerido ao agendar ou abrir consulta.',
    )

    # DEPRECATED: aliases inglês→português mantidos apenas para o management command
    # popular_loja_clinica_beleza. O mapeamento real é feito em views_pacientes._map_patient_data.
    @property
    def name(self):
        return self.nome

    @name.setter
    def name(self, value):
        self.nome = value

    @property
    def phone(self):
        return self.telefone

    @phone.setter
    def phone(self, value):
        self.telefone = value

    class Meta(ClienteBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Professional(ProfissionalBase):
    """Profissionais da clínica (herda de ProfissionalBase)"""

    CONSELHO_CHOICES = (
        ('CRM', 'CRM - Medicina'),
        ('CRO', 'CRO - Odontologia'),
        ('COREN', 'COREN - Enfermagem'),
        ('CRF', 'CRF - Farmácia'),
        ('CRP', 'CRP - Psicologia'),
        ('CRN', 'CRN - Nutrição'),
        ('CREFITO', 'CREFITO - Fisioterapia/TO'),
        ('CRBM', 'CRBM - Biomedicina'),
        ('CRMV', 'CRMV - Veterinária'),
        ('CRFa', 'CRFa - Fonoaudiologia'),
    )

    # Dados do prescritor para integração com a Memed (receituário/exames).
    conselho = models.CharField(
        max_length=10, blank=True, null=True,
        choices=CONSELHO_CHOICES, verbose_name="Conselho",
        help_text="Conselho de classe (CRM, COREN, CRF, etc.)",
    )
    conselho_uf = models.CharField(
        max_length=2, blank=True, null=True, verbose_name="UF do conselho",
    )
    cpf = models.CharField(
        max_length=14, blank=True, null=True, verbose_name="CPF",
        help_text="CPF do prescritor (usado para assinar na Memed).",
    )
    SEXO_CHOICES = (
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    )
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name="Data de nascimento",
        help_text="Data de nascimento do prescritor (usada no cadastro da Memed).",
    )
    sexo = models.CharField(
        max_length=1, blank=True, null=True, choices=SEXO_CHOICES,
        verbose_name="Sexo", help_text="Sexo do prescritor (usado no cadastro da Memed).",
    )

    class Meta(ProfissionalBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.especialidade}"


class ProfessionalCommission(LojaIsolationMixin, models.Model):
    """
    Configuração de comissão por profissional.
    Permite comissão por consulta (atendimento) e por procedimento específico.
    Cada tipo pode ser valor fixo (R$) ou percentual (%).
    """
    TIPO_CHOICES = (
        ('consulta', 'Por consulta (atendimento)'),
        ('procedimento', 'Por procedimento'),
    )
    MODO_CHOICES = (
        ('percentual', 'Percentual (%)'),
        ('fixo', 'Valor fixo (R$)'),
    )

    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='comissoes',
        verbose_name='Profissional',
    )
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES,
        verbose_name='Tipo de comissão',
    )
    modo = models.CharField(
        max_length=15, choices=MODO_CHOICES, default='percentual',
        verbose_name='Modo de cálculo',
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Valor',
        help_text='Percentual (ex: 30.00 = 30%) ou valor fixo em R$.',
    )
    procedure = models.ForeignKey(
        'Procedure',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='comissoes',
        verbose_name='Procedimento',
        help_text='Obrigatório quando tipo = procedimento. Vazio em consulta.',
    )
    local_atendimento = models.ForeignKey(
        'LocalAtendimento',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='comissoes',
        verbose_name='Local de atendimento',
        help_text='Obrigatório quando tipo = consulta: comissão para este local de atendimento.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_professional_commissions'
        ordering = ['professional', 'tipo', 'procedure']
        verbose_name = 'Comissão do profissional'
        verbose_name_plural = 'Comissões dos profissionais'

    def __str__(self):
        if self.tipo == 'procedimento' and self.procedure:
            return f"{self.professional.nome} — {self.procedure.nome}: {self.valor_display}"
        if self.local_atendimento_id:
            return f"{self.professional.nome} — Consulta ({self.local_atendimento.nome}): {self.valor_display}"
        return f"{self.professional.nome} — Consulta (geral): {self.valor_display}"

    @property
    def valor_display(self):
        if self.modo == 'percentual':
            return f"{self.valor}%"
        return f"R$ {self.valor}"


class Procedure(ServicoBase):
    """Procedimentos/Serviços oferecidos (herda de ServicoBase)"""

    class Meta(ServicoBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ProcedureProtocol(LojaIsolationMixin, models.Model):
    """Protocolos padronizados vinculados a procedimentos (Clínica da Beleza)."""
    nome = models.CharField(max_length=200, verbose_name='Nome do protocolo')
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='protocolos',
        verbose_name='Procedimento',
    )
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    preparacao = models.TextField(blank=True, default='', verbose_name='Preparação')
    execucao = models.TextField(blank=True, default='', verbose_name='Execução')
    pos_procedimento = models.TextField(blank=True, default='', verbose_name='Pós-procedimento')
    tempo_estimado = models.PositiveIntegerField(default=30, verbose_name='Tempo estimado (min)')
    materiais_necessarios = models.TextField(blank=True, default='', verbose_name='Materiais necessários')
    contraindicacoes = models.TextField(blank=True, default='', verbose_name='Contraindicações')
    cuidados_especiais = models.TextField(blank=True, default='', verbose_name='Cuidados especiais')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_protocolos'
        ordering = ['procedure__nome', 'nome']
        verbose_name = 'Protocolo de procedimento'
        verbose_name_plural = 'Protocolos de procedimentos'

    def __str__(self):
        return f'{self.procedure.nome} — {self.nome}'


class Appointment(LojaIsolationMixin, models.Model):
    """Agendamentos"""
    STATUS_CHOICES = (
        ('CONFIRMED', 'Confirmado'),
        ('PENDING', 'Pendente'),
        ('SCHEDULED', 'Agendado'),
        ('IN_PROGRESS', 'Em Atendimento'),
        ('COMPLETED', 'Concluído'),
        ('CANCELLED', 'Cancelado'),
        ('NO_SHOW', 'Faltou'),
    )

    date = models.DateTimeField(verbose_name="Data e Hora")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name="Status")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Paciente")
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, verbose_name="Profissional")
    procedure = models.ForeignKey(
        Procedure, on_delete=models.CASCADE, verbose_name="Procedimento principal",
        null=True, blank=True,
        help_text="Legado: procedimento único. Use appointment_procedures para múltiplos.",
    )
    procedures = models.ManyToManyField(
        Procedure, through='AppointmentProcedure',
        related_name='appointments_multi', blank=True,
        verbose_name="Procedimentos",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    convenio = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
        verbose_name='Convênio',
        help_text='Convênio do atendimento (define preços dos procedimentos).',
    )
    duracao_minutos = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duração efetiva (min)",
        help_text="Opcional. Se vazio, usa a duração cadastrada do procedimento.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    # Sincronização offline: version para detectar conflitos; updated_by_id = ID do user (schema public)
    version = models.PositiveIntegerField(default=1, verbose_name="Versão")
    updated_by_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Atualizado por (user id)")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['professional', 'date']),
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['loja_id', 'date']),
        ]

    def __str__(self):
        nomes = ', '.join(
            self.procedures.values_list('nome', flat=True)
        ) if self.procedures.exists() else (self.procedure.nome if self.procedure_id else '—')
        return f"{self.patient.nome} - {nomes} - {self.date.strftime('%d/%m/%Y %H:%M')}"

    def get_duracao_efetiva(self) -> int:
        """Duração efetiva: campo manual > soma dos procedimentos > procedimento principal."""
        if self.duracao_minutos is not None:
            return self.duracao_minutos
        # Soma dos procedimentos extras (se houver)
        total = sum(
            ap.duracao_minutos or ap.procedure.duracao_minutos
            for ap in self.appointment_procedures.select_related('procedure').all()
        )
        if total > 0:
            return total
        # Fallback: procedimento principal (legado)
        if self.procedure_id:
            return self.procedure.duracao_minutos
        return 30

    @property
    def valor_total(self):
        """Valor total: soma dos preços de todos os procedimentos."""
        from decimal import Decimal
        total = sum(
            (ap.valor or ap.procedure.preco or Decimal('0'))
            for ap in self.appointment_procedures.select_related('procedure').all()
        )
        if total > 0:
            return total
        if self.procedure_id:
            return self.procedure.preco or Decimal('0')
        return Decimal('0')


class AppointmentProcedure(LojaIsolationMixin, models.Model):
    """
    Procedimentos de um agendamento — permite N procedimentos por agendamento.
    Cada item tem sua duração (override opcional) e valor.
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='appointment_procedures',
        verbose_name='Agendamento',
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        verbose_name='Procedimento',
    )
    duracao_minutos = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Duração (min)',
        help_text='Opcional. Se vazio, usa a duração cadastrada do procedimento.',
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor (R$)',
        help_text='Opcional. Se vazio, usa o preço cadastrado do procedimento.',
    )
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_appointment_procedures'
        ordering = ['ordem', 'id']
        verbose_name = 'Procedimento do agendamento'
        verbose_name_plural = 'Procedimentos do agendamento'

    def __str__(self):
        return f"{self.procedure.nome} ({self.get_duracao() or '?'} min)"

    def get_duracao(self) -> int:
        return self.duracao_minutos or self.procedure.duracao_minutos

    def get_valor(self):
        from decimal import Decimal
        return self.valor or self.procedure.preco or Decimal('0')


class BloqueioHorario(BloqueioAgendaBase):
    """
    Bloqueio de horário na agenda (herda de BloqueioAgendaBase)
    profissional=None = bloqueio geral (todos os profissionais).
    """
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Profissional",
        help_text="Deixe vazio para bloqueio geral (todos)",
    )
    
    # Campos adicionais específicos (mantém compatibilidade)
    motivo = models.CharField(max_length=100, verbose_name="Motivo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    # Aliases para compatibilidade
    @property
    def data_inicio_dt(self):
        """Retorna data_inicio como datetime para compatibilidade"""
        from datetime import datetime, time
        if self.horario_inicio:
            return datetime.combine(self.data_inicio, self.horario_inicio)
        return datetime.combine(self.data_inicio, time.min)
    
    @property
    def data_fim_dt(self):
        """Retorna data_fim como datetime para compatibilidade"""
        from datetime import datetime, time
        if self.horario_fim:
            return datetime.combine(self.data_fim, self.horario_fim)
        return datetime.combine(self.data_fim, time.max)

    class Meta(BloqueioAgendaBase.Meta):
        app_label = "clinica_beleza"
        verbose_name = "Bloqueio de Horário"
        verbose_name_plural = "Bloqueios de Horário"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=['data_inicio', 'data_fim']),
            models.Index(fields=['professional', 'data_inicio']),
            models.Index(fields=['loja_id', 'data_inicio']),
        ]

    def __str__(self):
        return f"{self.motivo} ({self.data_inicio} - {self.data_fim})"
    
    def save(self, *args, **kwargs):
        # Sincronizar motivo com titulo
        if not self.titulo:
            self.titulo = self.motivo
        # Definir tipo padrão se não especificado
        if not self.tipo:
            self.tipo = 'outros'
        super().save(*args, **kwargs)


class HorarioTrabalhoProfissional(HorarioTrabalhoProfissionalBase):
    """
    Dias e horários de trabalho por profissional (herda de HorarioTrabalhoProfissionalBase)
    Um registro por dia da semana em que o profissional trabalha (ex.: Seg 08:00-18:00).
    """
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='horarios_trabalho',
        verbose_name="Profissional",
    )

    class Meta(HorarioTrabalhoProfissionalBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Horário de trabalho (profissional)"
        verbose_name_plural = "Horários de trabalho (profissionais)"
        ordering = ['professional', 'dia_semana']
        unique_together = [['professional', 'dia_semana']]
        indexes = [
            models.Index(fields=['professional', 'dia_semana']),
            models.Index(fields=['loja_id', 'professional']),
        ]

    def __str__(self):
        return f"{self.professional.nome} - {self.get_dia_semana_display()}: {self.hora_entrada}-{self.hora_saida}"


class Payment(LojaIsolationMixin, models.Model):
    """Pagamentos"""
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Dinheiro'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('DEBIT_CARD', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('TRANSFER', 'Transferência'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('PAID', 'Pago'),
        ('CANCELLED', 'Cancelado'),
    )

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, verbose_name="Agendamento")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Método de Pagamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name="Data do Pagamento")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    comissao_percentual = models.PositiveSmallIntegerField(default=0, verbose_name="Comissão %")
    comissao_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Comissão R$")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'payment_date']),
            models.Index(fields=['appointment', 'status']),
            models.Index(fields=['loja_id', 'payment_date']),
        ]

    def save(self, *args, **kwargs):
        if self.amount is not None and self.comissao_percentual is not None:
            self.comissao_valor = (self.amount * self.comissao_percentual / 100).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento {self.id} - R$ {self.amount}"


class CampanhaPromocao(LojaIsolationMixin, models.Model):
    """
    Campanha de promoção: mensagem enviada em massa aos pacientes via WhatsApp.
    Tabela isolada por loja: cada loja tem sua própria tabela no schema (loja_*).
    Router: clinica_beleza está em loja_apps; migrate_all_lojas aplica em cada schema.
    """
    titulo = models.CharField(max_length=200, verbose_name="Título da campanha")
    mensagem = models.TextField(verbose_name="Mensagem (enviada por WhatsApp)")
    data_inicio = models.DateField(blank=True, null=True, verbose_name="Vigência início")
    data_fim = models.DateField(blank=True, null=True, verbose_name="Vigência fim")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    enviada_em = models.DateTimeField(blank=True, null=True, verbose_name="Enviada em")
    total_enviados = models.PositiveIntegerField(default=0, verbose_name="Total de mensagens enviadas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Campanha de promoção"
        verbose_name_plural = "Campanhas de promoções"
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo


# ═══════════════════════════════════════════════════════════════════════════════
# ESTOQUE — Controle de produtos (botox, ácido hialurônico, soros, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

class ProdutoEstoque(LojaIsolationMixin, models.Model):
    """Produto do estoque da clínica (botox, ácido hialurônico, soro, etc.)"""
    CATEGORIA_CHOICES = [
        ('injetavel', 'Injetável'),
        ('soroterapia', 'Soroterapia'),
        ('cosmético', 'Cosmético'),
        ('descartavel', 'Descartável'),
        ('equipamento', 'Equipamento'),
        ('outro', 'Outro'),
    ]

    nome = models.CharField(max_length=200, verbose_name="Nome do produto")
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default='outro', verbose_name="Categoria")
    marca = models.CharField(max_length=100, blank=True, default='', verbose_name="Marca/Fabricante")
    unidade_medida = models.CharField(max_length=30, default='unidade', verbose_name="Unidade de medida",
                                      help_text="Ex: unidade, ml, mg, ampola, frasco")
    quantidade_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Quantidade atual")
    quantidade_minima = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Estoque mínimo",
                                            help_text="Alerta quando atingir este valor")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Preço de custo (R$)")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Preço de venda (R$)")
    validade = models.DateField(null=True, blank=True, verbose_name="Data de validade")
    lote = models.CharField(max_length=50, blank=True, default='', verbose_name="Lote")
    observacoes = models.TextField(blank=True, default='', verbose_name="Observações")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Produto do estoque"
        verbose_name_plural = "Produtos do estoque"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.quantidade_atual} {self.unidade_medida})"

    @property
    def estoque_baixo(self):
        """Retorna True se estoque está abaixo do mínimo."""
        return self.quantidade_atual <= self.quantidade_minima


class MovimentacaoEstoque(LojaIsolationMixin, models.Model):
    """Registro de entrada/saída de produtos do estoque."""
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste de inventário'),
    ]

    produto = models.ForeignKey(ProdutoEstoque, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    motivo = models.CharField(max_length=200, blank=True, default='', verbose_name="Motivo/Observação")
    profissional = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="Profissional responsável")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Agendamento vinculado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da movimentação")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})"


class Consulta(LojaIsolationMixin, models.Model):
    """Consulta clínica — criada automaticamente ao mudar status do agendamento na agenda."""
    STATUS_CHOICES = (
        ('SCHEDULED', 'Agendada'),
        ('IN_PROGRESS', 'Em Atendimento'),
        ('COMPLETED', 'Concluída'),
        ('CANCELLED', 'Cancelada'),
    )

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='consulta',
        verbose_name='Agendamento',
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultas', verbose_name='Cliente')
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, null=True, related_name='consultas', verbose_name='Profissional',
    )
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, related_name='consultas', verbose_name='Procedimento')
    protocol = models.ForeignKey(
        ProcedureProtocol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Protocolo aplicado',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name='Status')
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name='Início')
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name='Fim')
    observacoes_gerais = models.TextField(blank=True, default='', verbose_name='Observações gerais')
    protocolo_notas = models.TextField(blank=True, default='', verbose_name='Notas do protocolo')
    valor_consulta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    local_atendimento = models.ForeignKey(
        'LocalAtendimento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Local de atendimento',
    )
    convenio = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Convênio',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_consultas'
        ordering = ['-data_inicio', '-created_at']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['loja_id', 'status']),
        ]

    def __str__(self):
        return f'Consulta {self.patient.nome} — {self.procedure.nome}'

    @property
    def duracao_minutos(self):
        if self.data_inicio and self.data_fim:
            return int((self.data_fim - self.data_inicio).total_seconds() / 60)
        return None


class PrescricaoMemed(LojaIsolationMixin, models.Model):
    """
    Prescrição emitida na Memed (receituário/exames), registrada no histórico do
    paciente a partir do evento `prescricaoImpressa` capturado no frontend.
    """
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescricoes_memed',
        verbose_name='Consulta',
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='prescricoes_memed', verbose_name='Cliente',
    )
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Profissional',
    )
    prescricao_id = models.CharField(
        max_length=64, blank=True, default='', verbose_name='ID na Memed',
        help_text='Identificador da prescrição retornado pela Memed.',
    )
    resumo = models.TextField(
        blank=True, default='', verbose_name='Resumo',
        help_text='Lista legível dos itens prescritos (medicamentos/exames).',
    )
    itens = models.JSONField(
        default=list, blank=True, verbose_name='Itens',
        help_text='Itens estruturados da prescrição (nome, posologia, tipo, receituário).',
    )
    pdf_url = models.URLField(
        max_length=500, blank=True, default='', verbose_name='URL do PDF',
        help_text='Link para o PDF da prescrição gerado pela Memed.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_prescricoes_memed'
        ordering = ['-created_at']
        verbose_name = 'Prescrição Memed'
        verbose_name_plural = 'Prescrições Memed'

    def __str__(self):
        return f'Prescrição {self.patient.nome} — {self.created_at:%d/%m/%Y %H:%M}'


class PatientAnamnese(LojaIsolationMixin, models.Model):
    """Anamnese do cliente — histórico clínico persistente."""
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name='anamnese',
        verbose_name='Cliente',
    )
    queixa_principal = models.TextField(blank=True, default='')
    historico_medico = models.TextField(blank=True, default='')
    medicamentos_uso = models.TextField(blank=True, default='')
    alergias = models.TextField(blank=True, default='')
    condicoes_clinicas = models.TextField(blank=True, default='')
    tipo_pele = models.CharField(max_length=100, blank=True, default='')
    pressao_arterial = models.CharField(max_length=20, blank=True, default='')
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    observacoes = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_anamneses'
        verbose_name = 'Anamnese do cliente'
        verbose_name_plural = 'Anamneses dos clientes'

    def __str__(self):
        return f'Anamnese — {self.patient.nome}'


class ConsultaEvolucao(LojaIsolationMixin, models.Model):
    """Evolução registrada durante ou após a consulta."""
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='evolucoes',
        verbose_name='Consulta',
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='evolucoes', verbose_name='Cliente')
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Profissional',
    )
    descricao = models.TextField(blank=True, default='', verbose_name='Evolução')
    procedimento_realizado = models.TextField(blank=True, default='')
    produtos_utilizados = models.TextField(blank=True, default='')
    orientacoes = models.TextField(blank=True, default='')
    protocolo_snapshot = models.TextField(blank=True, default='', help_text='Texto do protocolo aplicado')
    satisfacao = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_consulta_evolucoes'
        ordering = ['-created_at']
        verbose_name = 'Evolução da consulta'
        verbose_name_plural = 'Evoluções das consultas'

    def __str__(self):
        return f'Evolução {self.patient.nome} — {self.created_at:%d/%m/%Y %H:%M}'


class MemedTimbrado(LojaIsolationMixin, models.Model):
    """
    PDF timbrado A4 da clínica (cabeçalho/rodapé) para receituário e exames na Memed.
    Um arquivo por loja; aplicado a cada prescritor via API da Memed ao salvar/upload.
    """
    pdf = models.BinaryField(
        verbose_name='PDF timbrado',
        help_text='Arquivo PDF A4 com papel timbrado da clínica.',
    )
    pdf_nome = models.CharField(max_length=255, blank=True, default='', verbose_name='Nome do arquivo')
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_memed_timbrado'
        verbose_name = 'Timbrado Memed'
        verbose_name_plural = 'Timbrados Memed'

    def __str__(self):
        return self.pdf_nome or f'Timbrado loja {self.loja_id}'

# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTOS CLÍNICOS — Templates reutilizáveis e documentos gerados
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentTemplate(LojaIsolationMixin, models.Model):
    """Template reutilizável de documento clínico."""
    TIPO_CHOICES = [
        ('receituario', 'Receituário'),
        ('pedido_exame', 'Pedido de Exame'),
        ('atestado', 'Atestado'),
        ('documento_personalizado', 'Documento Personalizado'),
    ]
    professional = models.ForeignKey(
        'Professional', on_delete=models.CASCADE, related_name='document_templates',
        verbose_name='Profissional',
    )
    nome = models.CharField(max_length=200, verbose_name='Nome do template')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name='Tipo')
    conteudo = models.TextField(
        verbose_name='Conteúdo',
        help_text='Texto com placeholders: {{paciente_nome}}, {{data_atual}}, etc.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_document_templates'
        ordering = ['-updated_at']
        verbose_name = 'Template de documento'
        verbose_name_plural = 'Templates de documentos'

    def __str__(self):
        return f'{self.nome} ({self.get_tipo_display()})'


class DocumentoClinico(LojaIsolationMixin, models.Model):
    """Documento clínico gerado durante uma consulta."""
    TIPO_CHOICES = DocumentTemplate.TIPO_CHOICES

    consulta = models.ForeignKey(
        'Consulta', on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Consulta',
    )
    patient = models.ForeignKey(
        'Patient', on_delete=models.CASCADE, related_name='documentos_clinicos',
        verbose_name='Paciente',
    )
    professional = models.ForeignKey(
        'Professional', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documentos_emitidos', verbose_name='Profissional',
    )
    template = models.ForeignKey(
        'DocumentTemplate', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Template usado',
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name='Tipo')
    titulo = models.CharField(max_length=200, blank=True, default='', verbose_name='Título')
    conteudo = models.TextField(verbose_name='Conteúdo', help_text='Conteúdo final renderizado do documento.')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_documentos_clinicos'
        ordering = ['-created_at']
        verbose_name = 'Documento clínico'
        verbose_name_plural = 'Documentos clínicos'

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.patient.nome} ({self.created_at:%d/%m/%Y})'


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAIS DE ATENDIMENTO — Locais onde consultas são realizadas
# ═══════════════════════════════════════════════════════════════════════════════

class LocalAtendimento(LojaIsolationMixin, models.Model):
    """Local de atendimento com valor de consulta associado (ex: Consultório, Home Care, Telemedicina)."""
    nome = models.CharField(max_length=200, verbose_name="Nome do local")
    valor_consulta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da consulta (R$)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_locais_atendimento'
        ordering = ['nome']
        verbose_name = 'Local de atendimento'
        verbose_name_plural = 'Locais de atendimento'

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_consulta}"


# ═══════════════════════════════════════════════════════════════════════════════
# CONVÊNIOS — Tabelas de preço por plano
# ═══════════════════════════════════════════════════════════════════════════════

class Convenio(LojaIsolationMixin, models.Model):
    """Plano de saúde / convênio com tabela de preços por procedimento."""
    nome = models.CharField(max_length=200, verbose_name='Nome')
    codigo = models.CharField(max_length=50, blank=True, default='', verbose_name='Código')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_convenios'
        ordering = ['nome']
        verbose_name = 'Convênio'
        verbose_name_plural = 'Convênios'

    def __str__(self):
        return self.nome


class ConvenioProcedimentoPreco(LojaIsolationMixin, models.Model):
    """Preço de um procedimento para um convênio específico."""
    convenio = models.ForeignKey(
        Convenio,
        on_delete=models.CASCADE,
        related_name='precos_procedimentos',
        verbose_name='Convênio',
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='precos_convenio',
        verbose_name='Procedimento',
    )
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço (R$)')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_convenio_procedimento_precos'
        ordering = ['convenio', 'procedure__nome']
        verbose_name = 'Preço convênio × procedimento'
        verbose_name_plural = 'Preços convênio × procedimento'
        constraints = [
            models.UniqueConstraint(
                fields=['convenio', 'procedure', 'loja_id'],
                name='uniq_convenio_procedure_loja',
            ),
        ]

    def __str__(self):
        return f'{self.convenio.nome} — {self.procedure.nome}: R$ {self.preco}'
