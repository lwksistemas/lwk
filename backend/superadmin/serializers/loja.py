"""Serializers de lojas."""
import logging
import traceback

from rest_framework import serializers

from core.serializer_mixins import CpfCnpjNormalizationMixin, TextNormalizationMixin, UniqueDocumentoPerLojaMixin

from ..models import Loja
from .financeiro import FinanceiroLojaSerializer

logger = logging.getLogger(__name__)

class LojaSerializer(
    UniqueDocumentoPerLojaMixin,
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    unique_documento_fields = ["cpf_cnpj"]
    unique_documento_global = True
    tipo_loja_nome = serializers.CharField(source="tipo_loja.nome", read_only=True)
    plano_nome = serializers.CharField(source="plano.nome", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    owner_full_name = serializers.SerializerMethodField(read_only=True)
    owner_email_edit = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    owner_username_edit = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=150)
    owner_name_edit = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=200)
    financeiro = FinanceiroLojaSerializer(read_only=True)
    tipo_assinatura_display = serializers.CharField(source="get_tipo_assinatura_display", read_only=True)
    uppercase_fields = ["nome", "cidade", "bairro"]
    phone_fields = ["owner_telefone"]
    cpf_cnpj_fields = ["cpf_cnpj"]

    class Meta:
        model = Loja
        fields = "__all__"
        read_only_fields = ["database_name", "database_created", "login_page_url", "senha_provisoria", "owner", "owner_telefone"]

    def update(self, instance, validated_data):
        new_email = validated_data.pop("owner_email_edit", None)
        new_username = validated_data.pop("owner_username_edit", None)
        new_name = validated_data.pop("owner_name_edit", None)
        instance = super().update(instance, validated_data)
        if instance.owner:
            update_fields = []
            if new_email and new_email.strip():
                instance.owner.email = new_email.strip()
                update_fields.append("email")
            if new_username and new_username.strip():
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if User.objects.filter(username=new_username.strip()).exclude(id=instance.owner.id).exists():
                    raise serializers.ValidationError({"owner_username_edit": "Este nome de usuário já está em uso."})
                instance.owner.username = new_username.strip()
                update_fields.append("username")
            if new_name is not None and new_name.strip():
                parts = new_name.strip().split(" ", 1)
                instance.owner.first_name = parts[0]
                instance.owner.last_name = parts[1] if len(parts) > 1 else ""
                update_fields.extend(["first_name", "last_name"])
            if update_fields:
                instance.owner.save(update_fields=update_fields)
            try:
                from crm_vendas.vendedor_admin_service import sincronizar_vendedor_admin_owner
                sincronizar_vendedor_admin_owner(instance, instance.owner)
            except Exception:
                logger.exception("Falha ao sincronizar vendedor admin após editar loja %s", instance.slug)
        return instance

    def get_owner_full_name(self, obj):
        if obj.owner:
            full = f"{obj.owner.first_name or ''} {obj.owner.last_name or ''}".strip()
            return full or obj.owner.username
        return ""


