from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, 
    PagamentoLoja, UsuarioSistema, HistoricoAcessoGlobal,
    ViolacaoSeguranca
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
        read_only_fields = ['database_name', 'database_created', 'login_page_url', 'senha_provisoria']


class LojaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar loja com banco isolado"""
    owner_full_name = serializers.CharField(write_only=True, required=True, help_text='Nome completo do administrador')
    owner_username = serializers.CharField(write_only=True, help_text='Nome de acesso (login) à loja')
    owner_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    owner_email = serializers.EmailField(write_only=True)
    dia_vencimento = serializers.IntegerField(write_only=True, default=10, min_value=1, max_value=28)
    
    class Meta:
        model = Loja
        fields = [
            'nome', 'slug', 'descricao', 'cpf_cnpj',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'tipo_loja', 'plano', 'tipo_assinatura',
            'owner_full_name', 'owner_username', 'owner_password', 'owner_email', 'dia_vencimento',
            'logo', 'cor_primaria', 'cor_secundaria', 'dominio_customizado'
        ]
    
    def create(self, validated_data):
        import secrets
        import string
        import traceback
        import os
        
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Extrair dados do owner
            owner_full_name = (validated_data.pop('owner_full_name', '') or '').strip()
            owner_username = validated_data.pop('owner_username')
            owner_password = validated_data.pop('owner_password', None)
            owner_email = validated_data.pop('owner_email')
            dia_vencimento = validated_data.pop('dia_vencimento', 10)
            # Nome completo -> first_name e last_name (primeira palavra = first_name, resto = last_name)
            parts = owner_full_name.split(None, 1) if owner_full_name else []
            owner_first_name = parts[0] if parts else ''
            owner_last_name = parts[1] if len(parts) > 1 else ''
            
            # Gerar senha provisória se não fornecida
            if not owner_password:
                # Gerar senha segura: 8 caracteres com letras, números e símbolos
                alphabet = string.ascii_letters + string.digits + "!@#$%&*"
                owner_password = ''.join(secrets.choice(alphabet) for _ in range(8))
        
            # Criar usuário owner da loja
            owner = User.objects.create_user(
                username=owner_username,
                email=owner_email,
                password=owner_password,
                first_name=owner_first_name,
                last_name=owner_last_name,
                is_staff=False  # CORREÇÃO: Usuários de loja NÃO devem ser staff
            )
            
            # Slug: usar o enviado pelo frontend se for válido e único; senão o model gera automaticamente
            slug_enviado = (validated_data.pop('slug', None) or '').strip()
            if slug_enviado:
                from django.utils.text import slugify
                slug_sanitizado = slugify(slug_enviado) or None
                if slug_sanitizado:
                    if Loja.objects.filter(slug=slug_sanitizado).exists():
                        raise serializers.ValidationError({'slug': f'Já existe uma loja com o slug "{slug_sanitizado}". Escolha outro.'})
                    validated_data['slug'] = slug_sanitizado
            validated_data['owner'] = owner
            validated_data['senha_provisoria'] = owner_password  # Salvar senha provisória
            validated_data['senha_foi_alterada'] = False  # Garantir que precisa trocar no primeiro login
            
            # 🔒 VALIDAÇÃO: Verificar que database_name será único
            if 'slug' in validated_data:
                proposed_db_name = f"loja_{validated_data['slug'].replace('-', '_')}"
                if Loja.objects.filter(database_name=proposed_db_name).exists():
                    raise serializers.ValidationError({
                        'slug': f'Já existe uma loja com database_name derivado deste slug. O sistema gerará um slug único automaticamente.'
                    })
            
            loja = Loja.objects.create(**validated_data)
            
            # LOG para confirmar criação
            print(f"\n{'='*80}")
            print(f"✅ Loja criada: {loja.nome}")
            print(f"   - ID: {loja.id}")
            print(f"   - Slug: {loja.slug}")
            print(f"   - Database name: {loja.database_name}")
            print(f"   - Owner: {owner.username} ({owner.email})")
            print(f"   - Senha provisória: {owner_password[:3]}***")
            print(f"   - Senha foi alterada: {loja.senha_foi_alterada}")
            print(f"{'='*80}\n")
            
            # Criar schema no PostgreSQL automaticamente
            try:
                from django.db import connection
                schema_name = loja.database_name.replace('-', '_')  # Remover hífens
                
                with connection.cursor() as cursor:
                    # Criar schema - validando nome para evitar SQL injection
                    import re
                    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
                        raise ValueError(f"Nome de schema inválido: {schema_name}")
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                    print(f"✅ Schema '{schema_name}' criado no PostgreSQL")
                
                # Marcar como criado
                loja.database_created = True
                loja.save()
                
                # 🔒 VALIDAÇÃO: Verificar que schema foi criado com sucesso
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.schemata 
                        WHERE schema_name = %s
                    """, [schema_name])
                    schema_exists = cursor.fetchone()[0] > 0
                    
                    if not schema_exists:
                        raise Exception(f"Schema '{schema_name}' não foi criado corretamente!")
                    
                    print(f"✅ Schema '{schema_name}' verificado e confirmado")
                
                # Adicionar às configurações do Django
                from django.conf import settings
                import dj_database_url
                
                DATABASE_URL = os.environ.get('DATABASE_URL')
                if DATABASE_URL:
                    default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
                    settings.DATABASES[loja.database_name] = {
                        **default_db,
                        'OPTIONS': {
                            'options': f'-c search_path={schema_name},public'
                        },
                        'ATOMIC_REQUESTS': False,
                        'AUTOCOMMIT': True,
                        'CONN_MAX_AGE': 600,
                        'CONN_HEALTH_CHECKS': True,
                        'TIME_ZONE': None,
                    }
                    print(f"✅ Configuração de banco adicionada para '{loja.database_name}'")
                    print(f"✅ Banco '{loja.database_name}' adicionado às configurações")
                
                # Criar tabelas no novo schema copiando estrutura do public
                try:
                    tipo_loja_nome = loja.tipo_loja.nome if loja.tipo_loja else ''
                    
                    # Definir tabelas por tipo de loja
                    tabelas_por_tipo = {
                        'Clínica de Estética': [
                            'clinica_clientes',
                            'clinica_profissionais',
                            'clinica_procedimentos',
                            'clinica_agendamentos',
                            'clinica_funcionarios',
                            'clinica_protocolos',
                            'clinica_consultas',
                            'clinica_evolucoes',
                            'clinica_anamneses_templates',
                            'clinica_anamneses',
                            'clinica_horarios_funcionamento',
                            'clinica_bloqueios_agenda',
                            'clinica_historico_login',
                            'clinica_categorias_financeiras',
                            'clinica_transacoes'
                        ],
                        'CRM Vendas': [
                            'crm_clientes',
                            'crm_leads',
                            'crm_oportunidades',
                            'crm_vendas',
                            'crm_funcionarios'
                        ],
                        'Cabeleireiro': [
                            'cabeleireiro_clientes',
                            'cabeleireiro_profissionais',
                            'cabeleireiro_servicos',
                            'cabeleireiro_agendamentos',
                            'cabeleireiro_funcionarios'
                        ],
                        'Restaurante': [
                            'restaurante_mesas',
                            'restaurante_produtos',
                            'restaurante_pedidos',
                            'restaurante_funcionarios'
                        ],
                        'Serviços': [
                            'servicos_clientes',
                            'servicos_servicos',
                            'servicos_agendamentos',
                            'servicos_funcionarios'
                        ],
                        'E-commerce': [
                            'ecommerce_produtos',
                            'ecommerce_categorias',
                            'ecommerce_pedidos',
                            'ecommerce_clientes'
                        ]
                    }
                    
                    tabelas = tabelas_por_tipo.get(tipo_loja_nome, [])
                    
                    if tabelas:
                        tabelas_criadas = 0
                        with connection.cursor() as cursor:
                            for tabela in tabelas:
                                try:
                                    # Verificar se tabela existe no public
                                    cursor.execute("""
                                        SELECT table_name 
                                        FROM information_schema.tables 
                                        WHERE table_schema = 'public' AND table_name = %s
                                    """, [tabela])
                                    
                                    if not cursor.fetchone():
                                        print(f"⚠️  Tabela {tabela} não existe no schema public, pulando...")
                                        continue
                                    
                                    # Copiar estrutura da tabela do schema public
                                    cursor.execute(f"""
                                        CREATE TABLE {schema_name}.{tabela} 
                                        (LIKE public.{tabela} INCLUDING ALL)
                                    """)
                                    tabelas_criadas += 1
                                    print(f"   ✅ {tabela}")
                                except Exception as e:
                                    print(f"   ⚠️  Erro ao criar {tabela}: {str(e)[:100]}")
                        
                        if tabelas_criadas > 0:
                            print(f"✅ {tabelas_criadas} tabelas criadas no schema '{schema_name}'")
                        else:
                            print(f"⚠️ Nenhuma tabela foi criada no schema '{schema_name}'")
                    else:
                        print(f"⚠️ Tipo de loja '{tipo_loja_nome}' não tem tabelas definidas")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao criar tabelas: {e}")
                    import traceback
                    print(traceback.format_exc())
                
            except Exception as e:
                print(f"⚠️ Erro ao criar schema: {e}")
                # Não falhar a criação da loja por causa do schema
            
            # Calcular valor baseado no tipo de assinatura
            if loja.tipo_assinatura == 'anual':
                valor_mensalidade = loja.plano.preco_anual / 12 if loja.plano.preco_anual else loja.plano.preco_mensal
            else:
                valor_mensalidade = loja.plano.preco_mensal
            
            # Criar financeiro
            from datetime import date, timedelta
            from calendar import monthrange
            
            # Calcular próxima cobrança baseada no dia de vencimento
            # SEMPRE no próximo mês (não no mês atual)
            hoje = date.today()
            
            # Calcular próximo mês
            if hoje.month == 12:
                proximo_mes = 1
                proximo_ano = hoje.year + 1
            else:
                proximo_mes = hoje.month + 1
                proximo_ano = hoje.year
            
            # Ajustar dia se o mês não tiver esse dia (ex: dia 31 em fevereiro)
            ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
            dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
            
            # Definir próxima cobrança sempre no próximo mês
            proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
            
            financeiro = FinanceiroLoja.objects.create(
                loja=loja,
                data_proxima_cobranca=proxima_cobranca,
                valor_mensalidade=valor_mensalidade,
                dia_vencimento=dia_vencimento,
                status_pagamento='ativo' if not loja.is_trial else 'pendente'
            )
            
            # 🚀 INTEGRAÇÃO ASAAS: Criação automática via signal
            # A cobrança é criada automaticamente pelo signal em asaas_integration/signals.py
            # Não criar aqui para evitar duplicação
            # 
            # NOTA: O signal create_asaas_subscription_on_loja_creation já cria:
            # - AsaasCustomer
            # - AsaasPayment  
            # - LojaAssinatura
            #
            # Se precisar dos dados do Asaas imediatamente após criar a loja,
            # consulte LojaAssinatura.objects.get(loja_slug=loja.slug)
            
            # 👤 CRIAR FUNCIONÁRIO ADMIN AUTOMATICAMENTE
            try:
                # Importar o model de Funcionario do tipo de loja correto
                tipo_loja_nome = loja.tipo_loja.nome if loja.tipo_loja else ''
                
                if tipo_loja_nome == 'Clínica de Estética':
                    from clinica_estetica.models import Funcionario
                    
                    # Criar funcionário admin
                    Funcionario.objects.create(
                        loja_id=loja.id,
                        nome=owner_first_name + (' ' + owner_last_name if owner_last_name else ''),
                        email=owner_email,
                        telefone='',
                        cargo='Administrador',
                        is_admin=True,
                        is_active=True
                    )
                    print(f"✅ Funcionário admin criado para {owner_email}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao criar funcionário admin: {e}")
                # Não falhar a criação da loja por causa do funcionário
        
            # Enviar email com senha provisória
            try:
                # Verificar se email está configurado
                if hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL:
                    assunto = f"Acesso à sua loja {loja.nome} - Senha Provisória"
                    
                    # Mensagem base
                    mensagem = f"""
Olá!

Sua loja "{loja.nome}" foi criada com sucesso no nosso sistema!

🔐 DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
• Usuário: {owner_username}
• Senha Provisória: {owner_password}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}
• Assinatura: {loja.get_tipo_assinatura_display()}"""

                    # Adicionar informações do boleto se disponível
                    if hasattr(loja, '_asaas_data') and loja._asaas_data.get('success'):
                        asaas_data = loja._asaas_data
                        mensagem += f"""

💰 INFORMAÇÕES DE PAGAMENTO:
• Valor da Mensalidade: R$ {loja.plano.preco_mensal}
• Vencimento: {asaas_data.get('due_date', 'Em breve')}
• Status: Aguardando Pagamento"""
                        
                        if asaas_data.get('boleto_url'):
                            mensagem += f"""
• Boleto: {asaas_data.get('boleto_url')}"""
                        
                        if asaas_data.get('pix_copy_paste'):
                            mensagem += f"""
• PIX Copia e Cola: {asaas_data.get('pix_copy_paste')}"""

                    mensagem += f"""

🎯 PRÓXIMOS PASSOS:
1. Acesse o link de login acima
2. Faça login com os dados fornecidos
3. Altere sua senha provisória
4. Configure sua loja"""
                    
                    if hasattr(loja, '_asaas_data') and loja._asaas_data.get('success'):
                        mensagem += """
5. Efetue o pagamento da primeira mensalidade"""

                    mensagem += """

Bem-vindo ao nosso sistema!

---
Equipe de Suporte
Sistema Multi-Loja"""
                    
                    send_mail(
                        subject=assunto,
                        message=mensagem,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[owner_email],
                        fail_silently=True  # Não falhar se email não funcionar
                    )
                    
                    print(f"✅ Email enviado para {owner_email} com senha provisória e dados de pagamento")
                else:
                    print(f"⚠️ Email não configurado, senha provisória: {owner_password}")
                
            except Exception as e:
                print(f"⚠️ Erro ao enviar email: {e}")
                # Não falhar a criação da loja por causa do email
            
            # Adicionar senha provisória ao contexto para retorno
            loja._senha_provisoria = owner_password
            
            return loja
        
        except Exception as e:
            print(f"❌ ERRO AO CRIAR LOJA: {e}")
            print(traceback.format_exc())
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
