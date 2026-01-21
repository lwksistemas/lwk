from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Cliente(models.Model):
    """Cliente da clínica de estética"""
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome


class Profissional(models.Model):
    """Profissional que realiza procedimentos"""
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100)
    registro_profissional = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_profissionais'
        ordering = ['nome']
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'

    def __str__(self):
        return f"{self.nome} - {self.especialidade}"


class Procedimento(models.Model):
    """Procedimentos oferecidos pela clínica"""
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    duracao = models.IntegerField(help_text='Duração em minutos')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_procedimentos'
        ordering = ['categoria', 'nome']
        verbose_name = 'Procedimento'
        verbose_name_plural = 'Procedimentos'

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class Agendamento(models.Model):
    """Agendamentos de procedimentos"""
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('confirmado', 'Confirmado'),
        ('em_atendimento', 'Em Atendimento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    profissional = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, related_name='agendamentos')
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE, related_name='agendamentos')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendado')
    observacoes = models.TextField(blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_agendamentos'
        ordering = ['data', 'horario']
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'

    def __str__(self):
        return f"{self.cliente.nome} - {self.procedimento.nome} - {self.data} {self.horario}"


class Funcionario(models.Model):
    """Funcionários da clínica (recepção, administração, etc)"""
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_funcionarios'
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return f"{self.nome} - {self.cargo}"


class ProtocoloProcedimento(models.Model):
    """Protocolos padronizados para procedimentos estéticos"""
    nome = models.CharField(max_length=200)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE, related_name='protocolos')
    descricao = models.TextField(help_text='Descrição detalhada do protocolo')
    
    # Etapas do protocolo
    preparacao = models.TextField(help_text='Preparação do cliente e ambiente')
    execucao = models.TextField(help_text='Passos de execução do procedimento')
    pos_procedimento = models.TextField(help_text='Cuidados pós-procedimento')
    
    # Informações técnicas
    tempo_estimado = models.IntegerField(help_text='Tempo estimado em minutos')
    materiais_necessarios = models.TextField(help_text='Lista de materiais necessários')
    contraindicacoes = models.TextField(blank=True, help_text='Contraindicações do procedimento')
    cuidados_especiais = models.TextField(blank=True, help_text='Cuidados especiais')
    
    # Configurações
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_protocolos'
        ordering = ['procedimento__nome', 'nome']
        verbose_name = 'Protocolo de Procedimento'
        verbose_name_plural = 'Protocolos de Procedimentos'

    def __str__(self):
        return f"{self.procedimento.nome} - {self.nome}"


