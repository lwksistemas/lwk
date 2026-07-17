"""Modelos Super Admin."""

from datetime import time

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .loja import Loja

# Madrugada BRT: 20 slots de 15 min (00:00–04:45) distribuídos por loja_id.
BACKUP_SLOT_NOTURNO_INICIO_MIN = 0  # 00:00
BACKUP_SLOT_NOTURNO_QTD = 20
BACKUP_SLOT_NOTURNO_PASSO_MIN = 15


def horario_envio_slot_noturno(loja_id: int) -> time:
    """Deriva horário noturno estável a partir do id da loja (America/Sao_Paulo)."""
    slot = int(loja_id or 0) % BACKUP_SLOT_NOTURNO_QTD
    total_min = BACKUP_SLOT_NOTURNO_INICIO_MIN + slot * BACKUP_SLOT_NOTURNO_PASSO_MIN
    return time(hour=total_min // 60, minute=total_min % 60, second=0)


class ConfiguracaoBackup(models.Model):
    """Configuração de backup automático para cada loja.

    Responsabilidades:
    - Armazenar configurações de agendamento de backup
    - Controlar frequência e horário de envio
    - Manter histórico de execuções

    Boas práticas aplicadas:
    - Single Responsibility: Apenas configuração de backup
    - Validação de dados no método clean()
    - Choices bem definidos para campos de seleção
    """

    # Choices
    FREQUENCIA_CHOICES = [
        ("diario", "Diário"),
        ("semanal", "Semanal"),
        ("mensal", "Mensal"),
    ]

    DIA_SEMANA_CHOICES = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    # Relacionamento
    loja = models.OneToOneField(
        Loja,
        on_delete=models.CASCADE,
        related_name="config_backup",
        help_text="Loja associada a esta configuração",
    )

    # Configuração de agendamento
    backup_automatico_ativo = models.BooleanField(
        default=False,
        help_text="Ativa ou desativa o backup automático",
    )
    horario_envio = models.TimeField(
        default=time(0, 0),
        help_text="Slot noturno (00:00–04:45 BRT) atribuído pelo sistema por loja",
    )
    frequencia = models.CharField(
        max_length=20,
        choices=FREQUENCIA_CHOICES,
        default="semanal",
        help_text="Frequência de execução do backup automático",
    )
    dia_semana = models.IntegerField(
        null=True,
        blank=True,
        choices=DIA_SEMANA_CHOICES,
        help_text="Dia da semana para backup semanal (0=Segunda, 6=Domingo)",
    )
    dia_mes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Dia do mês para backup mensal (1-28)",
    )

    # Histórico de execuções
    ultimo_backup = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora do último backup realizado",
    )
    ultimo_envio_email = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora do último envio de email com backup",
    )
    total_backups_realizados = models.IntegerField(
        default=0,
        help_text="Contador total de backups realizados",
    )

    # Configurações adicionais
    incluir_imagens = models.BooleanField(
        default=False,
        help_text="Incluir imagens no backup (aumenta significativamente o tamanho)",
    )
    manter_ultimos_n_backups = models.IntegerField(
        default=5,
        help_text="Quantidade de backups a manter armazenados no servidor",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "superadmin_configuracao_backup"
        verbose_name = "Configuração de Backup"
        verbose_name_plural = "Configurações de Backup"
        indexes = [
            models.Index(fields=["backup_automatico_ativo", "horario_envio"], name="cfg_backup_ativo_idx"),
            models.Index(fields=["ultimo_backup"], name="cfg_backup_ultimo_idx"),
        ]

    def __str__(self):
        status = "✅ Ativo" if self.backup_automatico_ativo else "❌ Inativo"
        return f"{status} - {self.loja.nome} - {self.get_frequencia_display()}"

    def clean(self):
        """Validações customizadas.

        Garante consistência dos dados de agendamento.
        """
        from django.core.exceptions import ValidationError

        # Validar dia_semana para backup semanal
        if self.frequencia == "semanal" and self.dia_semana is None:
            raise ValidationError({
                "dia_semana": "Dia da semana é obrigatório para backup semanal",
            })

        # Validar dia_mes para backup mensal
        if self.frequencia == "mensal":
            if self.dia_mes is None:
                raise ValidationError({
                    "dia_mes": "Dia do mês é obrigatório para backup mensal",
                })
            if not (1 <= self.dia_mes <= 28):
                raise ValidationError({
                    "dia_mes": "Dia do mês deve estar entre 1 e 28",
                })

        # Validar manter_ultimos_n_backups
        if self.manter_ultimos_n_backups < 1:
            raise ValidationError({
                "manter_ultimos_n_backups": "Deve manter pelo menos 1 backup",
            })
        if self.manter_ultimos_n_backups > 30:
            raise ValidationError({
                "manter_ultimos_n_backups": "Não é recomendado manter mais de 30 backups",
            })

    def save(self, *args, **kwargs):
        """Força slot noturno distribuído e valida antes de salvar."""
        loja_id = self.loja_id or getattr(self.loja, "id", None)
        if loja_id:
            self.horario_envio = horario_envio_slot_noturno(loja_id)
        self.full_clean()
        super().save(*args, **kwargs)

    def deve_executar_backup_hoje(self):
        """Verifica se o backup deve ser executado hoje (data local conforme TIME_ZONE).

        Returns:
            bool: True se deve executar, False caso contrário

        """
        if not self.backup_automatico_ativo:
            return False

        now_local = timezone.localtime(timezone.now())

        if self.frequencia == "diario":
            return True

        if self.frequencia == "semanal":
            return now_local.weekday() == self.dia_semana

        if self.frequencia == "mensal":
            return now_local.day == self.dia_mes

        return False

    def incrementar_contador(self):
        """Incrementa o contador de backups realizados"""
        self.total_backups_realizados += 1
        self.ultimo_backup = timezone.now()
        self.save(update_fields=["total_backups_realizados", "ultimo_backup"])


class HistoricoBackup(models.Model):
    """Histórico de backups realizados.

    Responsabilidades:
    - Registrar cada backup executado
    - Armazenar metadados e estatísticas
    - Controlar status e erros

    Boas práticas aplicadas:
    - Auditoria completa de operações
    - Separação de concerns (status, email, arquivo)
    - Índices otimizados para queries comuns
    """

    # Choices
    TIPO_CHOICES = [
        ("manual", "Manual"),
        ("automatico", "Automático"),
    ]

    STATUS_CHOICES = [
        ("processando", "Processando"),
        ("concluido", "Concluído"),
        ("erro", "Erro"),
    ]

    # Relacionamentos
    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name="historico_backups",
        help_text="Loja que teve backup realizado",
    )
    solicitado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="backups_solicitados",
        help_text="Usuário que solicitou o backup (para backups manuais)",
    )

    # Tipo e status
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        db_index=True,
        help_text="Tipo de backup: manual ou automático",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="processando",
        db_index=True,
        help_text="Status atual do processamento do backup",
    )

    # Informações do arquivo
    arquivo_nome = models.CharField(
        max_length=255,
        help_text="Nome do arquivo de backup gerado",
    )
    arquivo_tamanho_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Tamanho do arquivo em megabytes",
    )
    arquivo_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Caminho do arquivo no storage (S3, filesystem, etc)",
    )

    # Estatísticas do backup
    total_registros = models.IntegerField(
        default=0,
        help_text="Total de registros incluídos no backup",
    )
    tabelas_incluidas = models.JSONField(
        default=dict,
        help_text="Dicionário com contagem de registros por tabela",
    )
    tempo_processamento_segundos = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tempo total de processamento em segundos",
    )

    # Controle de erros
    erro_mensagem = models.TextField(
        blank=True,
        help_text="Mensagem de erro detalhada (se houver)",
    )

    # Controle de email
    email_enviado = models.BooleanField(
        default=False,
        help_text="Indica se o backup foi enviado por email",
    )
    email_enviado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora do envio do email",
    )
    email_destinatario = models.EmailField(
        blank=True,
        help_text="Email do destinatário",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Data e hora de criação do registro",
    )
    concluido_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora de conclusão do backup",
    )

    class Meta:
        db_table = "superadmin_historico_backup"
        verbose_name = "Histórico de Backup"
        verbose_name_plural = "Histórico de Backups"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["loja", "-created_at"], name="hist_backup_loja_idx"),
            models.Index(fields=["status", "-created_at"], name="hist_backup_status_idx"),
            models.Index(fields=["tipo", "-created_at"], name="hist_backup_tipo_idx"),
            models.Index(fields=["email_enviado"], name="hist_backup_email_idx"),
        ]

    def __str__(self):
        status_emoji = {
            "processando": "⏳",
            "concluido": "✅",
            "erro": "❌",
        }
        emoji = status_emoji.get(self.status, "❓")
        return f"{emoji} {self.loja.nome} - {self.get_tipo_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def marcar_como_concluido(self, tamanho_mb: float, total_registros: int, tabelas: dict):
        """Marca o backup como concluído com sucesso.

        Args:
            tamanho_mb: Tamanho do arquivo em MB
            total_registros: Total de registros exportados
            tabelas: Dicionário com contagem por tabela

        """
        self.status = "concluido"
        self.arquivo_tamanho_mb = tamanho_mb
        self.total_registros = total_registros
        self.tabelas_incluidas = tabelas
        self.concluido_em = timezone.now()

        # Calcular tempo de processamento
        if self.created_at:
            delta = self.concluido_em - self.created_at
            self.tempo_processamento_segundos = int(delta.total_seconds())

        self.save()

    def marcar_como_erro(self, erro_mensagem: str):
        """Marca o backup como erro.

        Args:
            erro_mensagem: Mensagem de erro detalhada

        """
        self.status = "erro"
        self.erro_mensagem = erro_mensagem
        self.concluido_em = timezone.now()
        self.save()

    def marcar_email_enviado(self, destinatario: str):
        """Marca que o email foi enviado com sucesso.

        Args:
            destinatario: Email do destinatário

        """
        self.email_enviado = True
        self.email_enviado_em = timezone.now()
        self.email_destinatario = destinatario
        self.save(update_fields=["email_enviado", "email_enviado_em", "email_destinatario"])

    def get_tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado.

        Returns:
            str: Tamanho formatado (ex: "15.5 MB")

        """
        if self.arquivo_tamanho_mb < 1:
            return f"{self.arquivo_tamanho_mb * 1024:.1f} KB"
        return f"{self.arquivo_tamanho_mb:.2f} MB"

    def get_tempo_processamento_formatado(self):
        """Retorna o tempo de processamento formatado.

        Returns:
            str: Tempo formatado (ex: "2m 30s")

        """
        if not self.tempo_processamento_segundos:
            return "N/A"

        minutos = self.tempo_processamento_segundos // 60
        segundos = self.tempo_processamento_segundos % 60

        if minutos > 0:
            return f"{minutos}m {segundos}s"
        return f"{segundos}s"


