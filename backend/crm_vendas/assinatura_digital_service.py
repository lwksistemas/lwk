"""
Serviço de Assinatura Digital para Propostas e Contratos.
Workflow: cliente → vendedor → concluído.
"""
import logging

from django.utils import timezone

from .assinatura_digital_emails import enviar_email_assinatura_cliente, enviar_pdf_final
from .assinatura_digital_notificacoes import (
    _email_vendedor_documento,
    _notificar_assinatura_concluida,
    _notificar_cliente_assinou,
    _telefone_vendedor_documento,
    enviar_whatsapp_assinatura_cliente,
    notificar_vendedor_apos_assinatura_cliente,
    tentar_enviar_link_vendedor,
)
from .assinatura_digital_token import (
    AVISO_LINK_ANTERIOR,
    MSG_LINK_SUBSTITUIDO,
    TOKEN_EXPIRACAO_DIAS,
    criar_token_assinatura,
    normalizar_token_assinatura_url,
    verificar_token_assinatura,
)

logger = logging.getLogger(__name__)

def registrar_assinatura(assinatura, ip_address, user_agent=''):
    """
    Registra a assinatura com IP e timestamp.
    Atualiza status do documento e inicia próximo passo do workflow.
    
    Args:
        assinatura: instância de AssinaturaDigital
        ip_address: IP do assinante
        user_agent: User agent do navegador
    
    Returns:
        str: próximo status ('aguardando_vendedor' ou 'concluido')
    """
    # Registrar assinatura
    assinatura.assinado = True
    assinatura.assinado_em = timezone.now()
    assinatura.ip_address = ip_address
    assinatura.user_agent = user_agent[:500]
    assinatura.save()
    
    documento = assinatura.documento
    
    logger.info(
        f'Assinatura registrada: tipo={assinatura.tipo}, documento={documento.__class__.__name__}#{documento.id}, '
        f'assinante={assinatura.nome_assinante}, ip={ip_address}'
    )
    
    if assinatura.tipo == 'cliente':
        # Cliente assinou: próximo passo é vendedor
        documento.status_assinatura = 'aguardando_vendedor'
        documento.save(update_fields=['status_assinatura', 'updated_at'])
        
        # Notificar que o cliente assinou e o vendedor precisa assinar
        _notificar_cliente_assinou(documento, assinatura)
        
        return 'aguardando_vendedor'
    else:
        # Vendedor assinou: documento concluído
        documento.status_assinatura = 'concluido'
        # Proposta: muda status automaticamente para pedido
        if documento.__class__.__name__ == 'Proposta':
            if documento.status in ('rascunho', 'enviada', 'aceita'):
                documento.status = 'pedido'
            documento.save(update_fields=['status_assinatura', 'status', 'updated_at'])
            # Fechar oportunidade como ganha automaticamente
            _fechar_oportunidade_como_ganha(documento)
        else:
            documento.save(update_fields=['status_assinatura', 'updated_at'])
            # Contrato assinado também fecha a oportunidade
            _fechar_oportunidade_como_ganha(documento)
        
        # Notificar o dono da loja que a assinatura foi concluída
        _notificar_assinatura_concluida(documento, assinatura)
        
        return 'concluido'


def _fechar_oportunidade_como_ganha(documento):
    """Marca a oportunidade vinculada como closed_won quando assinatura é concluída."""
    try:
        from django.utils import timezone
        oportunidade = getattr(documento, 'oportunidade', None)
        if not oportunidade:
            return
        if oportunidade.etapa == 'closed_won':
            return  # Já está fechada
        oportunidade.etapa = 'closed_won'
        if not oportunidade.data_fechamento_ganho:
            oportunidade.data_fechamento_ganho = timezone.now().date()
        # Atualizar valor da oportunidade para valor com desconto (valor real pago)
        valor_com_desconto = getattr(documento, 'valor_com_desconto', None)
        update_fields = ['etapa', 'data_fechamento_ganho', 'updated_at']
        if valor_com_desconto and valor_com_desconto != oportunidade.valor:
            oportunidade.valor = valor_com_desconto
            update_fields.append('valor')
        oportunidade.save(update_fields=update_fields)
        try:
            from .services_financeiro import sincronizar_receita_comissao_oportunidade
            sincronizar_receita_comissao_oportunidade(oportunidade)
        except Exception as sync_exc:
            logger.warning('Erro ao sincronizar receita comissão opp=%s: %s', oportunidade.id, sync_exc)
        logger.info(
            'Oportunidade %s fechada como ganha automaticamente (assinatura concluída do documento %s)',
            oportunidade.id, documento.id,
        )
    except Exception as e:
        logger.warning('Erro ao fechar oportunidade como ganha: %s', e)


