"""
Configuração e utilidades administrativas do Mercado Pago (camada de serviço).

Separa regras de negócio das views HTTP (Two Scoops / Clean Architecture leve).
"""
from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from django.http import HttpRequest
from django.urls import reverse

from ..models import MercadoPagoConfig


class MercadoPagoAdminService:
    """Leitura/atualização de config global MP e teste de conexão."""

    @staticmethod
    def serialize_config(config: MercadoPagoConfig, *, include_token_mask: bool = True) -> Dict[str, Any]:
        masked = ''
        if include_token_mask and config.access_token:
            tok = config.access_token
            masked = (tok[:8] + '...' + tok[-4:]) if len(tok) >= 12 else ('****' if tok else '')
        data: Dict[str, Any] = {
            'enabled': config.enabled,
            'use_for_boletos': config.use_for_boletos,
            'access_token_set': bool(config.access_token),
            'public_key': getattr(config, 'public_key', '') or '',
            'chave_pix_estatica': getattr(config, 'chave_pix_estatica', '') or '',
        }
        if include_token_mask:
            data['access_token_masked'] = masked
        return data

    @staticmethod
    def apply_patch(config: MercadoPagoConfig, data: Dict[str, Any]) -> None:
        if 'enabled' in data:
            config.enabled = bool(data['enabled'])
        if 'use_for_boletos' in data:
            config.use_for_boletos = bool(data['use_for_boletos'])
        if 'access_token' in data and data['access_token'] is not None:
            config.access_token = str(data['access_token']).strip()
        if 'public_key' in data and data['public_key'] is not None:
            config.public_key = str(data['public_key']).strip()[:80]
        if 'chave_pix_estatica' in data:
            config.chave_pix_estatica = str(data.get('chave_pix_estatica') or '').strip()[:120]

    @staticmethod
    def test_connection(config: MercadoPagoConfig) -> Tuple[Dict[str, Any], bool]:
        """Retorna (payload, success)."""
        if not config.access_token:
            return (
                {
                    'success': False,
                    'error': 'Access Token não configurado. Salve o token nas configurações antes de testar.',
                },
                False,
            )
        from ..mercadopago_service import MercadoPagoClient

        result = MercadoPagoClient(config.access_token).test_connection()
        ok = bool(result.get('success'))
        return result, ok

    @staticmethod
    def webhook_discovery_payload(request: HttpRequest) -> Dict[str, Any]:
        path = reverse('mercadopago-webhook')
        webhook_url = request.build_absolute_uri(path)
        return {
            'status': 'ok',
            'message': 'Endpoint do webhook Mercado Pago ativo.',
            'url': webhook_url,
            'test': (
                'Envie POST com JSON: {"type": "payment", "data": {"id": "<payment_id>"}}. '
                'Use o ID de um pagamento real (boleto) para testar a confirmação.'
            ),
        }

    @staticmethod
    def parse_webhook_body(request: HttpRequest) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        raw = getattr(request, 'data', None)
        if isinstance(raw, dict):
            body = raw
        elif request.body:
            try:
                body = json.loads(request.body.decode('utf-8'))
            except Exception:
                body = {}
        return body if isinstance(body, dict) else {}
