from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, 
    PagamentoLoja, UsuarioSistema, HistoricoAcessoGlobal,
    ViolacaoSeguranca, EmailRetry, ConfiguracaoBackup, HistoricoBackup
)
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class UsuarioSistemaSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = UsuarioSistema
        fields = '__all__'
    
    def create(self, validated_data):
        import random
        import string
        from django.core.mail import send_mail
        from django.conf import settings
        
        user_data = validated_data.pop('user')
        
        # Gerar senha provisória automaticamente
        senha_provisoria = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%&*', k=10))
        
        # Criar usuário
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data.get('email', ''),
            password=senha_provisoria,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_staff=True
        )
        
        # Criar perfil com senha provisória
        perfil = UsuarioSistema.objects.create(
            user=user, 
            senha_provisoria=senha_provisoria,
            senha_foi_alterada=False,
            **validated_data
        )
        
        # Adicionar ao grupo
        if perfil.tipo == 'suporte':
            grupo, _ = Group.objects.get_or_create(name='suporte')
            user.groups.add(grupo)
        elif perfil.tipo == 'superadmin':
            user.is_superuser = True
            user.save()
        
        # Enviar email com senha provisória
        try:
            tipo_display = 'Super Admin' if perfil.tipo == 'superadmin' else 'Suporte'
            url_login = f"https://lwksistemas.com.br/{perfil.tipo}/login"
            
            assunto = f"Bem-vindo ao LWK Sistemas - {tipo_display}"
            mensagem = f"""
Olá {user.first_name or user.username}!

Sua conta foi criada no LWK Sistemas.

🔐 DADOS DE ACESSO:
• URL de Login: {url_login}
• Usuário: {user.username}
• Senha Provisória: {senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Você será solicitado a trocar a senha no primeiro acesso
• Por segurança, altere a senha assim que fizer login
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA CONTA:
• Nome: {user.first_name} {user.last_name}
• Email: {user.email}
• Tipo: {tipo_display}

---
Equipe LWK Sistemas
            """.strip()
            
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
            logger.info(f"✅ Email enviado para {user.email} com senha provisória")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao enviar email: {e}")
        
        # Armazenar senha provisória no contexto para retornar na resposta
        perfil._senha_provisoria_gerada = senha_provisoria
        
        return perfil
    
    def update(self, instance, validated_data):
        """
        Atualizar usuário do sistema
        
        IMPORTANTE:
        - Username NÃO pode ser alterado (ignorado se enviado)
        - Senha só é atualizada se fornecida
        - Tipo pode ser alterado (superadmin <-> suporte)
        """
        user_data = validated_data.pop('user', {})
        
        # Atualizar dados do User (exceto username)
        user = instance.user
        if 'email' in user_data:
            user.email = user_data['email']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        
        # Atualizar senha se fornecida
        if 'password' in user_data and user_data['password']:
            user.set_password(user_data['password'])
        
        user.save()
        
        # Atualizar tipo e permissões
        tipo_antigo = instance.tipo
        tipo_novo = validated_data.get('tipo', tipo_antigo)
        
        if tipo_antigo != tipo_novo:
            # Remover permissões antigas
            if tipo_antigo == 'superadmin':
                user.is_superuser = False
            elif tipo_antigo == 'suporte':
                grupo_suporte = Group.objects.filter(name='suporte').first()
                if grupo_suporte:
                    user.groups.remove(grupo_suporte)
            
            # Adicionar novas permissões
            if tipo_novo == 'superadmin':
                user.is_superuser = True
            elif tipo_novo == 'suporte':
                grupo_suporte, _ = Group.objects.get_or_create(name='suporte')
                user.groups.add(grupo_suporte)
            
            user.save()
        
        # Atualizar campos do UsuarioSistema
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        return instance


class TipoLojaSerializer(serializers.ModelSerializer):
    total_lojas = serializers.SerializerMethodField()
    planos = serializers.SerializerMethodField()
    
    class Meta:
        model = TipoLoja
        fields = '__all__'
    
    def get_total_lojas(self, obj):
        return obj.lojas.count()
    
    def get_planos(self, obj):
        planos = obj.planos.filter(is_active=True).order_by('ordem', 'preco_mensal')
        return PlanoAssinaturaSerializer(planos, many=True).data


