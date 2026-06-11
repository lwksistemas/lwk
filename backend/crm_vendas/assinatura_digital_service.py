"""
Serviço de Assinatura Digital para Propostas e Contratos.
Gerencia workflow de assinatura: cliente → vendedor → concluído.
"""
from django.core.signing import dumps, loads, BadSignature
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from urllib.parse import quote, unquote
import logging

from core.assinatura_service import normalizar_token_url
from .assinatura_digital_emails import (
    enviar_email_assinatura_cliente,
    enviar_email_assinatura_vendedor,
    enviar_pdf_final,
)

logger = logging.getLogger(__name__)

# Configurações
TOKEN_EXPIRACAO_DIAS = 7  # Token válido por 7 dias

# Alias CRM — mesma lógica de core.assinatura_service (evita duplicar unquote em loop).
normalizar_token_assinatura_url = normalizar_token_url


def criar_token_assinatura(documento, tipo, loja_id):
    """
    Cria token de assinatura para cliente ou vendedor.
    
    Args:
        documento: instância de Proposta ou Contrato
        tipo: 'cliente' ou 'vendedor'
        loja_id: ID da loja
    
    Returns:
        AssinaturaDigital: instância criada
    """
    from .models import AssinaturaDigital
    
    # Obter dados do assinante
    if tipo == 'cliente':
        lead = documento.oportunidade.lead
        nome = lead.nome
        email = lead.email
    else:  # vendedor
        vendedor = documento.oportunidade.vendedor
        if vendedor:
            nome = vendedor.nome
            email = vendedor.email
        else:
            # Fallback: usar dados da loja (admin)
            from superadmin.models import Loja
            loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
            if loja and loja.owner:
                nome = loja.owner.get_full_name() or loja.owner.username
                email = loja.owner.email
            else:
                nome = 'Vendedor'
                email = ''
    
    # Gerar token único
    payload = {
        'doc_type': documento.__class__.__name__.lower(),
        'doc_id': documento.id,
        'tipo': tipo,
        'loja_id': loja_id,
        'exp': int((timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS)).timestamp()),
    }
    # Gerar token - Django já usa base64 URL-safe
    token = dumps(payload)
    logger.info(
        'Token de assinatura gerado: tipo=%s, documento=%s#%s, loja_id=%s, tamanho=%s',
        tipo,
        documento.__class__.__name__,
        documento.id,
        loja_id,
        len(token),
    )
    
    # Criar registro de assinatura
    # Determinar se é proposta ou contrato
    kwargs = {
        'tipo': tipo,
        'nome_assinante': nome,
        'email_assinante': email,
        'token': token,
        'token_expira_em': timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS),
        'loja_id': loja_id,
        'ip_address': '0.0.0.0',  # Será atualizado ao assinar
    }
    
    if documento.__class__.__name__ == 'Proposta':
        kwargs['proposta'] = documento
    else:
        kwargs['contrato'] = documento
    
    assinatura = AssinaturaDigital.objects.create(**kwargs)
    
    logger.info(
        f'✅ Token de assinatura criado e salvo no banco: '
        f'tipo={tipo}, documento={documento.__class__.__name__}#{documento.id}, '
        f'assinante={nome}, loja_id={loja_id}, assinatura_id={assinatura.id}'
    )
    
    return assinatura



