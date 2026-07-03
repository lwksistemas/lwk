"""Serializers de propostas e contratos."""
from rest_framework import serializers

from ..emitente_documento import limpar_emitente_se_vazio
from ..models import Contrato, ContratoTemplate, Proposta, PropostaTemplate

_EMITENTE_FIELDS = [
    'emitente_nome', 'emitente_endereco', 'emitente_cpf_cnpj',
    'emitente_responsavel', 'emitente_email',
]


def _conta_nome_do_documento(obj) -> str | None:
    """Empresa do cliente (conta/lead), não prestadora — proposta e contrato."""
    lead = getattr(obj.oportunidade, 'lead', None) if getattr(obj, 'oportunidade_id', None) else None
    if not lead:
        return None
    from core.cpf_utils import label_empresa_lead

    conta_nome = None
    if getattr(lead, 'conta_id', None):
        try:
            conta_nome = lead.conta.nome
        except Exception:
            pass
    return label_empresa_lead(
        lead.cpf_cnpj,
        empresa=getattr(lead, 'empresa', None),
        conta_nome=conta_nome,
    )


class PropostaSerializer(serializers.ModelSerializer):
    oportunidade_titulo = serializers.CharField(source='oportunidade.titulo', read_only=True)
    lead_nome = serializers.CharField(source='oportunidade.lead.nome', read_only=True)
    lead_email = serializers.CharField(source='oportunidade.lead.email', read_only=True)
    lead_telefone = serializers.CharField(source='oportunidade.lead.telefone', read_only=True)
    conta_nome = serializers.SerializerMethodField()
    vendedor_nome = serializers.CharField(source='oportunidade.vendedor.nome', read_only=True)
    vendedor_email = serializers.CharField(source='oportunidade.vendedor.email', read_only=True)
    vendedor_telefone = serializers.CharField(source='oportunidade.vendedor.telefone', read_only=True)
    valor_com_desconto = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Proposta
        fields = [
            'id', 'oportunidade', 'oportunidade_titulo', 'lead_nome', 'lead_email', 'lead_telefone',
            'conta_nome',
            'vendedor_nome', 'vendedor_email', 'vendedor_telefone', 'canal_assinatura_vendedor',
            'numero', 'titulo', 'conteudo', 'valor_total',
            'desconto_tipo', 'desconto_valor', 'valor_com_desconto',
            'status', 'status_assinatura', 'motivo_cancelamento',
            'data_envio', 'data_resposta', 'observacoes',
            'nome_vendedor_assinatura', 'nome_cliente_assinatura',
            *_EMITENTE_FIELDS,
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'numero']

    def get_conta_nome(self, obj):
        return _conta_nome_do_documento(obj)

    def validate(self, attrs):
        return limpar_emitente_se_vazio(attrs)

    def update(self, instance, validated_data):
        """Ao marcar como assinado manualmente, fecha oportunidade como ganha."""
        old_status_assinatura = instance.status_assinatura
        new_status_assinatura = validated_data.get('status_assinatura', old_status_assinatura)
        
        instance = super().update(instance, validated_data)
        
        # Se status_assinatura mudou para 'concluido', fechar oportunidade como ganha
        if old_status_assinatura != 'concluido' and new_status_assinatura == 'concluido':
            oportunidade = instance.oportunidade
            if oportunidade and oportunidade.etapa not in ('closed_won', 'closed_lost'):
                from django.utils import timezone
                oportunidade.etapa = 'closed_won'
                if not oportunidade.data_fechamento_ganho:
                    oportunidade.data_fechamento_ganho = timezone.now().date()
                # Atualizar valor da oportunidade para valor com desconto (valor real pago)
                valor_com_desconto = instance.valor_com_desconto
                if valor_com_desconto and valor_com_desconto != oportunidade.valor:
                    oportunidade.valor = valor_com_desconto
                oportunidade.save(update_fields=['etapa', 'data_fechamento_ganho', 'valor', 'updated_at'])
        
        return instance


class PropostaTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropostaTemplate
        fields = [
            'id', 'nome', 'conteudo', 'is_padrao', 'ativo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ContratoTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContratoTemplate
        fields = [
            'id', 'nome', 'conteudo', 'is_padrao', 'ativo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ContratoSerializer(serializers.ModelSerializer):
    oportunidade_titulo = serializers.CharField(source='oportunidade.titulo', read_only=True)
    lead_nome = serializers.CharField(source='oportunidade.lead.nome', read_only=True)
    lead_email = serializers.CharField(source='oportunidade.lead.email', read_only=True)
    lead_telefone = serializers.CharField(source='oportunidade.lead.telefone', read_only=True)
    conta_nome = serializers.SerializerMethodField()
    vendedor_nome = serializers.CharField(source='oportunidade.vendedor.nome', read_only=True)
    vendedor_email = serializers.CharField(source='oportunidade.vendedor.email', read_only=True)
    vendedor_telefone = serializers.CharField(source='oportunidade.vendedor.telefone', read_only=True)
    valor_com_desconto = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Contrato
        fields = [
            'id', 'oportunidade', 'oportunidade_titulo', 'lead_nome', 'lead_email', 'lead_telefone',
            'conta_nome',
            'vendedor_nome', 'vendedor_email', 'vendedor_telefone', 'canal_assinatura_vendedor',
            'numero', 'titulo', 'conteudo', 'valor_total',
            'desconto_tipo', 'desconto_valor', 'valor_com_desconto',
            'status', 'status_assinatura', 'motivo_cancelamento',
            'data_envio', 'data_assinatura', 'observacoes',
            'nome_vendedor_assinatura', 'nome_cliente_assinatura',
            *_EMITENTE_FIELDS,
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'numero']

    def get_conta_nome(self, obj):
        return _conta_nome_do_documento(obj)

    def validate(self, attrs):
        return limpar_emitente_se_vazio(attrs)

