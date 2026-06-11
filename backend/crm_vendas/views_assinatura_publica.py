"""
Views públicas de assinatura digital (sem autenticação).
Extraído de views.py para melhor organização.
"""
import json
import logging
from functools import wraps

from django.views import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.conf import settings

from tenants.middleware import set_current_loja_id, set_current_tenant_db, get_current_loja_id

logger = logging.getLogger(__name__)


def _rate_limit(key_prefix, max_requests=10, window=60):
    """Rate limiting simples por IP. Bloqueia após max_requests em window segundos."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            cache_key = f'rate_limit:{key_prefix}:{ip}'
            count = cache.get(cache_key, 0)
            if count >= max_requests:
                return JsonResponse({'error': 'Muitas tentativas. Aguarde um momento.'}, status=429)
            cache.set(cache_key, count + 1, window)
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def _configurar_tenant_para_assinatura_publica(loja_id):
    """
    Garante search_path / banco do tenant antes de consultar AssinaturaDigital.
    Sem isso, o manager usa apenas 'default' e o token não é encontrado no schema da loja.
    Retorna None se OK, ou string de erro para o cliente.
    """
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from superadmin.models import Loja
    from core.db_config import ensure_loja_database_config

    set_current_loja_id(loja_id)
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        logger.error(f'[AssinaturaPublica] Loja id={loja_id} inexistente (token válido mas loja apagada?)')
        return 'Link de assinatura inválido.'

    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", "")}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        logger.error(f'[AssinaturaPublica] Falha ensure_loja_database_config para db_name={db_name!r}')
        return 'Serviço temporariamente indisponível. Tente novamente ou solicite um novo link de assinatura.'

    set_current_tenant_db(db_name)
    logger.info(f'✅ [AssinaturaPublica] tenant db={db_name} loja_id={loja_id}')
    return None


@method_decorator(csrf_exempt, name='dispatch')
class AssinaturaPublicaView(View):
    """
    View pública para assinatura digital de propostas e contratos.
    GET /api/crm-vendas/assinar/{token}/ - Retorna dados do documento
    POST /api/crm-vendas/assinar/{token}/ - Registra assinatura
    """

    def _calcular_valor_por_recorrencia(self, oportunidade, recorrencia_tipo):
        """Calcula soma dos itens por tipo de recorrência."""
        if not oportunidade:
            return 0
        try:
            itens = oportunidade.itens.select_related('produto_servico').all()
            total = sum(
                float(item.quantidade * item.preco_unitario)
                for item in itens
                if getattr(item.produto_servico, 'recorrencia', 'unico') == recorrencia_tipo
            )
            return round(total, 2)
        except Exception:
            return 0
    
    @_rate_limit('assinatura_get', max_requests=30, window=60)
    def get(self, request, token):
        """Retorna dados do documento para assinatura"""
        from .assinatura_digital_service import verificar_token_assinatura, normalizar_token_assinatura_url
        from django.core.signing import loads, BadSignature

        token = normalizar_token_assinatura_url(token)
        logger.info('Recebendo requisição de assinatura: token_tamanho=%s', len(token))

        # PASSO 1: Decodificar token para extrair loja_id
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
            logger.info(f'📦 Token decodificado - loja_id={loja_id}, doc_type={payload.get("doc_type")}, doc_id={payload.get("doc_id")}')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        if not loja_id:
            logger.error('❌ Token não contém loja_id')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        # PASSO 2: Configurar tenant (obrigatório — antes caía em default sem schema)
        cfg_err = _configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            status = 503 if 'indisponível' in cfg_err.lower() else 400
            return JsonResponse({'error': cfg_err}, status=status)

        # PASSO 3: Buscar token no banco (agora com contexto correto)
        assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
        
        if erro:
            logger.warning(f'❌ Erro ao verificar token: {erro}')
            return JsonResponse({'error': erro}, status=400)
        
        logger.info(f'✅ Token válido - Assinatura ID: {assinatura.id}, Loja ID: {assinatura.loja_id}')
        
        documento = assinatura.documento
        
        # Determinar tipo de documento
        tipo_documento = 'proposta' if assinatura.proposta else 'contrato'
        
        # Retornar dados do documento
        oportunidade = getattr(documento, 'oportunidade', None)
        lead = getattr(oportunidade, 'lead', None) if oportunidade else None
        vendedor = getattr(oportunidade, 'vendedor', None) if oportunidade else None

        return JsonResponse({
            'tipo_documento': tipo_documento,
            'titulo': documento.titulo,
            'valor_total': str(documento.valor_total or '0.00'),
            'valor_adesao': str(self._calcular_valor_por_recorrencia(oportunidade, 'unico')),
            'valor_mensal': str(self._calcular_valor_por_recorrencia(oportunidade, 'mensal')),
            'nome_assinante': assinatura.nome_assinante,
            'tipo_assinante': assinatura.tipo,
            'tipo_assinante_display': assinatura.get_tipo_display(),
            'lead_nome': getattr(lead, 'nome', '') or '',
            'lead_email': getattr(lead, 'email', '') or '',
            'lead_empresa': getattr(lead, 'empresa', '') or '',
            'vendedor_email': getattr(vendedor, 'email', '') or '',
        })
    
    @_rate_limit('assinatura_post', max_requests=5, window=60)
    def post(self, request, token):
        """Registra a assinatura"""
        from .assinatura_digital_service import (
            verificar_token_assinatura,
            registrar_assinatura,
            notificar_vendedor_apos_assinatura_cliente,
            enviar_pdf_final,
            normalizar_token_assinatura_url,
        )
        from django.core.signing import loads, BadSignature

        token = normalizar_token_assinatura_url(token)

        # PASSO 1: Decodificar token para extrair loja_id
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        if not loja_id:
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        cfg_err = _configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            status = 503 if 'indisponível' in cfg_err.lower() else 400
            return JsonResponse({'error': cfg_err}, status=status)

        # PASSO 3: Buscar token no banco (agora com contexto correto)
        assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
        
        if erro:
            return JsonResponse({'error': erro}, status=400)
        
        # Obter IP do cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Registrar assinatura
        proximo_status = registrar_assinatura(assinatura, ip_address, user_agent)
        
        documento = assinatura.documento
        
        # Se cliente assinou, criar token e enviar para vendedor
        if proximo_status == 'aguardando_vendedor':
            try:
                ok_v, err_v = notificar_vendedor_apos_assinatura_cliente(documento, loja_id, request)
                if ok_v:
                    logger.info(
                        'Cliente assinou, link enviado ao vendedor (%s): %s#%s',
                        getattr(documento, 'canal_assinatura_vendedor', 'email'),
                        documento.__class__.__name__,
                        documento.id,
                    )
                else:
                    logger.warning('Falha ao enviar link ao vendedor: %s', err_v)
            except Exception as e:
                logger.exception(f'Erro ao enviar link para vendedor: {e}')
                # Não falha a assinatura do cliente se envio ao vendedor falhar
        
        # Se vendedor assinou, enviar PDF final
        elif proximo_status == 'concluido':
            try:
                # Enviar PDF final de forma síncrona (rápido, não precisa de background)
                enviar_pdf_final(documento, loja_id)
                logger.info(
                    f'Vendedor assinou, PDF final enviado: '
                    f'documento={documento.__class__.__name__}#{documento.id}'
                )
            except Exception as e:
                logger.exception(f'Erro ao enviar PDF final: {e}')
                # Não falha a assinatura se envio do PDF falhar
        
        return JsonResponse({
            'success': True,
            'message': 'Documento assinado com sucesso!',
            'proximo_status': proximo_status,
            'proximo_status_display': documento.get_status_assinatura_display() if hasattr(documento, 'get_status_assinatura_display') else proximo_status
        })



@method_decorator(csrf_exempt, name='dispatch')
class AssinaturaPdfView(View):
    """
    View pública para visualizar/baixar PDF do documento antes de assinar.
    GET /api/crm-vendas/assinar/{token}/pdf/ - Retorna PDF do documento
    """
    
    @_rate_limit('assinatura_pdf', max_requests=20, window=60)
    def get(self, request, token):
        """Retorna PDF do documento para visualização"""
        from .assinatura_digital_service import verificar_token_assinatura, normalizar_token_assinatura_url
        from .pdf_proposta_contrato import gerar_pdf_proposta, gerar_pdf_contrato
        from django.http import HttpResponse
        from django.core.signing import loads, BadSignature

        token = normalizar_token_assinatura_url(token)
        logger.info('Requisição de PDF de assinatura: token_tamanho=%s', len(token))

        # PASSO 1: Decodificar token para extrair loja_id
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token para PDF: {e}')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        if not loja_id:
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        cfg_err = _configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            status = 503 if 'indisponível' in cfg_err.lower() else 400
            return JsonResponse({'error': cfg_err}, status=status)

        # PASSO 3: Buscar token no banco (agora com contexto correto)
        assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
        
        if erro:
            logger.warning(f'❌ Erro ao verificar token para PDF: {erro}')
            return JsonResponse({'error': erro}, status=400)
        
        documento = assinatura.documento
        
        try:
            # Gerar PDF sem assinaturas (documento ainda não foi assinado)
            if assinatura.proposta:
                pdf_buffer = gerar_pdf_proposta(documento, incluir_assinaturas=False)
                filename = f'proposta_{documento.titulo or documento.id}.pdf'
            else:
                pdf_buffer = gerar_pdf_contrato(documento, incluir_assinaturas=False)
                filename = f'contrato_{documento.titulo or documento.id}.pdf'
            
            pdf_buffer.seek(0)
            
            logger.info(f'✅ PDF gerado com sucesso: {filename}')
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
            
        except Exception as e:
            logger.exception(f'Erro ao gerar PDF: {e}')
            return JsonResponse({'error': 'Erro ao gerar PDF'}, status=500)