def verificar_token_assinatura(token, loja_id=None):
    """
    Verifica e retorna AssinaturaDigital se token válido.
    
    Args:
        token: string do token (pode estar URL encoded ou não)
        loja_id: ID da loja (opcional, será extraído do token se não fornecido)
    
    Returns:
        tuple: (AssinaturaDigital ou None, mensagem_erro ou None, loja_id extraído)
    """
    from .models import AssinaturaDigital

    token = normalizar_token_assinatura_url(token)
    if not token:
        return None, 'Link de assinatura inválido.', loja_id
    
    logger.info('Verificando token de assinatura: tamanho=%s, loja_id=%s', len(token), loja_id)
    
    # Se loja_id não foi fornecido, extrair do token
    if loja_id is None:
        try:
            # Decodificar token para extrair loja_id
            payload = loads(token)
            loja_id = payload.get('loja_id')
            logger.info(
                'Payload de assinatura decodificado: loja_id=%s, doc_type=%s, doc_id=%s',
                loja_id,
                payload.get('doc_type'),
                payload.get('doc_id'),
            )
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return None, 'Link de assinatura inválido.', None
    
    try:
        # Tentar buscar com o token como está (pode estar URL encoded)
        try:
            logger.info(f'Tentando buscar token direto no banco (loja_id={loja_id})...')
            assinatura = AssinaturaDigital.objects.select_related('proposta', 'contrato').get(token=token)
            logger.info(f'✅ Token encontrado direto - ID: {assinatura.id}')
        except AssinaturaDigital.DoesNotExist:
            # Se não encontrar, tentar com URL decode (para tokens antigos que foram salvos encoded)
            token_decoded = unquote(token)
            logger.info('Token não encontrado direto. Tentando decode: tamanho=%s', len(token_decoded))
            if token_decoded != token:  # Só tenta se realmente decodificou algo
                assinatura = AssinaturaDigital.objects.select_related('proposta', 'contrato').get(token=token_decoded)
                logger.info(f'✅ Token encontrado após decode - ID: {assinatura.id}')
            else:
                logger.warning(f'❌ Token não mudou após decode')
                raise AssinaturaDigital.DoesNotExist
        
        # Verificar se já foi assinado
        if assinatura.assinado:
            logger.warning(f'⚠️ Documento já foi assinado - Assinatura ID: {assinatura.id}')
            return None, 'Este documento já foi assinado.', loja_id
        
        # Verificar expiração
        if assinatura.is_expirado():
            logger.warning(f'⚠️ Token expirado - Assinatura ID: {assinatura.id}')
            return None, 'Este link de assinatura expirou.', loja_id
        
        logger.info(f'✅ Token válido e ativo - Assinatura ID: {assinatura.id}')
        return assinatura, None, loja_id
    except AssinaturaDigital.DoesNotExist:
        logger.error(f'❌ Token não encontrado no banco de dados (loja_id={loja_id})')
        return None, 'Link de assinatura inválido.', loja_id


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
        logger.info(
            'Oportunidade %s fechada como ganha automaticamente (assinatura concluída do documento %s)',
            oportunidade.id, documento.id,
        )
    except Exception as e:
        logger.warning('Erro ao fechar oportunidade como ganha: %s', e)


def _notificar_assinatura_concluida(documento, assinatura):
    """Cria notificação in-app quando assinatura digital é concluída."""
    try:
        from notificacoes.models import Notification
        from superadmin.models import Loja
        loja_id = getattr(documento, 'loja_id', None)
        if not loja_id:
            return
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if not loja or not loja.owner_id:
            return
        tipo_doc = documento.__class__.__name__
        titulo_doc = getattr(documento, 'titulo', '') or f'{tipo_doc} #{documento.id}'
        Notification.objects.using('default').create(
            user_id=loja.owner_id,
            titulo=f'✅ {tipo_doc} assinada digitalmente',
            mensagem=f'{titulo_doc} foi assinada por ambas as partes.',
            tipo='sistema',
            canal='in_app',
            status='pendente',
            metadata={'tipo_documento': tipo_doc.lower(), 'documento_id': documento.id, 'loja_id': loja_id},
        )
    except Exception as e:
        logger.warning(f'Erro ao criar notificação de assinatura: {e}')


