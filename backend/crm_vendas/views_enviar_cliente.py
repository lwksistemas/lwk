"""
Views para enviar proposta/contrato ao cliente por email ou WhatsApp.
"""
import time
from django.conf import settings
from django.core.signing import dumps, loads, BadSignature
from django.http import HttpResponse
from django.views import View
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
import logging

from tenants.middleware import set_current_loja_id, set_current_tenant_db, get_current_loja_id
from .models import Proposta, Contrato
from .pdf_proposta_contrato import gerar_pdf_proposta, gerar_pdf_contrato

logger = logging.getLogger(__name__)

TOKEN_MAX_AGE = 3600  # 1 hora


def _criar_token(tipo: str, doc_id: int, loja_id: int) -> str:
    """Cria token assinado para download de documento."""
    payload = {
        'tipo': tipo,
        'id': doc_id,
        'loja_id': loja_id,
        'exp': int(time.time()) + TOKEN_MAX_AGE,
    }
    return dumps(payload)


def _verificar_token(token: str) -> dict | None:
    """Verifica e decodifica token. Retorna payload ou None."""
    try:
        payload = loads(token)
        if payload.get('exp', 0) < int(time.time()):
            return None
        return payload
    except (BadSignature, TypeError, ValueError):
        return None


class DocumentoPdfPublicView(View):
    """
    Endpoint público para download de PDF (usado pelo WhatsApp para baixar o documento).
    GET /api/crm-vendas/documento-pdf/?token=xxx
    """
    def get(self, request):
        token = request.GET.get('token')
        if not token:
            return HttpResponse('Token ausente', status=400)

        payload = _verificar_token(token)
        if not payload:
            return HttpResponse('Token inválido ou expirado', status=403)

        tipo = payload.get('tipo')
        doc_id = payload.get('id')
        loja_id = payload.get('loja_id')
        if not tipo or not doc_id or not loja_id:
            return HttpResponse('Token inválido', status=403)

        try:
            from superadmin.models import Loja
            import dj_database_url
            import os

            loja = Loja.objects.using('default').filter(id=loja_id).first()
            if not loja:
                return HttpResponse('Loja não encontrada', status=404)

            db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", "")}'
            schema_name = db_name.replace('-', '_') if db_name else 'default'
            set_current_loja_id(loja_id)

            from core.db_config import ensure_loja_database_config
            ensure_loja_database_config(db_name, conn_max_age=0)
            set_current_tenant_db(db_name if db_name in settings.DATABASES else 'default')

            if tipo == 'proposta':
                proposta = Proposta.objects.filter(id=doc_id, loja_id=loja_id).select_related(
                    'oportunidade', 'oportunidade__lead'
                ).prefetch_related('oportunidade__itens__produto_servico').first()
                if not proposta:
                    return HttpResponse('Proposta não encontrada', status=404)
                pdf_buffer = gerar_pdf_proposta(proposta)
                filename = f'proposta_{proposta.titulo or doc_id}.pdf'
            elif tipo == 'contrato':
                contrato = Contrato.objects.filter(id=doc_id, loja_id=loja_id).select_related(
                    'oportunidade', 'oportunidade__lead'
                ).prefetch_related('oportunidade__itens__produto_servico').first()
                if not contrato:
                    return HttpResponse('Contrato não encontrado', status=404)
                pdf_buffer = gerar_pdf_contrato(contrato)
                filename = f'contrato_{contrato.titulo or contrato.numero or doc_id}.pdf'
            else:
                return HttpResponse('Tipo inválido', status=400)

            pdf_buffer.seek(0)
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        except Exception as e:
            logger.exception('Erro ao gerar PDF para download: %s', e)
            return HttpResponse('Erro interno', status=500)


def _enviar_proposta_contrato_cliente(instance, canal: str, request) -> tuple[bool, str]:
    """
    Envia proposta ou contrato ao cliente por email ou WhatsApp.
    instance: Proposta ou Contrato
    canal: 'email' | 'whatsapp'
    Retorna (sucesso, mensagem_erro)
    """
    from django.core.mail import EmailMessage
    from whatsapp.services import send_whatsapp_document

    oportunidade = instance.oportunidade
    if not oportunidade or not oportunidade.lead_id:
        return False, 'Oportunidade ou lead não encontrado.'

    lead = oportunidade.lead
    loja_id = get_current_loja_id()
    if not loja_id:
        return False, 'Contexto de loja não definido.'

    is_proposta = isinstance(instance, Proposta)
    tipo = 'proposta' if is_proposta else 'contrato'
    titulo = (instance.titulo or instance.numero or tipo).replace(' ', '_')[:50]
    filename = f'{titulo}.pdf'

    pdf_buffer = gerar_pdf_proposta(instance) if is_proposta else gerar_pdf_contrato(instance)
    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()

    if canal == 'email':
        email_dest = (lead.email or '').strip()
        if not email_dest:
            return False, 'Lead não possui e-mail cadastrado.'
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'
            assunto = f'{tipo.capitalize()}: {instance.titulo or instance.numero or "Documento"}'
            corpo = f'Prezado(a) {lead.nome},\n\nSegue em anexo o documento solicitado.\n\nAtenciosamente.'
            email = EmailMessage(
                subject=assunto,
                body=corpo,
                from_email=from_email,
                to=[email_dest],
            )
            email.attach(filename, pdf_bytes, 'application/pdf')
            email.send(fail_silently=False)
            return True, None
        except Exception as e:
            logger.exception('Erro ao enviar email: %s', e)
            return False, str(e)

    elif canal == 'whatsapp':
        telefone = (lead.telefone or '').strip()
        if not telefone:
            return False, 'Lead não possui telefone cadastrado.'

        try:
            from whatsapp.models import WhatsAppConfig
            config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
            token_str = _criar_token(tipo, instance.id, loja_id)
            base_url = request.build_absolute_uri('/').rstrip('/')
            doc_url = f'{base_url}api/crm-vendas/documento-pdf/?token={token_str}'
            caption = f'Olá {lead.nome}! Segue o documento solicitado.'
            ok, err = send_whatsapp_document(
                telefone=telefone,
                document_url=doc_url,
                filename=filename,
                caption=caption,
                user=request.user,
                config=config,
            )
            return ok, err or ''
        except Exception as e:
            logger.exception('Erro ao enviar WhatsApp: %s', e)
            return False, str(e)

    return False, 'Canal inválido.'


