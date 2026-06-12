"""Serializer de configuração CRM."""
from rest_framework import serializers

from ..models import CRMConfig

class CRMConfigSerializer(serializers.ModelSerializer):
    provedor_nf_display = serializers.CharField(source='get_provedor_nf_display', read_only=True)
    asaas_api_key_configured = serializers.SerializerMethodField()
    asaas_webhook_url = serializers.SerializerMethodField()
    asaas_webhook_token_configured = serializers.SerializerMethodField()
    asaas_webhook_token_masked = serializers.SerializerMethodField()
    asaas_webhook_token_length = serializers.SerializerMethodField()
    issnet_senhas_salvas = serializers.SerializerMethodField()
    issnet_certificado = serializers.SerializerMethodField()

    def get_asaas_api_key_configured(self, obj):
        return bool((getattr(obj, 'asaas_api_key', None) or '').strip())

    def get_asaas_webhook_url(self, obj):
        loja = self.context.get('loja')
        if not loja:
            return ''
        slug = (getattr(loja, 'atalho', None) or loja.slug or '').strip()
        if not slug:
            return ''
        request = self.context.get('request')
        base = ''
        if request:
            base = request.build_absolute_uri('/').rstrip('/')
        if not base:
            from django.conf import settings
            base = (getattr(settings, 'API_BASE_URL', None) or 'https://api.lwksistemas.com.br').rstrip('/')
        return f'{base}/api/crm-vendas/webhooks/asaas/{slug}/'

    def get_asaas_webhook_token_configured(self, obj):
        loja = self.context.get('loja')
        if loja:
            from .models_config import CRMConfig
            return bool(CRMConfig.resolve_asaas_webhook_token(loja.id))
        token = obj.asaas_webhook_token_decrypted() if hasattr(obj, 'asaas_webhook_token_decrypted') else ''
        return bool(token)

    def get_asaas_webhook_token_masked(self, obj):
        return getattr(obj, 'asaas_webhook_token_masked', '') or ''

    def get_asaas_webhook_token_length(self, obj):
        loja = self.context.get('loja')
        if loja:
            from .models_config import CRMConfig
            return len(CRMConfig.resolve_asaas_webhook_token(loja.id))
        return len(obj.asaas_webhook_token_decrypted()) if hasattr(obj, 'asaas_webhook_token_decrypted') else 0

    def get_issnet_senhas_salvas(self, obj):
        return bool(
            (getattr(obj, 'issnet_senha', None) or '').strip()
            and (getattr(obj, 'issnet_senha_certificado', None) or '').strip()
        )

    def get_issnet_certificado(self, obj):
        """Retorna nome do arquivo se certificado está salvo no banco."""
        nome = getattr(obj, 'issnet_certificado_nome', '') or ''
        has_data = bool(getattr(obj, 'issnet_certificado', None))
        return nome if has_data else ''

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()
        bool_fields = [
            'asaas_sandbox',
            'optante_simples_nacional',
            'incentivador_cultural',
            'emitir_nf_automaticamente',
            'issnet_ambiente_homologacao',
        ]
        for field in bool_fields:
            if hasattr(data, 'get') and data.get(field) is not None:
                v = data.get(field)
                if isinstance(v, str):
                    data[field] = v.lower() in ('true', '1', 'on', 'yes')
        # Remover issnet_certificado do data — tratado manualmente no update()
        if hasattr(data, 'pop'):
            data.pop('issnet_certificado', None)
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        """Trata upload do certificado .pfx e normalização da API Key Asaas."""
        api_key = validated_data.get('asaas_api_key')
        if api_key is not None:
            from asaas_integration.api_key_utils import (
                normalize_asaas_api_key,
                is_valid_asaas_api_key,
                asaas_key_is_sandbox,
            )
            raw = (api_key or '').strip()
            if not raw:
                validated_data['asaas_api_key'] = ''
            elif '...' in raw:
                validated_data.pop('asaas_api_key', None)
            else:
                norm = normalize_asaas_api_key(raw)
                if not is_valid_asaas_api_key(norm):
                    raise serializers.ValidationError({
                        'asaas_api_key': (
                            'Chave API inválida. Cole a chave completa do painel Asaas '
                            '($aact_prod_... produção ou $aact_hmlg_... sandbox).'
                        ),
                    })
                validated_data['asaas_api_key'] = norm
                if 'asaas_sandbox' not in validated_data:
                    validated_data['asaas_sandbox'] = asaas_key_is_sandbox(norm)

        webhook_token = validated_data.get('asaas_webhook_token')
        if webhook_token is not None:
            from core.encryption import encrypt_value
            raw = (webhook_token or '').strip()
            if not raw:
                validated_data['asaas_webhook_token'] = ''
            elif '...' in raw:
                validated_data.pop('asaas_webhook_token', None)
            else:
                if len(raw) < 32:
                    raise serializers.ValidationError({
                        'asaas_webhook_token': (
                            'Token do webhook deve ter pelo menos 32 caracteres (requisito Asaas).'
                        ),
                    })
                validated_data['asaas_webhook_token'] = encrypt_value(raw)

        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            cert_file = request.FILES.get('issnet_certificado')
            if cert_file:
                instance.issnet_certificado = cert_file.read()
                instance.issnet_certificado_nome = cert_file.name or 'certificado.pfx'
        return super().update(instance, validated_data)

    class Meta:
        model = CRMConfig
        fields = [
            'id', 'origens_leads', 'etapas_pipeline', 'colunas_leads',
            'modulos_ativos', 'proposta_conteudo_padrao',
            'provedor_nf', 'provedor_nf_display',
            'issnet_usuario', 'issnet_senha',
            'issnet_certificado', 'issnet_certificado_nome', 'issnet_senha_certificado',
            'inscricao_municipal', 'codigo_cnae',
            'optante_simples_nacional', 'regime_especial_tributacao',
            'incentivador_cultural', 'item_lista_servico', 'codigo_nbs',
            'issnet_serie_rps', 'issnet_ultimo_rps_conhecido', 'issnet_numero_lote',
            'issnet_ambiente_homologacao',
            'codigo_servico_municipal', 'descricao_servico_padrao',
            'aliquota_iss', 'emitir_nf_automaticamente',
            'asaas_api_key', 'asaas_sandbox', 'asaas_api_key_configured',
            'asaas_webhook_token', 'asaas_webhook_url',
            'asaas_webhook_token_configured', 'asaas_webhook_token_masked', 'asaas_webhook_token_length',
            'issnet_senhas_salvas',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'asaas_api_key_configured',
            'asaas_webhook_url', 'asaas_webhook_token_configured',
            'asaas_webhook_token_masked', 'asaas_webhook_token_length',
            'issnet_senhas_salvas', 'issnet_certificado',
        ]
        extra_kwargs = {
            'issnet_senha': {'write_only': True},
            'issnet_senha_certificado': {'write_only': True},
            'asaas_api_key': {'write_only': True, 'required': False, 'allow_blank': True},
            'asaas_webhook_token': {'write_only': True, 'required': False, 'allow_blank': True},
        }
