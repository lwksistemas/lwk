"""Serializers de backup de lojas."""
from rest_framework import serializers

from ..models import ConfiguracaoBackup, HistoricoBackup


class ConfiguracaoBackupSerializer(serializers.ModelSerializer):
    """
    Serializer para ConfiguracaoBackup.
    
    Boas práticas:
    - Validação de dados no método validate()
    - Campos read-only apropriados
    - Campos display para choices
    """
    
    frequencia_display = serializers.CharField(source='get_frequencia_display', read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    
    class Meta:
        model = ConfiguracaoBackup
        fields = [
            'id',
            'loja',
            'loja_nome',
            'backup_automatico_ativo',
            'horario_envio',
            'frequencia',
            'frequencia_display',
            'dia_semana',
            'dia_semana_display',
            'dia_mes',
            'ultimo_backup',
            'ultimo_envio_email',
            'total_backups_realizados',
            'incluir_imagens',
            'manter_ultimos_n_backups',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'loja',
            'ultimo_backup',
            'ultimo_envio_email',
            'total_backups_realizados',
            'created_at',
            'updated_at',
        ]
    
    def validate(self, data):
        """Validações customizadas"""
        frequencia = data.get('frequencia')
        dia_semana = data.get('dia_semana')
        dia_mes = data.get('dia_mes')
        
        # Validar dia_semana para backup semanal
        if frequencia == 'semanal' and dia_semana is None:
            raise serializers.ValidationError({
                'dia_semana': 'Dia da semana é obrigatório para backup semanal'
            })
        
        # Validar dia_mes para backup mensal
        if frequencia == 'mensal':
            if dia_mes is None:
                raise serializers.ValidationError({
                    'dia_mes': 'Dia do mês é obrigatório para backup mensal'
                })
            if not (1 <= dia_mes <= 28):
                raise serializers.ValidationError({
                    'dia_mes': 'Dia do mês deve estar entre 1 e 28'
                })
        
        # Validar manter_ultimos_n_backups
        manter = data.get('manter_ultimos_n_backups')
        if manter is not None:
            if manter < 1:
                raise serializers.ValidationError({
                    'manter_ultimos_n_backups': 'Deve manter pelo menos 1 backup'
                })
            if manter > 30:
                raise serializers.ValidationError({
                    'manter_ultimos_n_backups': 'Não é recomendado manter mais de 30 backups'
                })
        
        return data


class HistoricoBackupSerializer(serializers.ModelSerializer):
    """
    Serializer para HistoricoBackup.
    
    Inclui campos calculados e formatados para facilitar uso no frontend.
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    loja_slug = serializers.CharField(source='loja.slug', read_only=True)
    solicitado_por_nome = serializers.SerializerMethodField()
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    tempo_formatado = serializers.CharField(source='get_tempo_processamento_formatado', read_only=True)
    
    class Meta:
        model = HistoricoBackup
        fields = [
            'id',
            'loja',
            'loja_nome',
            'loja_slug',
            'solicitado_por',
            'solicitado_por_nome',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'arquivo_nome',
            'arquivo_tamanho_mb',
            'tamanho_formatado',
            'arquivo_path',
            'total_registros',
            'tabelas_incluidas',
            'tempo_processamento_segundos',
            'tempo_formatado',
            'erro_mensagem',
            'email_enviado',
            'email_enviado_em',
            'email_destinatario',
            'created_at',
            'concluido_em',
        ]
        read_only_fields = [
            'id',
            'loja',
            'solicitado_por',
            'tipo',
            'status',
            'arquivo_nome',
            'arquivo_tamanho_mb',
            'arquivo_path',
            'total_registros',
            'tabelas_incluidas',
            'tempo_processamento_segundos',
            'erro_mensagem',
            'email_enviado',
            'email_enviado_em',
            'email_destinatario',
            'created_at',
            'concluido_em',
        ]
    
    def get_solicitado_por_nome(self, obj):
        """Retorna nome do usuário que solicitou"""
        if obj.solicitado_por:
            return obj.solicitado_por.get_full_name() or obj.solicitado_por.username
        return None


class HistoricoBackupListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de histórico.
    
    Retorna apenas campos essenciais para melhor performance.
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    
    class Meta:
        model = HistoricoBackup
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'arquivo_nome',
            'tamanho_formatado',
            'total_registros',
            'email_enviado',
            'created_at',
        ]