def reenviar_link_assinatura_pendente(documento, loja_id, request, canal='email'):
    """
    Gera novo token e reenvia o e-mail quando o documento está em
    aguardando_cliente ou aguardando_vendedor. Remove assinaturas pendentes
    (não assinadas) do passo atual antes de criar um novo link.

    Returns:
        tuple: (sucesso: bool, mensagem_sucesso: str | None, erro: str | None)
    """
    from .models import AssinaturaDigital

    sa = documento.status_assinatura
    is_proposta = documento.__class__.__name__ == 'Proposta'
    fk_field = 'proposta' if is_proposta else 'contrato'

    if sa == 'aguardando_cliente':
        if not documento.oportunidade or not documento.oportunidade.lead:
            return False, None, 'Documento sem oportunidade ou lead vinculado.'
        lead = documento.oportunidade.lead
        canal = (canal or 'email').strip().lower()
        if canal not in ('email', 'whatsapp'):
            return False, None, 'Canal inválido. Use email ou whatsapp.'

        if canal == 'email' and not lead.email:
            return False, None, 'Lead não possui email cadastrado.'
        if canal == 'whatsapp' and not (getattr(lead, 'telefone', None) or '').strip():
            return False, None, 'Lead não possui telefone cadastrado.'

        filt = {fk_field: documento, 'tipo': 'cliente', 'assinado': False}
        assinatura = criar_token_assinatura(documento, 'cliente', loja_id)

        if canal == 'whatsapp':
            ok, err = enviar_whatsapp_assinatura_cliente(
                documento, assinatura, request, user=getattr(request, 'user', None),
            )
            if ok:
                AssinaturaDigital.objects.filter(**filt).exclude(pk=assinatura.pk).delete()
                dest = (lead.telefone or '').strip()
                return True, f'Novo link de assinatura enviado por WhatsApp para {dest}', None
        else:
            ok, err = enviar_email_assinatura_cliente(documento, assinatura, request)
            if ok:
                AssinaturaDigital.objects.filter(**filt).exclude(pk=assinatura.pk).delete()
                return True, f'Novo link de assinatura enviado para {lead.email}', None

        assinatura.delete()
        return False, None, err or 'Erro ao reenviar.'

    if sa == 'aguardando_vendedor':
        canal = (canal or getattr(documento, 'canal_assinatura_vendedor', None) or 'email').strip().lower()
        if canal not in ('email', 'whatsapp'):
            return False, None, 'Canal inválido. Use email ou whatsapp.'
        if canal == 'email' and not _email_vendedor_documento(documento):
            return False, None, 'Vendedor não possui e-mail cadastrado.'
        if canal == 'whatsapp' and not _telefone_vendedor_documento(documento):
            return False, None, 'Vendedor não possui telefone cadastrado.'

        documento.canal_assinatura_vendedor = canal
        documento.save(update_fields=['canal_assinatura_vendedor', 'updated_at'])

        filt = {fk_field: documento, 'tipo': 'vendedor', 'assinado': False}
        assinatura = criar_token_assinatura(documento, 'vendedor', loja_id)
        ok, canal_usado, err = tentar_enviar_link_vendedor(
            documento,
            assinatura,
            request,
            user=getattr(request, 'user', None),
        )
        if ok:
            AssinaturaDigital.objects.filter(**filt).exclude(pk=assinatura.pk).delete()
            canal_label = 'WhatsApp' if (canal_usado or canal) == 'whatsapp' else 'e-mail'
            return True, f'Novo link de assinatura enviado ao vendedor por {canal_label}.', None
        assinatura.delete()
        return False, None, err or 'Erro ao enviar link ao vendedor.'

    return False, None, (
        'Reenvio só é possível quando a assinatura está aguardando cliente ou vendedor.'
    )


# Re-exports (compatibilidade com imports existentes)
from .assinatura_digital_notificacoes import (  # noqa: E402,F401
    enviar_link_assinatura_vendedor,
    enviar_whatsapp_assinatura_vendedor,
)

__all__ = [
    # token
    'criar_token_assinatura',
    'normalizar_token_assinatura_url',
    'verificar_token_assinatura',
    'MSG_LINK_SUBSTITUIDO',
    'AVISO_LINK_ANTERIOR',
    'TOKEN_EXPIRACAO_DIAS',
    # workflow
    'registrar_assinatura',
    'reenviar_link_assinatura_pendente',
    # e-mail / PDF
    'enviar_email_assinatura_cliente',
    'enviar_pdf_final',
    # notificações
    '_telefone_vendedor_documento',
    'enviar_link_assinatura_vendedor',
    'enviar_whatsapp_assinatura_vendedor',
    'enviar_whatsapp_assinatura_cliente',
    'notificar_vendedor_apos_assinatura_cliente',
    'tentar_enviar_link_vendedor',
]
