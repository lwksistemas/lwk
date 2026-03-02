"""
Serviço de validação centralizado para o módulo superadmin
Consolida validações comuns em um único lugar
"""
import re
from typing import Dict, List, Optional, Tuple
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class ValidationService:
    """
    Serviço centralizado para validações do superadmin
    """
    
    @staticmethod
    def validar_slug(slug: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato de slug
        
        Args:
            slug: String a ser validada
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not slug:
            return False, "Slug não pode ser vazio"
        
        if not re.match(r'^[a-z0-9-]+$', slug):
            return False, "Slug deve conter apenas letras minúsculas, números e hífens"
        
        if slug.startswith('-') or slug.endswith('-'):
            return False, "Slug não pode começar ou terminar com hífen"
        
        if '--' in slug:
            return False, "Slug não pode conter hífens consecutivos"
        
        return True, None
    
    @staticmethod
    def validar_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato de email
        
        Args:
            email: String a ser validada
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not email:
            return False, "Email não pode ser vazio"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Formato de email inválido"
        
        return True, None
    
    @staticmethod
    def validar_senha(senha: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
        """
        Valida força da senha
        
        Args:
            senha: Senha a ser validada
            min_length: Tamanho mínimo da senha
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not senha:
            return False, "Senha não pode ser vazia"
        
        if len(senha) < min_length:
            return False, f"Senha deve ter no mínimo {min_length} caracteres"
        
        return True, None
    
    @staticmethod
    def validar_username_disponivel(username: str, exclude_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Verifica se username está disponível
        
        Args:
            username: Username a ser verificado
            exclude_id: ID do usuário a ser excluído da verificação (para edição)
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not username:
            return False, "Username não pode ser vazio"
        
        query = User.objects.filter(username=username)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        if query.exists():
            return False, f"Username '{username}' já está em uso"
        
        return True, None
    
    @staticmethod
    def validar_dados_loja(data: Dict) -> List[str]:
        """
        Valida dados completos de uma loja
        
        Args:
            data: Dicionário com dados da loja
            
        Returns:
            Lista de erros (vazia se válido)
        """
        erros = []
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome', 'slug', 'tipo_loja', 'plano']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                erros.append(f"Campo '{campo}' é obrigatório")
        
        # Validar slug
        if data.get('slug'):
            is_valid, error = ValidationService.validar_slug(data['slug'])
            if not is_valid:
                erros.append(error)
        
        # Validar email do proprietário
        if data.get('owner_email'):
            is_valid, error = ValidationService.validar_email(data['owner_email'])
            if not is_valid:
                erros.append(f"Email do proprietário: {error}")
        
        return erros
    
    @staticmethod
    def validar_permissoes_superadmin(user) -> Tuple[bool, Optional[str]]:
        """
        Verifica se usuário tem permissões de superadmin
        
        Args:
            user: Objeto User do Django
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not user or not user.is_authenticated:
            return False, "Usuário não autenticado"
        
        if not user.is_superuser:
            return False, "Usuário não tem permissões de superadmin"
        
        return True, None
    
    @staticmethod
    def validar_dados_pagamento(data: Dict) -> List[str]:
        """
        Valida dados de pagamento
        
        Args:
            data: Dicionário com dados do pagamento
            
        Returns:
            Lista de erros (vazia se válido)
        """
        erros = []
        
        # Validar valor
        if 'valor' in data:
            try:
                valor = float(data['valor'])
                if valor <= 0:
                    erros.append("Valor deve ser maior que zero")
            except (ValueError, TypeError):
                erros.append("Valor inválido")
        
        # Validar método de pagamento
        metodos_validos = ['boleto', 'pix', 'credit_card']
        if data.get('metodo') and data['metodo'] not in metodos_validos:
            erros.append(f"Método de pagamento inválido. Opções: {', '.join(metodos_validos)}")
        
        return erros
