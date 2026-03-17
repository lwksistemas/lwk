"""
Serviço para criação de lojas
Extrai lógica complexa do LojaCreateSerializer
"""
import logging
import secrets
import string
from typing import Dict, Tuple
from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework import serializers

logger = logging.getLogger(__name__)


class LojaCreationService:
    """
    Serviço responsável pela criação de lojas e seus componentes
    """
    
    @staticmethod
    def gerar_senha_provisoria(tamanho: int = 8) -> str:
        """
        Gera senha provisória segura
        
        Args:
            tamanho: Tamanho da senha
            
        Returns:
            Senha gerada
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        return ''.join(secrets.choice(alphabet) for _ in range(tamanho))
    
    @staticmethod
    def processar_nome_completo(nome_completo: str) -> Tuple[str, str]:
        """
        Divide nome completo em first_name e last_name
        
        Args:
            nome_completo: Nome completo do usuário
            
        Returns:
            Tupla (first_name, last_name)
        """
        parts = nome_completo.split(None, 1) if nome_completo else []
        first_name = parts[0] if parts else ''
        last_name = parts[1] if len(parts) > 1 else ''
        return first_name, last_name
    
    @staticmethod
    def criar_ou_atualizar_owner(
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str
    ) -> User:
        """
        Cria ou atualiza usuário owner da loja
        
        Args:
            username: Nome de usuário
            email: Email do usuário
            password: Senha do usuário
            first_name: Primeiro nome
            last_name: Sobrenome
            
        Returns:
            Objeto User criado ou atualizado
            
        Raises:
            serializers.ValidationError: Se houver erro na criação
        """
        # Verificar se usuário já existe
        owner = User.objects.filter(username=username).first()
        
        if owner:
            # Verificar se já é dono de outra loja
            if owner.lojas_owned.exists():
                raise serializers.ValidationError({
                    'owner_username': f'O usuário "{username}" já é dono de outra loja. Use outro nome de usuário.'
                })
            
            # Usuário órfão: reutilizar e atualizar dados
            owner.email = email
            owner.first_name = first_name
            owner.last_name = last_name
            owner.set_password(password)
            owner.is_staff = False
            owner.save()
            
            logger.info(f"Usuário órfão reutilizado: {username}")
            return owner
        
        # Criar novo usuário
        try:
            owner = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=False
            )
            logger.info(f"Novo usuário criado: {username}")
            return owner
            
        except IntegrityError as e:
            if 'username' in str(e) or 'auth_user_username_key' in str(e):
                raise serializers.ValidationError({
                    'owner_username': (
                        f'Já existe um usuário com o login "{username}". '
                        'Para liberar esse login (usuário órfão), no servidor execute: '
                        f'python manage.py verificar_usuario {username} --remover '
                        'ou python manage.py limpar_usuarios_orfaos --confirmar. '
                        'Veja docs/LIMPAR_USUARIOS_ORFAOS.md. Ou use outro nome de usuário.'
                    )
                })
            
            if 'email' in str(e) or 'auth_user_email_key' in str(e):
                raise serializers.ValidationError({
                    'owner_email': f'Já existe um usuário com o e-mail "{email}". Use outro e-mail ou limpe usuários órfãos.'
                })
            
            raise serializers.ValidationError({
                'owner_username': 'Erro ao criar usuário (dados duplicados). Use outro nome de usuário ou e-mail.'
            })
    
    @staticmethod
    def validar_e_processar_slug(slug_enviado: str) -> str:
        """
        Valida e processa slug da loja.
        Slug fixo: CPF/CNPJ (apenas dígitos) — ex.: 41449198000172
        
        Args:
            slug_enviado: Slug enviado (dígitos do CPF/CNPJ ou texto)
            
        Returns:
            Slug processado e validado
            
        Raises:
            serializers.ValidationError: Se slug for inválido ou duplicado
        """
        import re
        from django.utils.text import slugify
        from superadmin.models import Loja
        
        if not slug_enviado:
            return None
        
        s = str(slug_enviado).strip()
        # Se for só dígitos (CPF/CNPJ), manter como está
        if re.match(r'^\d{11,14}$', s):
            slug_sanitizado = s
        else:
            slug_sanitizado = slugify(s) or None
        
        if not slug_sanitizado:
            return None
        
        # Verificar se já existe
        if Loja.objects.filter(slug__iexact=slug_sanitizado).exists():
            raise serializers.ValidationError({
                'slug': f'Já existe uma loja com o CPF/CNPJ "{slug_sanitizado}".'
            })
        
        # Verificar database_name único (loja_41449198000172)
        db_slug = slug_sanitizado.replace('-', '_')
        proposed_db_name = f"loja_{db_slug}"
        if Loja.objects.filter(database_name=proposed_db_name).exists():
            raise serializers.ValidationError({
                'slug': 'Já existe uma loja com este CPF/CNPJ.'
            })
        
        return slug_sanitizado
    
    @staticmethod
    def calcular_valor_mensalidade(loja) -> float:
        """
        Calcula valor da mensalidade baseado no tipo de assinatura
        
        Args:
            loja: Objeto Loja
            
        Returns:
            Valor da mensalidade
        """
        if loja.tipo_assinatura == 'anual':
            return loja.plano.preco_anual / 12 if loja.plano.preco_anual else loja.plano.preco_mensal
        return loja.plano.preco_mensal
    
    @staticmethod
    def calcular_datas_vencimento(dia_vencimento: int) -> Tuple:
        """
        Calcula datas de vencimento para primeiro boleto e próxima cobrança
        
        Args:
            dia_vencimento: Dia do mês para vencimento
            
        Returns:
            Tupla (primeiro_vencimento, proxima_cobranca)
        """
        from datetime import date, timedelta
        from calendar import monthrange
        
        hoje = date.today()
        
        # Primeiro boleto: 3 dias a partir de hoje
        primeiro_vencimento = hoje + timedelta(days=3)
        
        # Próxima cobrança: dia fixo no próximo mês
        if hoje.month == 12:
            proximo_mes = 1
            proximo_ano = hoje.year + 1
        else:
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year
        
        # Ajustar dia se o mês não tiver esse dia
        ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
        dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
        
        return primeiro_vencimento, primeiro_vencimento
    
    @staticmethod
    def log_criacao_loja(loja, owner, senha_provisoria: str):
        """
        Registra log da criação da loja
        
        Args:
            loja: Objeto Loja criado
            owner: Objeto User do proprietário
            senha_provisoria: Senha provisória gerada
        """
        print(f"\n{'='*80}")
        print(f"✅ Loja criada: {loja.nome}")
        print(f"   - Provedor boleto preferido: {getattr(loja, 'provedor_boleto_preferido', 'asaas')}")
        print(f"   - ID: {loja.id}")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Database name: {loja.database_name}")
        print(f"   - Owner: {owner.username} ({owner.email})")
        print(f"   - Senha provisória: {senha_provisoria[:3]}***")
        print(f"   - Senha foi alterada: {loja.senha_foi_alterada}")
        print(f"{'='*80}\n")
        
        logger.info(
            "Loja criada com sucesso: %s (owner: %s). Senha será enviada após confirmação do pagamento.",
            loja.slug,
            owner.email,
        )