def _notificar_cliente_assinou(documento, assinatura):
    """Cria notificação in-app quando o cliente assina e o vendedor precisa assinar."""
    try:
        from notificacoes.models import Notification
        from superadmin.models import Loja
        loja_id = getattr(documento, 'loja_id', None)
        if not loja_id:
            return
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if not loja or not loja.owner_id:
            return
        tipo_doc = documento.__class__.__name__
        titulo_doc = getattr(documento, 'titulo', '') or f'{tipo_doc} #{documento.id}'
        cliente_nome = assinatura.nome_assinante or 'Cliente'
        canal_v = (getattr(documento, 'canal_assinatura_vendedor', None) or 'email').strip().lower()
        canal_txt = 'WhatsApp' if canal_v == 'whatsapp' else 'e-mail'
        Notification.objects.using('default').create(
            user_id=loja.owner_id,
            titulo=f'📝 {tipo_doc} aguardando sua assinatura',
            mensagem=f'{titulo_doc} foi assinada por {cliente_nome}. Verifique seu {canal_txt} para assinar.',
            tipo='sistema',
            canal='in_app',
            status='pendente',
            metadata={'tipo_documento': tipo_doc.lower(), 'documento_id': documento.id, 'loja_id': loja_id},
        )
    except Exception as e:
        logger.warning(f'Erro ao criar notificação de assinatura cliente: {e}')


def _telefone_vendedor_documento(documento) -> str:
    oportunidade = getattr(documento, 'oportunidade', None)
    vendedor = getattr(oportunidade, 'vendedor', None) if oportunidade else None
    return (getattr(vendedor, 'telefone', None) or '').strip()


def _email_vendedor_documento(documento) -> str:
    oportunidade = getattr(documento, 'oportunidade', None)
    vendedor = getattr(oportunidade, 'vendedor', None) if oportunidade else None
    return (getattr(vendedor, 'email', None) or '').strip()


