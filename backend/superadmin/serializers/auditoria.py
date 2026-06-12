"""Serializers de auditoria e segurança."""
from rest_framework import serializers

from ..models import HistoricoAcessoGlobal, ViolacaoSeguranca

class HistoricoAcessoGlobalSerializer(serializers.ModelSerializer):
    """
    Serializer para Histórico de Acesso Global
    
    Boas práticas:
    - Read-only fields para dados calculados
    - SerializerMethodField para dados relacionados
    - Campos otimizados (select_related já feito na ViewSet)
    """
    
    # Campos relacionados (otimizados)
    usuario_username = serializers.CharField(source='user.username', read_only=True)
    loja_tipo = serializers.CharField(source='loja.tipo_loja.nome', read_only=True)
    
    # Campos calculados
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)
    navegador = serializers.ReadOnlyField()
    sistema_operacional = serializers.ReadOnlyField()
    
    # Formatação de data
    data_hora = serializers.SerializerMethodField()
    
    class Meta:
        model = HistoricoAcessoGlobal
        fields = [
            'id',
            'user',
            'usuario_username',
            'usuario_email',
            'usuario_nome',
            'loja',
            'loja_nome',
            'loja_slug',
            'loja_tipo',
            'acao',
            'acao_display',
            'recurso',
            'recurso_id',
            'detalhes',
            'ip_address',
            'user_agent',
            'navegador',
            'sistema_operacional',
            'metodo_http',
            'url',
            'sucesso',
            'erro',
            'created_at',
            'data_hora',
        ]
        read_only_fields = ['created_at']
    
    def get_data_hora(self, obj):
        """Formata data e hora para exibição (timezone local)"""
        from django.utils import timezone
        # Converter de UTC para timezone local (America/Sao_Paulo)
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d/%m/%Y %H:%M:%S')


class HistoricoAcessoGlobalListSerializer(serializers.ModelSerializer):
    """
    Serializer otimizado para listagem (menos campos)
    
    Boas práticas:
    - Serializer separado para listagem (performance)
    - Apenas campos essenciais
    - Reduz payload da API
    """
    
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)
    navegador = serializers.ReadOnlyField()
    data_hora = serializers.SerializerMethodField()
    
    class Meta:
        model = HistoricoAcessoGlobal
        fields = [
            'id',
            'usuario_nome',
            'usuario_email',
            'loja_nome',
            'loja_slug',
            'acao',
            'acao_display',
            'recurso',
            'ip_address',
            'navegador',
            'sucesso',
            'created_at',
            'data_hora',
        ]
    
    def get_data_hora(self, obj):
        """Formata data e hora para exibição (timezone local)"""
        from django.utils import timezone
        # Converter de UTC para timezone local (America/Sao_Paulo)
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d/%m/%Y %H:%M:%S')



class ViolacaoSegurancaSerializer(serializers.ModelSerializer):
    """
    Serializer para Violações de Segurança
    
    Inclui campos calculados e relacionamentos para facilitar exibição no frontend.
    """
    
    # Campos calculados
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tipo_display_friendly = serializers.CharField(source='get_tipo_display_friendly', read_only=True)
    criticidade_display = serializers.CharField(source='get_criticidade_display', read_only=True)
    criticidade_color = serializers.CharField(source='get_criticidade_color', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Contadores
    logs_relacionados_count = serializers.SerializerMethodField()
    
    # Informações de resolução
    resolvido_por_nome = serializers.SerializerMethodField()
    
    # Data formatada
    data_hora = serializers.SerializerMethodField()
    data_resolucao_formatada = serializers.SerializerMethodField()
    
    class Meta:
        model = ViolacaoSeguranca
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'tipo_display_friendly',
            'criticidade',
            'criticidade_display',
            'criticidade_color',
            'status',
            'status_display',
            'user',
            'usuario_email',
            'usuario_nome',
            'loja',
            'loja_nome',
            'descricao',
            'detalhes_tecnicos',
            'ip_address',
            'logs_relacionados_count',
            'resolvido_por',
            'resolvido_por_nome',
            'resolvido_em',
            'data_resolucao_formatada',
            'notas',
            'notificado',
            'notificado_em',
            'created_at',
            'updated_at',
            'data_hora',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'notificado',
            'notificado_em',
        ]
    
    def get_logs_relacionados_count(self, obj):
        """Retorna quantidade de logs relacionados"""
        return obj.logs_relacionados.count()
    
    def get_resolvido_por_nome(self, obj):
        """Retorna nome do usuário que resolveu"""
        if obj.resolvido_por:
            return obj.resolvido_por.get_full_name() or obj.resolvido_por.username
        return None
    
    def get_data_hora(self, obj):
        """Formata data e hora para exibição (timezone local)"""
        from django.utils import timezone
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d/%m/%Y %H:%M:%S')
    
    def get_data_resolucao_formatada(self, obj):
        """Formata data de resolução para exibição"""
        if obj.resolvido_em:
            from django.utils import timezone
            local_time = timezone.localtime(obj.resolvido_em)
            return local_time.strftime('%d/%m/%Y %H:%M:%S')
        return None


class ViolacaoSegurancaListSerializer(serializers.ModelSerializer):
    """
    Serializer otimizado para listagem de violações (menos campos)
    
    Boas práticas:
    - Serializer separado para listagem (performance)
    - Apenas campos essenciais
    - Reduz payload da API
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    criticidade_display = serializers.CharField(source='get_criticidade_display', read_only=True)
    criticidade_color = serializers.CharField(source='get_criticidade_color', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    data_hora = serializers.SerializerMethodField()
    logs_relacionados_count = serializers.SerializerMethodField()
    resolvido_por_nome = serializers.SerializerMethodField()
    data_resolucao_formatada = serializers.SerializerMethodField()
    
    class Meta:
        model = ViolacaoSeguranca
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'criticidade',
            'criticidade_display',
            'criticidade_color',
            'status',
            'status_display',
            'usuario_nome',
            'usuario_email',
            'loja_nome',
            'descricao',
            'detalhes_tecnicos',
            'ip_address',
            'logs_relacionados_count',
            'resolvido_por_nome',
            'data_resolucao_formatada',
            'notas',
            'created_at',
            'data_hora',
        ]
    
    def get_logs_relacionados_count(self, obj):
        return obj.logs_relacionados.count()

    def get_resolvido_por_nome(self, obj):
        if obj.resolvido_por:
            return obj.resolvido_por.get_full_name() or obj.resolvido_por.username
        return None

    def get_data_resolucao_formatada(self, obj):
        if not obj.resolvido_em:
            return None
        from django.utils import timezone
        return timezone.localtime(obj.resolvido_em).strftime('%d/%m/%Y %H:%M:%S')

    def get_data_hora(self, obj):
        """Formata data e hora para exibição (timezone local)"""
        from django.utils import timezone
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d/%m/%Y %H:%M:%S')


