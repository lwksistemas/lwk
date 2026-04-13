import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from core.serializer_mixins import TextNormalizationMixin

from .models import (
    Vendedor, Conta, Lead, Contato, Oportunidade, Atividade,
    ProdutoServico, CategoriaProdutoServico, OportunidadeItem, Proposta, Contrato, CRMConfig,
    PropostaTemplate, ContratoTemplate,
)

logger = logging.getLogger(__name__)


class VendedorSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    criar_acesso = serializers.BooleanField(write_only=True, default=False, required=False)
    tem_acesso = serializers.SerializerMethodField(read_only=True)
    grupo_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    grupo_nome = serializers.SerializerMethodField(read_only=True)
    
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'cargo']

    class Meta:
        model = Vendedor
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'comissao_padrao', 'is_admin', 'is_active',
            'criar_acesso', 'tem_acesso', 'grupo_id', 'grupo_nome',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_tem_acesso(self, obj):
        """✅ OTIMIZAÇÃO: Usa anotação do queryset para evitar N+1"""
        # Se tem anotação (vem do ViewSet otimizado), usa ela
        if hasattr(obj, 'tem_acesso_anotado'):
            return obj.tem_acesso_anotado
        
        # Fallback para casos sem anotação (detail view, etc)
        if not obj or not obj.email:
            return False
        from tenants.middleware import get_current_loja_id
        from superadmin.models import VendedorUsuario
        loja_id = get_current_loja_id()
        if not loja_id:
            return False
        return VendedorUsuario.objects.filter(
            loja_id=loja_id,
            vendedor_id=obj.id,
        ).exists()

    def get_grupo_nome(self, obj):
        """Retorna o nome do grupo do vendedor, se houver."""
        if not obj or not obj.email:
            return None
        from tenants.middleware import get_current_loja_id
        from superadmin.models import VendedorUsuario
        from django.contrib.auth.models import Group
        
        loja_id = get_current_loja_id()
        if not loja_id:
            return None
        
        try:
            vu = VendedorUsuario.objects.using('default').select_related('user').get(
                loja_id=loja_id,
                vendedor_id=obj.id,
            )
            # Pegar o primeiro grupo relacionado ao CRM
            grupo = vu.user.groups.filter(name__in=['Gerente de Vendas', 'Vendedor']).first()
            return grupo.name if grupo else None
        except VendedorUsuario.DoesNotExist:
            return None

    def create(self, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        grupo_id = validated_data.pop('grupo_id', None)
        vendedor = super().create(validated_data)
        if criar_acesso and vendedor.email:
            try:
                self._criar_acesso_e_enviar_email(vendedor, grupo_id)
            except serializers.ValidationError:
                vendedor.delete()
                raise
        return vendedor

    def update(self, instance, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        grupo_id = validated_data.pop('grupo_id', None)
        vendedor = super().update(instance, validated_data)
        if criar_acesso and vendedor.email:
            try:
                self._criar_acesso_e_enviar_email(vendedor, grupo_id)
            except serializers.ValidationError:
                raise
        elif grupo_id is not None:
            # Atualizar grupo mesmo sem criar acesso (se já tem acesso)
            self._atualizar_grupo(vendedor, grupo_id)
        return vendedor

    def _criar_acesso_e_enviar_email(self, vendedor, grupo_id=None):
        User = get_user_model()
        from superadmin.models import Loja, VendedorUsuario
        from tenants.middleware import get_current_loja_id
        from django.contrib.auth.models import Group

        loja_id = get_current_loja_id()
        if not loja_id:
            return
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
        except Loja.DoesNotExist:
            return

        email = vendedor.email.strip().lower()
        senha_provisoria = get_random_string(8)

        # Se já tem VendedorUsuario: apenas reenviar senha e atualizar grupo
        vu_existente = VendedorUsuario.objects.using('default').filter(
            loja_id=loja_id,
            vendedor_id=vendedor.id,
        ).select_related('user').first()
        if vu_existente:
            user = vu_existente.user
            user.set_password(senha_provisoria)
            user.first_name = vendedor.nome or user.first_name or ''
            user.save(update_fields=['password', 'first_name'])
            vu_existente.precisa_trocar_senha = True
            vu_existente.save(update_fields=['precisa_trocar_senha'])
            
            # Atualizar grupo se fornecido
            if grupo_id:
                self._atualizar_grupo_usuario(user, grupo_id)
            
            _enviar_email_senha(loja, vendedor, email, senha_provisoria, assunto='Nova senha provisória - CRM Vendas', reenviar=True)
            return

        existing_user = User.objects.using('default').filter(username=email).first()
        if existing_user:
            if VendedorUsuario.objects.using('default').filter(
                user=existing_user,
                loja_id=loja_id,
            ).exists():
                raise serializers.ValidationError({
                    'email': 'Este e-mail já possui acesso a esta loja. Use outro ou cadastre sem "Criar acesso".',
                    'detail': 'Este e-mail já possui acesso a esta loja.',
                })
            if existing_user.lojas_owned.exists():
                raise serializers.ValidationError({
                    'email': 'Já existe um usuário (proprietário de loja) com este e-mail. Use outro ou não marque "Criar acesso".',
                    'detail': 'E-mail já utilizado como proprietário.',
                })
            existing_user.set_password(senha_provisoria)
            existing_user.first_name = vendedor.nome or existing_user.first_name or ''
            existing_user.save(update_fields=['password', 'first_name'])
            VendedorUsuario.objects.using('default').create(
                user=existing_user,
                loja=loja,
                vendedor_id=vendedor.id,
                precisa_trocar_senha=True,
            )
            
            # Adicionar ao grupo se fornecido
            if grupo_id:
                self._atualizar_grupo_usuario(existing_user, grupo_id)
        else:
            user = User.objects.db_manager('default').create_user(
                username=email,
                email=email,
                password=senha_provisoria,
                first_name=vendedor.nome or '',
            )
            VendedorUsuario.objects.using('default').create(
                user=user,
                loja=loja,
                vendedor_id=vendedor.id,
                precisa_trocar_senha=True,
            )
            
            # Adicionar ao grupo se fornecido
            if grupo_id:
                self._atualizar_grupo_usuario(user, grupo_id)

        _enviar_email_senha(loja, vendedor, email, senha_provisoria, assunto='Acesso ao sistema - CRM Vendas')

    def _atualizar_grupo(self, vendedor, grupo_id):
        """Atualiza o grupo de um vendedor que já tem acesso."""
        from tenants.middleware import get_current_loja_id
        from superadmin.models import VendedorUsuario
        
        loja_id = get_current_loja_id()
        if not loja_id:
            return
        
        try:
            vu = VendedorUsuario.objects.using('default').select_related('user').get(
                loja_id=loja_id,
                vendedor_id=vendedor.id,
            )
            self._atualizar_grupo_usuario(vu.user, grupo_id)
        except VendedorUsuario.DoesNotExist:
            pass

    def _atualizar_grupo_usuario(self, user, grupo_id):
        """Atualiza o grupo de um usuário, removendo grupos CRM anteriores."""
        from django.contrib.auth.models import Group
        
        if not grupo_id:
            return
        
        try:
            grupo = Group.objects.using('default').get(id=grupo_id)
            
            # Remover grupos CRM anteriores
            user.groups.remove(*Group.objects.using('default').filter(
                name__in=['Gerente de Vendas', 'Vendedor']
            ))
            
            # Adicionar novo grupo
            user.groups.add(grupo)
        except Group.DoesNotExist:
            pass


def _enviar_email_senha(loja, vendedor, email, senha_provisoria, assunto='Acesso ao Sistema - CRM Vendas', reenviar=False):
    site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
    login_url = f"{site_url}/loja/{loja.slug}/login"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'
    
    if reenviar:
        titulo = "Senha Redefinida"
        subtitulo = "Sua senha foi redefinida com sucesso"
    else:
        titulo = "Bem-vindo ao CRM"
        subtitulo = "Seu acesso foi criado com sucesso!"
    
    try:
        from core.email_templates import email_senha_provisoria_html
        from django.core.mail import EmailMultiAlternatives
        
        info_adicional = {
            "Loja": loja.nome,
            "Sistema": "CRM de Vendas",
            "Seu Cargo": vendedor.cargo,
            "Comissão Padrão": f"{vendedor.comissao_padrao}%",
        }
        
        html_content, texto_plano = email_senha_provisoria_html(
            nome_destinatario=vendedor.nome or 'Vendedor',
            usuario=email,
            senha=senha_provisoria,
            url_login=login_url,
            titulo_principal=titulo,
            subtitulo=subtitulo,
            info_adicional=info_adicional,
            nome_sistema=loja.nome
        )
        
        email_msg = EmailMultiAlternatives(
            subject=assunto,
            body=texto_plano,
            from_email=from_email,
            to=[email],
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send(fail_silently=True)
    except Exception as mail_err:
        logger.warning('Envio de e-mail ao criar vendedor falhou: %s', mail_err)


class ContaSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'razao_social', 'segmento', 'cidade', 'bairro', 'uf']
    
    class Meta:
        model = Conta
        fields = [
            'id', 'nome', 'razao_social', 'cnpj', 'inscricao_estadual', 'segmento', 
            'telefone', 'email', 'site',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'endereco', 'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_cnpj(self, value):
        """Impede duplicata na mesma loja comparando CNPJ só pelos dígitos (formatos diferentes)."""
        import re

        if not value or not str(value).strip():
            return value

        digits = re.sub(r'\D', '', str(value))
        if len(digits) < 11:
            return value

        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        if not loja_id:
            return value

        qs = Conta.objects.filter(loja_id=loja_id).only('id', 'cnpj')
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        for _pk, other_cnpj in qs.values_list('id', 'cnpj'):
            if re.sub(r'\D', '', other_cnpj or '') == digits:
                raise serializers.ValidationError(
                    'Já existe uma empresa cadastrada com este CNPJ nesta loja.'
                )

        return value


class LeadSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    conta_info = serializers.SerializerMethodField()
    contato_info = serializers.SerializerMethodField()
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'empresa', 'cidade', 'bairro', 'uf']
    
    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'cpf_cnpj', 'email', 'telefone', 'origem', 'status',
            'valor_estimado', 'conta', 'conta_info', 'contato', 'contato_info', 'observacoes',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_conta_info(self, obj):
        """Retorna informações completas da conta vinculada."""
        if obj.conta:
            return {
                'id': obj.conta.id,
                'nome': obj.conta.nome,
                'razao_social': obj.conta.razao_social,
                'cnpj': obj.conta.cnpj,
                'inscricao_estadual': obj.conta.inscricao_estadual,
                'email': obj.conta.email,
                'telefone': obj.conta.telefone,
                'site': obj.conta.site,
                'cep': obj.conta.cep,
                'logradouro': obj.conta.logradouro,
                'numero': obj.conta.numero,
                'complemento': obj.conta.complemento,
                'bairro': obj.conta.bairro,
                'cidade': obj.conta.cidade,
                'uf': obj.conta.uf,
            }
        return None
    
    def get_contato_info(self, obj):
        """Retorna informações do contato vinculado."""
        if obj.contato:
            return {
                'id': obj.contato.id,
                'nome': obj.contato.nome,
                'email': obj.contato.email,
                'telefone': obj.contato.telefone,
                'cargo': obj.contato.cargo,
            }
        return None


class LeadListSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)
    contato_nome = serializers.CharField(source='contato.nome', read_only=True)
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'empresa', 'cidade', 'bairro', 'uf']

    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'cpf_cnpj', 'email', 'telefone', 'origem', 'status', 'valor_estimado',
            'conta', 'conta_nome', 'contato', 'contato_nome',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'created_at',
        ]


class ContatoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'cargo']

    class Meta:
        model = Contato
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'conta', 'conta_nome',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class OportunidadeSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    lead_nome = serializers.CharField(source='lead.nome', read_only=True)
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)

    uppercase_fields = ['titulo']

    class Meta:
        model = Oportunidade
        fields = [
            'id', 'titulo', 'lead', 'lead_nome', 'valor', 'etapa', 'vendedor', 'vendedor_nome',
            'probabilidade', 'data_fechamento_prevista', 'data_fechamento',
            'data_fechamento_ganho', 'data_fechamento_perdido', 'valor_comissao',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AtividadeSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['titulo']
    
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'data', 'duracao_minutos',
            'concluido', 'observacoes', 'google_event_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AtividadeListSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    """Serializer para listagem sem google_event_id (compatível com schemas antigos)."""
    uppercase_fields = ['titulo']
    
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'data', 'duracao_minutos',
            'concluido', 'observacoes', 'created_at', 'updated_at',
        ]


class CategoriaProdutoServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    produtos_count = serializers.SerializerMethodField()
    uppercase_fields = ['nome']
    
    class Meta:
        model = CategoriaProdutoServico
        fields = [
            'id', 'nome', 'descricao', 'cor', 'ordem', 'ativo',
            'produtos_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_produtos_count(self, obj):
        """Retorna quantidade de produtos/serviços nesta categoria"""
        return obj.produtos_servicos.filter(ativo=True).count()


class ProdutoServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    categoria_cor = serializers.CharField(source='categoria.cor', read_only=True)
    uppercase_fields = ['nome', 'codigo']
    
    class Meta:
        model = ProdutoServico
        fields = [
            'id', 'tipo', 'codigo', 'nome', 'descricao', 'categoria', 
            'categoria_nome', 'categoria_cor', 'preco', 'ativo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class OportunidadeItemSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    produto_servico_nome = serializers.CharField(source='produto_servico.nome', read_only=True)
    produto_servico_tipo = serializers.CharField(source='produto_servico.tipo', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OportunidadeItem
        fields = [
            'id', 'oportunidade', 'produto_servico', 'produto_servico_nome', 'produto_servico_tipo',
            'quantidade', 'preco_unitario', 'subtotal', 'observacao', 'created_at',
        ]
        read_only_fields = ['created_at']

    def get_subtotal(self, obj):
        return float(obj.quantidade * obj.preco_unitario)


class PropostaSerializer(serializers.ModelSerializer):
    oportunidade_titulo = serializers.CharField(source='oportunidade.titulo', read_only=True)
    lead_nome = serializers.CharField(source='oportunidade.lead.nome', read_only=True)
    lead_email = serializers.CharField(source='oportunidade.lead.email', read_only=True)

    class Meta:
        model = Proposta
        fields = [
            'id', 'oportunidade', 'oportunidade_titulo', 'lead_nome', 'lead_email',
            'numero', 'titulo', 'conteudo', 'valor_total', 'status', 'status_assinatura',
            'data_envio', 'data_resposta', 'observacoes',
            'nome_vendedor_assinatura', 'nome_cliente_assinatura',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'numero']


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

    class Meta:
        model = Contrato
        fields = [
            'id', 'oportunidade', 'oportunidade_titulo', 'lead_nome', 'lead_email',
            'numero', 'titulo', 'conteudo', 'valor_total', 'status', 'status_assinatura',
            'data_envio', 'data_assinatura', 'observacoes',
            'nome_vendedor_assinatura', 'nome_cliente_assinatura',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'numero']


class CRMConfigSerializer(serializers.ModelSerializer):
    provedor_nf_display = serializers.CharField(source='get_provedor_nf_display', read_only=True)
    asaas_api_key_configured = serializers.SerializerMethodField()
    issnet_senhas_salvas = serializers.SerializerMethodField()
    issnet_certificado = serializers.SerializerMethodField()

    def get_asaas_api_key_configured(self, obj):
        return bool((getattr(obj, 'asaas_api_key', None) or '').strip())

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
        """Trata upload do certificado .pfx como bytes no banco."""
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
            'issnet_senhas_salvas',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'asaas_api_key_configured', 'issnet_senhas_salvas', 'issnet_certificado']
        extra_kwargs = {
            'issnet_senha': {'write_only': True},
            'issnet_senha_certificado': {'write_only': True},
            'asaas_api_key': {'write_only': True, 'required': False, 'allow_blank': True},
        }