def enviar_whatsapp_assinatura_vendedor(documento, assinatura, request, user=None):
    """
    Envia link de assinatura digital ao vendedor por WhatsApp.
    Returns: (sucesso, erro)
    """
    from whatsapp.models import WhatsAppConfig
    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.services import send_whatsapp

    telefone = _telefone_vendedor_documento(documento)
    if not telefone:
        return False, 'Vendedor não possui telefone cadastrado.'

    is_proposta = documento.__class__.__name__ == 'Proposta'
    config = WhatsAppConfig.objects.filter(loja_id=assinatura.loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(
        config,
        proposta=is_proposta,
        contrato=not is_proposta,
    )
    if not ok_cfg:
        return False, err_cfg

    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    tipo_doc = 'Proposta' if is_proposta else 'Contrato'
    titulo = (getattr(documento, 'titulo', None) or getattr(documento, 'numero', None) or tipo_doc).strip()
    nome_vendedor = (assinatura.nome_assinante or 'Vendedor').strip()

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    link = f'{frontend_url}/assinar/{quote(assinatura.token, safe="")}'
    mensagem = (
        f'Olá {nome_vendedor}!\n\n'
        f'O cliente já assinou a *{tipo_doc}*'
        f'{f" — {titulo}" if titulo else ""} '
        f'de *{loja_nome}*.\n\n'
        f'Finalize com sua assinatura pelo link:\n{link}\n\n'
        f'Link válido por {TOKEN_EXPIRACAO_DIAS} dias.'
    )

    ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    if ok:
        logger.info(
            'WhatsApp assinatura vendedor CRM: %s#%s vendedor=%s',
            documento.__class__.__name__,
            documento.id,
            nome_vendedor,
        )
    return ok, err


def enviar_link_assinatura_vendedor(documento, assinatura, request, canal='email', user=None):
    """Envia link de assinatura ao vendedor por e-mail ou WhatsApp."""
    canal = (canal or 'email').strip().lower()
    if canal == 'whatsapp':
        return enviar_whatsapp_assinatura_vendedor(documento, assinatura, request, user=user)
    if not (assinatura.email_assinante or '').strip() and not _email_vendedor_documento(documento):
        return False, 'Vendedor não possui e-mail cadastrado.'
    return enviar_email_assinatura_vendedor(documento, assinatura, request)


def notificar_vendedor_apos_assinatura_cliente(documento, loja_id, request):
    """Cria token do vendedor e envia pelo canal escolhido na proposta/contrato."""
    canal = (getattr(documento, 'canal_assinatura_vendedor', None) or 'email').strip().lower()
    if canal not in ('email', 'whatsapp'):
        canal = 'email'

    assinatura_vendedor = criar_token_assinatura(documento, 'vendedor', loja_id)
    ok, err = enviar_link_assinatura_vendedor(
        documento,
        assinatura_vendedor,
        request,
        canal=canal,
        user=getattr(request, 'user', None),
    )
    if ok:
        logger.info(
            'Link vendedor enviado (%s): documento=%s#%s',
            canal,
            documento.__class__.__name__,
            documento.id,
        )
        return True, None

    assinatura_vendedor.delete()
    return False, err or f'Erro ao enviar link ao vendedor por {canal}.'


def enviar_whatsapp_assinatura_cliente(documento, assinatura, request, user=None):
    """
    Envia link de assinatura digital ao cliente por WhatsApp.
    Returns: (sucesso, erro)
    """
    from urllib.parse import quote
    from whatsapp.models import WhatsAppConfig
    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.services import send_whatsapp

    lead = documento.oportunidade.lead
    telefone = (getattr(lead, 'telefone', None) or '').strip()
    if not telefone:
        return False, 'Lead não possui telefone cadastrado.'

    is_proposta = documento.__class__.__name__ == 'Proposta'
    config = WhatsAppConfig.objects.filter(loja_id=assinatura.loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(
        config,
        proposta=is_proposta,
        contrato=not is_proposta,
    )
    if not ok_cfg:
        return False, err_cfg

    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    tipo_doc = 'Proposta' if is_proposta else 'Contrato'
    titulo = (getattr(documento, 'titulo', None) or getattr(documento, 'numero', None) or tipo_doc).strip()

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    link = f'{frontend_url}/assinar/{quote(assinatura.token, safe="")}'
    mensagem = (
        f'Olá {lead.nome}!\n\n'
        f'Você recebeu *{tipo_doc}*'
        f'{f" — {titulo}" if titulo else ""} '
        f'de *{loja_nome}* para assinatura digital.\n\n'
        f'Leia e assine pelo link:\n{link}\n\n'
        f'Link válido por {TOKEN_EXPIRACAO_DIAS} dias.'
    )

    ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    if ok:
        logger.info(
            'WhatsApp assinatura CRM enviado: %s#%s lead=%s',
            documento.__class__.__name__,
            documento.id,
            lead.nome,
        )
    return ok, err


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
        AssinaturaDigital.objects.filter(**filt).delete()
        assinatura = criar_token_assinatura(documento, 'cliente', loja_id)

        if canal == 'whatsapp':
            ok, err = enviar_whatsapp_assinatura_cliente(
                documento, assinatura, request, user=getattr(request, 'user', None),
            )
            if ok:
                dest = (lead.telefone or '').strip()
                return True, f'Novo link de assinatura enviado por WhatsApp para {dest}', None
        else:
            ok, err = enviar_email_assinatura_cliente(documento, assinatura, request)
            if ok:
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
        AssinaturaDigital.objects.filter(**filt).delete()
        assinatura = criar_token_assinatura(documento, 'vendedor', loja_id)
        ok, err = enviar_link_assinatura_vendedor(
            documento,
            assinatura,
            request,
            canal=canal,
            user=getattr(request, 'user', None),
        )
        if ok:
            canal_label = 'WhatsApp' if canal == 'whatsapp' else 'e-mail'
            return True, f'Novo link de assinatura enviado ao vendedor por {canal_label}.', None
        assinatura.delete()
        return False, None, err or 'Erro ao enviar link ao vendedor.'

    return False, None, (
        'Reenvio só é possível quando a assinatura está aguardando cliente ou vendedor.'
    )
