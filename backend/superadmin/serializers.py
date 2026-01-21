from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, 
    PagamentoLoja, UsuarioSistema
)

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
        user_data = validated_data.pop('user')
        password = user_data.pop('password', 'senha123')
        
        # Criar usuário
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data.get('email', ''),
            password=password,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_staff=True
        )
        
        # Criar perfil
        perfil = UsuarioSistema.objects.create(user=user, **validated_data)
        
        # Adicionar ao grupo
        if perfil.tipo == 'suporte':
            grupo, _ = Group.objects.get_or_create(name='suporte')
            user.groups.add(grupo)
        elif perfil.tipo == 'superadmin':
            user.is_superuser = True
            user.save()
        
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
    owner_username = serializers.CharField(write_only=True)
    owner_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    owner_email = serializers.EmailField(write_only=True)
    dia_vencimento = serializers.IntegerField(write_only=True, default=10, min_value=1, max_value=28)
    
    class Meta:
        model = Loja
        fields = [
            'nome', 'slug', 'descricao', 'cpf_cnpj', 'tipo_loja', 'plano', 'tipo_assinatura',
            'owner_username', 'owner_password', 'owner_email', 'dia_vencimento',
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
            owner_username = validated_data.pop('owner_username')
            owner_password = validated_data.pop('owner_password', None)
            owner_email = validated_data.pop('owner_email')
            dia_vencimento = validated_data.pop('dia_vencimento', 10)
            
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
                is_staff=False  # CORREÇÃO: Usuários de loja NÃO devem ser staff
            )
            
            # Criar loja
            validated_data['owner'] = owner
            validated_data['senha_provisoria'] = owner_password  # Salvar senha provisória
            loja = Loja.objects.create(**validated_data)
            
            # Criar schema no PostgreSQL automaticamente
            try:
                from django.db import connection
                schema_name = loja.database_name.replace('-', '_')  # Remover hífens
                
                with connection.cursor() as cursor:
                    # Criar schema
                    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                    print(f"✅ Schema '{schema_name}' criado no PostgreSQL")
                
                # Marcar como criado
                loja.database_created = True
                loja.save()
                
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
                    print(f"✅ Banco '{loja.database_name}' adicionado às configurações")
                
                # Aplicar migrations no novo schema
                from django.core.management import call_command
                try:
                    call_command('migrate', 'stores', '--database', loja.database_name, verbosity=0)
                    call_command('migrate', 'products', '--database', loja.database_name, verbosity=0)
                    print(f"✅ Migrations aplicadas no schema '{schema_name}'")
                except Exception as e:
                    print(f"⚠️ Erro ao aplicar migrations: {e}")
                
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
            hoje = date.today()
            if hoje.day <= dia_vencimento:
                # Próxima cobrança neste mês
                proxima_cobranca = date(hoje.year, hoje.month, dia_vencimento)
            else:
                # Próxima cobrança no próximo mês
                if hoje.month == 12:
                    proxima_cobranca = date(hoje.year + 1, 1, dia_vencimento)
                else:
                    proxima_cobranca = date(hoje.year, hoje.month + 1, dia_vencimento)
            
            financeiro = FinanceiroLoja.objects.create(
                loja=loja,
                data_proxima_cobranca=proxima_cobranca,
                valor_mensalidade=valor_mensalidade,
                dia_vencimento=dia_vencimento,
                status_pagamento='ativo' if not loja.is_trial else 'pendente'
            )
            
            # 🚀 INTEGRAÇÃO ASAAS: Criar cobrança automática
            try:
                from .asaas_service import LojaAsaasService
                
                asaas_service = LojaAsaasService()
                resultado_asaas = asaas_service.criar_cobranca_loja(loja, financeiro)
                
                if resultado_asaas.get('success'):
                    print(f"✅ Cobrança Asaas criada: {resultado_asaas.get('payment_id')}")
                    loja._asaas_data = resultado_asaas  # Adicionar dados para retorno
                else:
                    print(f"⚠️ Erro na cobrança Asaas: {resultado_asaas.get('error')}")
                    loja._asaas_error = resultado_asaas.get('error')
                    
            except Exception as e:
                print(f"⚠️ Erro na integração Asaas: {e}")
                loja._asaas_error = str(e)
        
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
