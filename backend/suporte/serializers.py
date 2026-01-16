from rest_framework import serializers
from .models import Chamado, RespostaChamado

class RespostaChamadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespostaChamado
        fields = ['id', 'chamado', 'usuario_nome', 'mensagem', 'is_suporte', 'created_at']
        read_only_fields = ['created_at']


class ChamadoSerializer(serializers.ModelSerializer):
    respostas = RespostaChamadoSerializer(many=True, read_only=True)
    atendente_nome = serializers.CharField(source='atendente.username', read_only=True)
    
    class Meta:
        model = Chamado
        fields = [
            'id', 'titulo', 'descricao', 'status', 'prioridade',
            'loja_slug', 'loja_nome', 'usuario_nome', 'usuario_email',
            'atendente', 'atendente_nome', 'respostas',
            'created_at', 'updated_at', 'resolvido_em'
        ]
        read_only_fields = ['created_at', 'updated_at']