class LojaCreateSerializer(
    UniqueDocumentoPerLojaMixin,
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    """Serializer para criar loja com banco isolado"""

    unique_documento_fields = ["cpf_cnpj"]
    unique_documento_global = True
    owner_full_name = serializers.CharField(write_only=True, required=True, help_text="Nome completo do administrador")
    owner_username = serializers.CharField(write_only=True, help_text="Nome de acesso (login) à loja")
    owner_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    owner_email = serializers.EmailField(write_only=True)
    owner_telefone = serializers.CharField(write_only=True, required=False, allow_blank=True, help_text="Telefone do administrador")
    dia_vencimento = serializers.IntegerField(write_only=True, default=10, min_value=1, max_value=28)
    uppercase_fields = ["nome", "cidade", "bairro"]
    phone_fields = ["owner_telefone"]
    cpf_cnpj_fields = ["cpf_cnpj"]

    class Meta:
        model = Loja
        fields = [
            "nome", "slug", "descricao", "cpf_cnpj",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "tipo_loja", "plano", "tipo_assinatura", "provedor_boleto_preferido",
            "forma_pagamento_preferida",  # ✅ NOVO: Forma de pagamento
            "owner_full_name", "owner_username", "owner_password", "owner_email", "owner_telefone", "dia_vencimento",
            "logo", "cor_primaria", "cor_secundaria", "dominio_customizado",
            "atalho", "subdomain",  # ✅ NOVO v1421: Sistema híbrido de acesso
        ]

    @staticmethod
    def _tentar_enriquecer_cep_attrs(attrs: dict, cep_raw: str) -> str:
        """Se CEP inválido, tenta ViaCEP e devolve o CEP atualizado."""
        from core.cep_utils import cep_digitos_validos
        from nfse_integration.nfse_geo import enriquecer_endereco_por_cep

        if not cep_raw or cep_digitos_validos(cep_raw):
            return cep_raw
        endereco = {
            "cep": cep_raw,
            "logradouro": (attrs.get("logradouro") or "").strip(),
            "bairro": (attrs.get("bairro") or "").strip(),
            "cidade": (attrs.get("cidade") or "").strip(),
            "uf": (attrs.get("uf") or "").strip(),
        }
        if not enriquecer_endereco_por_cep(endereco):
            return cep_raw
        attrs["cep"] = endereco["cep"]
        for campo in ("logradouro", "bairro", "cidade", "uf"):
            if (endereco.get(campo) or "").strip():
                attrs[campo] = endereco[campo]
        return attrs["cep"]

    @staticmethod
    def _aplicar_numero_complemento_attrs(attrs: dict) -> None:
        from nfse_integration.nfse_geo import normalizar_numero_complemento_endereco

        numero_norm, compl_norm = normalizar_numero_complemento_endereco(
            attrs.get("numero") or "",
            attrs.get("complemento") or "",
        )
        if numero_norm:
            attrs["numero"] = numero_norm
        if compl_norm:
            attrs["complemento"] = compl_norm

    @staticmethod
    def _exigir_cep_valido_attrs(attrs: dict, cep_raw: str) -> None:
        from core.cep_utils import cep_digitos_validos, normalizar_cep

        if cep_raw:
            if not cep_digitos_validos(cep_raw):
                raise serializers.ValidationError(
                    {"cep": "Informe um CEP válido com 8 dígitos (ex.: 14026-583)."}
                )
            attrs["cep"] = normalizar_cep(cep_raw)
            return
        if any((attrs.get(k) or "").strip() for k in ("logradouro", "cidade", "uf", "bairro")):
            raise serializers.ValidationError(
                {"cep": "CEP é obrigatório quando o endereço é informado."}
            )
        raise serializers.ValidationError(
            {"cep": "CEP é obrigatório para emissão da nota fiscal após o pagamento."}
        )

    def _validate_cep_enriquecer(self, attrs: dict) -> dict:
        """Tenta enriquecer CEP e normaliza campos de endereço. Retorna attrs modificado."""
        cep_raw = (attrs.get("cep") or "").strip()
        cep_raw = self._tentar_enriquecer_cep_attrs(attrs, cep_raw)
        self._aplicar_numero_complemento_attrs(attrs)
        self._exigir_cep_valido_attrs(attrs, cep_raw)
        return attrs

    def validate(self, attrs):
        attrs = self._validate_cep_enriquecer(attrs)
        return super().validate(attrs)

    def create(self, validated_data):
        """Cria loja usando services para separar responsabilidades
        ✅ REFATORADO v769: Reduzido de 300+ para ~80 linhas usando services
        """
        from ..services import (
            DatabaseSchemaService,
            FinanceiroService,
            LojaCreationService,
            ProfessionalService,
        )

        try:
            # 1. EXTRAIR E PROCESSAR DADOS DO OWNER
            owner_full_name = (validated_data.pop("owner_full_name", "") or "").strip()
            owner_username = validated_data.pop("owner_username")
            owner_password = validated_data.pop("owner_password", None)
            owner_email = validated_data.pop("owner_email")
            owner_telefone = (validated_data.pop("owner_telefone", "") or "").strip()
            dia_vencimento = validated_data.pop("dia_vencimento", 10)

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
                last_name=last_name,
            )

            # 3. SLUG FIXO: CPF/CNPJ (apenas dígitos) — URL: /loja/41449198000172/login
            slug_enviado = validated_data.pop("slug", None)
            cpf_cnpj = (validated_data.get("cpf_cnpj") or "").strip()
            cpf_cnpj_digits = "".join(c for c in cpf_cnpj if c.isdigit()) if cpf_cnpj else ""
            # Prioridade: slug enviado, ou CPF/CNPJ (11+ dígitos), ou slug enviado vazio
            if slug_enviado and str(slug_enviado).strip():
                slug_candidato = str(slug_enviado).strip()
            elif len(cpf_cnpj_digits) >= 11:
                slug_candidato = cpf_cnpj_digits
            else:
                slug_candidato = slug_enviado
            slug_validado = LojaCreationService.validar_e_processar_slug(slug_candidato)
            if slug_validado:
                validated_data["slug"] = slug_validado

            # 4. PREPARAR DADOS DA LOJA
            validated_data["owner"] = owner
            validated_data["owner_telefone"] = owner_telefone
            validated_data["senha_provisoria"] = owner_password
            validated_data["senha_foi_alterada"] = False
            validated_data.setdefault("provedor_boleto_preferido", "asaas")

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
                    f"Não foi possível configurar o banco de dados da loja: {e!s}. "
                    "Tente novamente ou entre em contato com o suporte.",
                )

            # 7. CRIAR FINANCEIRO (+ cobrança Asaas/MP via signal post_save)
            try:
                financeiro = FinanceiroService.criar_financeiro_loja(loja, dia_vencimento)
            except Exception as e:
                logger.error(f"Erro ao criar financeiro: {e}")
                raise

            # Rede de segurança: se o signal não gerou boleto, tenta criar aqui.
            try:
                financeiro.refresh_from_db()
                if not (financeiro.asaas_payment_id or financeiro.mercadopago_payment_id):
                    from superadmin.cobranca_service import CobrancaService

                    result = CobrancaService().criar_cobranca(loja, financeiro)
                    if not result.get("success"):
                        logger.error(
                            "Cobrança não criada no cadastro da loja %s: %s",
                            loja.slug,
                            result.get("error"),
                        )
            except Exception as e:
                logger.exception("Falha ao garantir cobrança no cadastro da loja %s: %s", loja.slug, e)

            # 8. CRIAR PROFISSIONAL/FUNCIONÁRIO ADMIN
            # Re-fetch loja para garantir database_created atualizado após configurar_schema
            loja.refresh_from_db()
            try:
                ok = ProfessionalService.criar_profissional_por_tipo(loja, owner, owner_telefone)
                if not ok:
                    logger.warning(
                        "ProfessionalService não criou profissional/vendedor para loja=%s (owner=%s). "
                        "Execute: python manage.py criar_funcionarios_admins para corrigir.",
                        loja.slug, owner.email,
                    )
            except Exception as e:
                logger.warning(
                    "Erro ao criar profissional/funcionário para loja=%s: %s. "
                    "Execute: python manage.py criar_funcionarios_admins para corrigir.",
                    loja.slug, e,
                )
                # Não falhar a criação da loja

            logger.info(
                "Loja criada com sucesso: %s (owner: %s). Senha será enviada após confirmação do pagamento.",
                loja.slug,
                owner_email,
            )

            return loja

        except Exception as e:
            logger.error(f"Erro ao criar loja: {e}")
            logger.error(traceback.format_exc())
            raise serializers.ValidationError(f"Erro ao criar loja: {e!s}")

    def to_representation(self, instance):
        """Inclui boleto/PIX na resposta do cadastro público (SucessoCadastro)."""
        data = super().to_representation(instance)
        try:
            fin = getattr(instance, "financeiro", None)
            if fin is None:
                from superadmin.models import FinanceiroLoja

                fin = FinanceiroLoja.objects.filter(loja_id=instance.pk).first()
            if fin:
                data["boleto_url"] = fin.boleto_url or ""
                data["pix_qr_code"] = fin.pix_qr_code or ""
                data["pix_copy_paste"] = fin.pix_copy_paste or ""
        except Exception:
            logger.exception(
                "to_representation: falha ao anexar boleto da loja %s",
                getattr(instance, "slug", "?"),
            )
        return data


