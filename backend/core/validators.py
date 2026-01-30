"""
✅ VALIDADORES CUSTOMIZADOS
Validações de segurança e integridade de dados
"""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re
import logging

logger = logging.getLogger(__name__)


# ============================================
# VALIDADOR DE SLUG
# ============================================

SLUG_REGEX = re.compile(r'^[a-z0-9-]+$')

def validate_store_slug(value):
    """
    Valida formato do slug da loja
    
    Regras:
    - Apenas letras minúsculas, números e hífens
    - Mínimo 3 caracteres
    - Máximo 50 caracteres
    - Não pode começar ou terminar com hífen
    - Não pode ter hífens consecutivos
    """
    if not value:
        raise ValidationError("Slug não pode ser vazio")
    
    if len(value) < 3:
        raise ValidationError("Slug deve ter no mínimo 3 caracteres")
    
    if len(value) > 50:
        raise ValidationError("Slug deve ter no máximo 50 caracteres")
    
    if not SLUG_REGEX.match(value):
        raise ValidationError(
            "Slug deve conter apenas letras minúsculas, números e hífens"
        )
    
    if value.startswith('-') or value.endswith('-'):
        raise ValidationError("Slug não pode começar ou terminar com hífen")
    
    if '--' in value:
        raise ValidationError("Slug não pode conter hífens consecutivos")
    
    # Slugs reservados
    reserved_slugs = [
        'admin', 'api', 'static', 'media', 'superadmin', 'suporte',
        'login', 'logout', 'register', 'dashboard', 'auth', 'docs',
        'swagger', 'redoc', 'health', 'status', 'debug'
    ]
    
    if value in reserved_slugs:
        raise ValidationError(f"Slug '{value}' é reservado e não pode ser usado")
    
    return value


# Validador Django para usar em models
slug_validator = RegexValidator(
    regex=SLUG_REGEX,
    message="Slug deve conter apenas letras minúsculas, números e hífens",
    code='invalid_slug'
)


# ============================================
# VALIDADOR DE LOJA_ID
# ============================================

def validate_loja_id_context(loja_id):
    """
    Valida que loja_id corresponde ao contexto atual
    
    Uso em views/serializers:
        validate_loja_id_context(obj.loja_id)
    """
    from tenants.middleware import get_current_loja_id
    
    current_loja_id = get_current_loja_id()
    
    if not current_loja_id:
        raise ValidationError("Contexto de loja não definido")
    
    if loja_id != current_loja_id:
        logger.critical(
            f"🚨 VIOLAÇÃO DE SEGURANÇA: Tentativa de acessar loja_id={loja_id} "
            f"mas contexto é loja_id={current_loja_id}"
        )
        raise ValidationError(
            "Você não tem permissão para acessar dados de outra loja"
        )
    
    return loja_id


# ============================================
# VALIDADOR DE SENHA
# ============================================

def validate_password_strength(password):
    """
    Valida força da senha
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    """
    if len(password) < 8:
        raise ValidationError("Senha deve ter no mínimo 8 caracteres")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Senha deve conter pelo menos 1 letra maiúscula")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Senha deve conter pelo menos 1 letra minúscula")
    
    if not re.search(r'\d', password):
        raise ValidationError("Senha deve conter pelo menos 1 número")
    
    # Senhas comuns
    common_passwords = [
        '12345678', 'password', 'senha123', 'admin123',
        'qwerty123', '123456789', 'abc123456'
    ]
    
    if password.lower() in common_passwords:
        raise ValidationError("Senha muito comum. Escolha uma senha mais forte.")
    
    return password


# ============================================
# VALIDADOR DE CPF
# ============================================

def validate_cpf(cpf):
    """
    Valida CPF brasileiro
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar se tem 11 dígitos
    if len(cpf) != 11:
        raise ValidationError("CPF deve ter 11 dígitos")
    
    # Verificar se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido")
    
    # Validar dígitos verificadores
    def calculate_digit(cpf_partial):
        total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, range(len(cpf_partial) + 1, 1, -1)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # Validar primeiro dígito
    if int(cpf[9]) != calculate_digit(cpf[:9]):
        raise ValidationError("CPF inválido")
    
    # Validar segundo dígito
    if int(cpf[10]) != calculate_digit(cpf[:10]):
        raise ValidationError("CPF inválido")
    
    return cpf


# ============================================
# VALIDADOR DE CNPJ
# ============================================

def validate_cnpj(cnpj):
    """
    Valida CNPJ brasileiro
    """
    # Remover caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verificar se tem 14 dígitos
    if len(cnpj) != 14:
        raise ValidationError("CNPJ deve ter 14 dígitos")
    
    # Verificar se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        raise ValidationError("CNPJ inválido")
    
    # Validar dígitos verificadores
    def calculate_digit(cnpj_partial, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # Pesos para validação
    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Validar primeiro dígito
    if int(cnpj[12]) != calculate_digit(cnpj[:12], weights_first):
        raise ValidationError("CNPJ inválido")
    
    # Validar segundo dígito
    if int(cnpj[13]) != calculate_digit(cnpj[:13], weights_second):
        raise ValidationError("CNPJ inválido")
    
    return cnpj


# ============================================
# VALIDADOR DE TELEFONE
# ============================================

def validate_phone(phone):
    """
    Valida telefone brasileiro
    Aceita: (11) 98765-4321 ou 11987654321
    """
    # Remover caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Verificar tamanho (10 ou 11 dígitos)
    if len(phone) not in [10, 11]:
        raise ValidationError("Telefone deve ter 10 ou 11 dígitos")
    
    # Verificar DDD válido (11-99)
    ddd = int(phone[:2])
    if ddd < 11 or ddd > 99:
        raise ValidationError("DDD inválido")
    
    return phone


# ============================================
# VALIDADOR DE EMAIL
# ============================================

def validate_email_domain(email):
    """
    Valida domínio do email (bloqueia domínios temporários)
    """
    blocked_domains = [
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'throwaway.email', 'mailinator.com', 'trashmail.com'
    ]
    
    domain = email.split('@')[-1].lower()
    
    if domain in blocked_domains:
        raise ValidationError(
            "Email temporário não é permitido. Use um email permanente."
        )
    
    return email


# ============================================
# VALIDADOR DE VALOR MONETÁRIO
# ============================================

def validate_positive_decimal(value):
    """
    Valida que valor decimal é positivo
    """
    if value < 0:
        raise ValidationError("Valor não pode ser negativo")
    
    return value


def validate_price_range(value, min_price=0, max_price=1000000):
    """
    Valida que preço está dentro de um range aceitável
    """
    if value < min_price:
        raise ValidationError(f"Preço não pode ser menor que R$ {min_price}")
    
    if value > max_price:
        raise ValidationError(f"Preço não pode ser maior que R$ {max_price}")
    
    return value


# ============================================
# VALIDADOR DE DATA
# ============================================

def validate_future_date(date):
    """
    Valida que data está no futuro
    """
    from django.utils import timezone
    
    if date < timezone.now().date():
        raise ValidationError("Data deve estar no futuro")
    
    return date


def validate_business_hours(time):
    """
    Valida que horário está dentro do horário comercial (6h-23h)
    """
    if time.hour < 6 or time.hour >= 23:
        raise ValidationError("Horário deve estar entre 06:00 e 23:00")
    
    return time