class EvolucaoPaciente(models.Model):
    """Evolução e histórico do paciente"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='evolucoes')
    agendamento = models.ForeignKey(Agendamento, on_delete=models.CASCADE, related_name='evolucoes', null=True, blank=True)
    profissional = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True)
    
    # Data da evolução
    data_evolucao = models.DateTimeField(auto_now_add=True)
    
    # Avaliação inicial
    queixa_principal = models.TextField(help_text='Queixa principal do paciente')
    historico_medico = models.TextField(blank=True, help_text='Histórico médico relevante')
    medicamentos_uso = models.TextField(blank=True, help_text='Medicamentos em uso')
    alergias = models.TextField(blank=True, help_text='Alergias conhecidas')
    
    # Avaliação física
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Peso em kg')
    altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text='Altura em metros')
    pressao_arterial = models.CharField(max_length=20, blank=True, help_text='Ex: 120x80')
    
    # Avaliação estética
    tipo_pele = models.CharField(max_length=50, blank=True, help_text='Tipo de pele')
    condicoes_pele = models.TextField(blank=True, help_text='Condições observadas na pele')
    areas_tratamento = models.TextField(help_text='Áreas a serem tratadas')
    
    # Procedimento realizado
    procedimento_realizado = models.TextField(help_text='Descrição do procedimento realizado')
    produtos_utilizados = models.TextField(blank=True, help_text='Produtos utilizados')
    parametros_equipamento = models.TextField(blank=True, help_text='Parâmetros de equipamentos utilizados')
    
    # Resultados e observações
    reacao_imediata = models.TextField(blank=True, help_text='Reação imediata do paciente')
    orientacoes_dadas = models.TextField(blank=True, help_text='Orientações dadas ao paciente')
    proxima_sessao = models.DateField(null=True, blank=True, help_text='Data sugerida para próxima sessão')
    
    # Anexos
    fotos_antes = models.TextField(blank=True, help_text='URLs das fotos antes do procedimento')
    fotos_depois = models.TextField(blank=True, help_text='URLs das fotos depois do procedimento')
    
    # Avaliação de satisfação
    satisfacao_paciente = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Satisfação do paciente (1-5)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_evolucoes'
        ordering = ['-data_evolucao']
        verbose_name = 'Evolução do Paciente'
        verbose_name_plural = 'Evoluções dos Pacientes'

    def __str__(self):
        return f"{self.cliente.nome} - {self.data_evolucao.strftime('%d/%m/%Y %H:%M')}"

    @property
    def imc(self):
        """Calcula o IMC se peso e altura estiverem disponíveis"""
        if self.peso and self.altura:
            return round(float(self.peso) / (float(self.altura) ** 2), 2)
        return None


class AnamnesesTemplate(models.Model):
    """Templates de anamnese para diferentes tipos de procedimento"""
    nome = models.CharField(max_length=200)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE, related_name='anamneses_templates')
    
    # Perguntas da anamnese (JSON)
    perguntas = models.JSONField(
        default=list,
        help_text='Lista de perguntas para anamnese'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_anamneses_templates'
        ordering = ['procedimento__nome', 'nome']
        verbose_name = 'Template de Anamnese'
        verbose_name_plural = 'Templates de Anamnese'

    def __str__(self):
        return f"{self.procedimento.nome} - {self.nome}"


class Anamnese(models.Model):
    """Anamnese preenchida pelo paciente"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='anamneses')
    template = models.ForeignKey(AnamnesesTemplate, on_delete=models.CASCADE)
    agendamento = models.ForeignKey(Agendamento, on_delete=models.CASCADE, related_name='anamneses', null=True, blank=True)
    
    # Respostas da anamnese (JSON)
    respostas = models.JSONField(
        default=dict,
        help_text='Respostas do paciente às perguntas da anamnese'
    )
    
    # Assinatura digital
    assinatura_digital = models.TextField(blank=True, help_text='Assinatura digital do paciente')
    data_assinatura = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinica_anamneses'
        ordering = ['-created_at']
        verbose_name = 'Anamnese'
        verbose_name_plural = 'Anamneses'

    def __str__(self):
        return f"{self.cliente.nome} - {self.template.nome} - {self.created_at.strftime('%d/%m/%Y')}"


class HorarioFuncionamento(models.Model):
    """Horários de funcionamento da clínica"""
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    horario_abertura = models.TimeField()
    horario_fechamento = models.TimeField()
    intervalo_inicio = models.TimeField(null=True, blank=True, help_text='Início do intervalo de almoço')
    intervalo_fim = models.TimeField(null=True, blank=True, help_text='Fim do intervalo de almoço')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'clinica_horarios_funcionamento'
        ordering = ['dia_semana']
        verbose_name = 'Horário de Funcionamento'
        verbose_name_plural = 'Horários de Funcionamento'
        unique_together = ['dia_semana']

    def __str__(self):
        return f"{self.get_dia_semana_display()} - {self.horario_abertura} às {self.horario_fechamento}"


class BloqueioAgenda(models.Model):
    """Bloqueios na agenda (feriados, férias, etc)"""
    TIPO_BLOQUEIO = [
        ('feriado', 'Feriado'),
        ('ferias', 'Férias'),
        ('manutencao', 'Manutenção'),
        ('evento', 'Evento'),
        ('outros', 'Outros'),
    ]
    
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_BLOQUEIO)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    horario_inicio = models.TimeField(null=True, blank=True, help_text='Se não informado, bloqueia o dia todo')
    horario_fim = models.TimeField(null=True, blank=True)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, null=True, blank=True, help_text='Se não informado, bloqueia para todos')
    observacoes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clinica_bloqueios_agenda'
        ordering = ['data_inicio']
        verbose_name = 'Bloqueio de Agenda'
        verbose_name_plural = 'Bloqueios de Agenda'

    def __str__(self):
        return f"{self.titulo} - {self.data_inicio} a {self.data_fim}"