class PlanoAssinaturaSerializer(serializers.ModelSerializer):
    total_lojas = serializers.SerializerMethodField()
    tipos_loja_nomes = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanoAssinatura
        fields = '__all__'
    
    def get_total_lojas(self, obj):
        return obj.lojas.filter(is_active=True).count()
    
    def get_tipos_loja_nomes(self, obj):
        return [tipo.nome for tipo in obj.tipos_loja.all()]


class FinanceiroLojaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_pagamento_display', read_only=True)
    
    class Meta:
        model = FinanceiroLoja
        fields = '__all__'


class PagamentoLojaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PagamentoLoja
        fields = '__all__'


class LojaSerializer(serializers.ModelSerializer):
    tipo_loja_nome = serializers.CharField(source='tipo_loja.nome', read_only=True)
    plano_nome = serializers.CharField(source='plano.nome', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    financeiro = FinanceiroLojaSerializer(read_only=True)
    tipo_assinatura_display = serializers.CharField(source='get_tipo_assinatura_display', read_only=True)
    
    class Meta:
        model = Loja
        fields = '__all__'
        read_only_fields = ['database_name', 'database_created', 'login_page_url', 'senha_provisoria', 'owner', 'owner_telefone']


class LojaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar loja com banco isolado"""
    owner_full_name = serializers.CharField(write_only=True, required=True, help_text='Nome completo do administrador')
    owner_username = serializers.CharField(write_only=True, help_text='Nome de acesso (login) à loja')
    owner_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    owner_email = serializers.EmailField(write_only=True)
    owner_telefone = serializers.CharField(write_only=True, required=False, allow_blank=True, help_text='Telefone do administrador')
    dia_vencimento = serializers.IntegerField(write_only=True, default=10, min_value=1, max_value=28)
    
    class Meta:
        model = Loja
        fields = [
            'nome', 'slug', 'descricao', 'cpf_cnpj',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'tipo_loja', 'plano', 'tipo_assinatura', 'provedor_boleto_preferido',
            'owner_full_name', 'owner_username', 'owner_password', 'owner_email', 'owner_telefone', 'dia_vencimento',
            'logo', 'cor_primaria', 'cor_secundaria', 'dominio_customizado',
            'atalho', 'subdomain',  # ✅ NOVO v1421: Sistema híbrido de acesso
        ]
    
    def create(self, validated_data):
        """
        Cria loja usando services para separar responsabilidades
        ✅ REFATORADO v769: Reduzido de 300+ para ~80 linhas usando services
        """
        from .services import (
            LojaCreationService,
            DatabaseSchemaService,
            FinanceiroService,
            ProfessionalService
        )
        import traceback

        try:
            # 1. EXTRAIR E PROCESSAR DADOS DO OWNER
            owner_full_name = (validated_data.pop('owner_full_name', '') or '').strip()
            owner_username = validated_data.pop('owner_username')
            owner_password = validated_data.pop('owner_password', None)
            owner_email = validated_data.pop('owner_email')
            owner_telefone = (validated_data.pop('owner_telefone', '') or '').strip()
            dia_vencimento = validated_data.pop('dia_vencimento', 10)

            # Processar nome completo
            first_name, last_name = LojaCreationService.processar_nome_completo(owner_full_name)

            # Gerar senha se não fornecida
            if not owner_password:
                owner_password = LojaCreationService.gerar_senha_provisoria()

            # 2. CRIAR OU ATUALIZAR OWNER
            owner = LojaCreationService.criar_ou_atualizar_owner(
                username=owner_username,
                email=owner_email,
                password=owner_password,
                first_name=first_name,
                last_name=last_name
            )

            # 3. SLUG FIXO: CPF/CNPJ (apenas dígitos) — URL: /loja/41449198000172/login
            slug_enviado = validated_data.pop('slug', None)
            cpf_cnpj = (validated_data.get('cpf_cnpj') or '').strip()
            cpf_cnpj_digits = ''.join(c for c in cpf_cnpj if c.isdigit()) if cpf_cnpj else ''
            # Prioridade: slug enviado, ou CPF/CNPJ (11+ dígitos), ou slug enviado vazio
            if slug_enviado and str(slug_enviado).strip():
                slug_candidato = str(slug_enviado).strip()
            elif len(cpf_cnpj_digits) >= 11:
                slug_candidato = cpf_cnpj_digits
            else:
                slug_candidato = slug_enviado
            slug_validado = LojaCreationService.validar_e_processar_slug(slug_candidato)
            if slug_validado:
                validated_data['slug'] = slug_validado

            # 4. PREPARAR DADOS DA LOJA
            validated_data['owner'] = owner
            validated_data['owner_telefone'] = owner_telefone
            validated_data['senha_provisoria'] = owner_password
            validated_data['senha_foi_alterada'] = False
            validated_data.setdefault('provedor_boleto_preferido', 'asaas')

            # 5. CRIAR LOJA
            loja = Loja.objects.create(**validated_data)

            # Log da criação
            LojaCreationService.log_criacao_loja(loja, owner, owner_password)

            # 6. CONFIGURAR SCHEMA DO BANCO DE DADOS
            try:
                DatabaseSchemaService.configurar_schema_completo(loja)
            except Exception as e:
                logger.error(f"Erro ao configurar schema para loja {loja.slug}: {e}")
                # Qualquer falha no schema isolado invalida o cadastro (evita loja sem tabelas).
                raise serializers.ValidationError(
                    f"Não foi possível configurar o banco de dados da loja: {str(e)}. "
                    "Tente novamente ou entre em contato com o suporte."
                )

            # 7. CRIAR FINANCEIRO
            try:
                FinanceiroService.criar_financeiro_loja(loja, dia_vencimento)
            except Exception as e:
                logger.error(f"Erro ao criar financeiro: {e}")
                raise

            # 8. CRIAR PROFISSIONAL/FUNCIONÁRIO ADMIN
            # Re-fetch loja para garantir database_created atualizado após configurar_schema
            loja.refresh_from_db()
            try:
                ok = ProfessionalService.criar_profissional_por_tipo(loja, owner, owner_telefone)
                if not ok:
                    logger.warning(
                        "ProfessionalService não criou profissional/vendedor para loja=%s (owner=%s). "
                        "Execute: python manage.py criar_funcionarios_admins para corrigir.",
                        loja.slug, owner.email
                    )
            except Exception as e:
                logger.warning(
                    "Erro ao criar profissional/funcionário para loja=%s: %s. "
                    "Execute: python manage.py criar_funcionarios_admins para corrigir.",
                    loja.slug, e
                )
                # Não falhar a criação da loja

            # 9. INTEGRAÇÃO ASAAS
            # A cobrança é criada automaticamente pelo signal em asaas_integration/signals.py
            # Signal: create_asaas_subscription_on_loja_creation
            # Cria: AsaasCustomer, AsaasPayment, LojaAssinatura

            logger.info(
                "Loja criada com sucesso: %s (owner: %s). Senha será enviada após confirmação do pagamento.",
                loja.slug,
                owner_email,
            )

            return loja

        except Exception as e:
            logger.error(f"Erro ao criar loja: {e}")
            logger.error(traceback.format_exc())
            raise serializers.ValidationError(f"Erro ao criar loja: {str(e)}")



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
            'ip_address',
            'created_at',
            'data_hora',
        ]
    
    def get_data_hora(self, obj):
        """Formata data e hora para exibição (timezone local)"""
        from django.utils import timezone
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d/%m/%Y %H:%M:%S')



class EmailRetrySerializer(serializers.ModelSerializer):
    """
    Serializer para EmailRetry
    
    ✅ NOVO v719: Gerenciamento de emails com falha de envio
    """
    
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    loja_slug = serializers.CharField(source='loja.slug', read_only=True)
    pode_retentar = serializers.SerializerMethodField()
    atingiu_max = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailRetry
        fields = [
            'id',
            'destinatario',
            'assunto',
            'mensagem',
            'tentativas',
            'max_tentativas',
            'enviado',
            'erro',
            'loja',
            'loja_nome',
            'loja_slug',
            'created_at',
            'updated_at',
            'proxima_tentativa',
            'pode_retentar',
            'atingiu_max',
            'status_display',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_pode_retentar(self, obj):
        """Verifica se ainda pode tentar reenviar"""
        return obj.pode_retentar()
    
    def get_atingiu_max(self, obj):
        """Verifica se atingiu máximo de tentativas"""
        return obj.atingiu_max_tentativas()
    
    def get_status_display(self, obj):
        """Retorna status formatado"""
        if obj.enviado:
            return "✅ Enviado"
        elif obj.atingiu_max_tentativas():
            return f"❌ Falhou ({obj.tentativas}/{obj.max_tentativas})"
        else:
            return f"⏳ Aguardando ({obj.tentativas}/{obj.max_tentativas})"



# ============================================================================
# SERIALIZERS DE BACKUP - v800
# ============================================================================

class ConfiguracaoBackupSerializer(serializers.ModelSerializer):
    """
    Serializer para ConfiguracaoBackup.
    
    Boas práticas:
    - Validação de dados no método validate()
    - Campos read-only apropriados
    - Campos display para choices
    """
    
    frequencia_display = serializers.CharField(source='get_frequencia_display', read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    
    class Meta:
        model = ConfiguracaoBackup
        fields = [
            'id',
            'loja',
            'loja_nome',
            'backup_automatico_ativo',
            'horario_envio',
            'frequencia',
            'frequencia_display',
            'dia_semana',
            'dia_semana_display',
            'dia_mes',
            'ultimo_backup',
            'ultimo_envio_email',
            'total_backups_realizados',
            'incluir_imagens',
            'manter_ultimos_n_backups',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'loja',
            'ultimo_backup',
            'ultimo_envio_email',
            'total_backups_realizados',
            'created_at',
            'updated_at',
        ]
    
    def validate(self, data):
        """Validações customizadas"""
        frequencia = data.get('frequencia')
        dia_semana = data.get('dia_semana')
        dia_mes = data.get('dia_mes')
        
        # Validar dia_semana para backup semanal
        if frequencia == 'semanal' and dia_semana is None:
            raise serializers.ValidationError({
                'dia_semana': 'Dia da semana é obrigatório para backup semanal'
            })
        
        # Validar dia_mes para backup mensal
        if frequencia == 'mensal':
            if dia_mes is None:
                raise serializers.ValidationError({
                    'dia_mes': 'Dia do mês é obrigatório para backup mensal'
                })
            if not (1 <= dia_mes <= 28):
                raise serializers.ValidationError({
                    'dia_mes': 'Dia do mês deve estar entre 1 e 28'
                })
        
        # Validar manter_ultimos_n_backups
        manter = data.get('manter_ultimos_n_backups')
        if manter is not None:
            if manter < 1:
                raise serializers.ValidationError({
                    'manter_ultimos_n_backups': 'Deve manter pelo menos 1 backup'
                })
            if manter > 30:
                raise serializers.ValidationError({
                    'manter_ultimos_n_backups': 'Não é recomendado manter mais de 30 backups'
                })
        
        return data


class HistoricoBackupSerializer(serializers.ModelSerializer):
    """
    Serializer para HistoricoBackup.
    
    Inclui campos calculados e formatados para facilitar uso no frontend.
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    loja_slug = serializers.CharField(source='loja.slug', read_only=True)
    solicitado_por_nome = serializers.SerializerMethodField()
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    tempo_formatado = serializers.CharField(source='get_tempo_processamento_formatado', read_only=True)
    
    class Meta:
        model = HistoricoBackup
        fields = [
            'id',
            'loja',
            'loja_nome',
            'loja_slug',
            'solicitado_por',
            'solicitado_por_nome',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'arquivo_nome',
            'arquivo_tamanho_mb',
            'tamanho_formatado',
            'arquivo_path',
            'total_registros',
            'tabelas_incluidas',
            'tempo_processamento_segundos',
            'tempo_formatado',
            'erro_mensagem',
            'email_enviado',
            'email_enviado_em',
            'email_destinatario',
            'created_at',
            'concluido_em',
        ]
        read_only_fields = [
            'id',
            'loja',
            'solicitado_por',
            'tipo',
            'status',
            'arquivo_nome',
            'arquivo_tamanho_mb',
            'arquivo_path',
            'total_registros',
            'tabelas_incluidas',
            'tempo_processamento_segundos',
            'erro_mensagem',
            'email_enviado',
            'email_enviado_em',
            'email_destinatario',
            'created_at',
            'concluido_em',
        ]
    
    def get_solicitado_por_nome(self, obj):
        """Retorna nome do usuário que solicitou"""
        if obj.solicitado_por:
            return obj.solicitado_por.get_full_name() or obj.solicitado_por.username
        return None


class HistoricoBackupListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de histórico.
    
    Retorna apenas campos essenciais para melhor performance.
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    
    class Meta:
        model = HistoricoBackup
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'arquivo_nome',
            'tamanho_formatado',
            'total_registros',
            'email_enviado',
            'created_at',
        ]
