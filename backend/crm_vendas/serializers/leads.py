"""Serializers de leads CRM."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import Contato, Lead


class LeadSerializer(
    UniqueDocumentoPerLojaMixin,
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    unique_documento_fields = ["cpf_cnpj"]
    unique_documento_entidade = "lead"
    conta_info = serializers.SerializerMethodField()
    contato_info = serializers.SerializerMethodField()
    cargo = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_fields = ["telefone"]
    uppercase_fields = ["nome", "empresa", "cidade", "bairro", "uf"]

    class Meta:
        model = Lead
        fields = [
            "id", "nome", "empresa", "cpf_cnpj", "email", "telefone", "origem", "status",
            "valor_estimado", "conta", "conta_info", "contato", "contato_info", "cargo", "observacoes",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_conta_info(self, obj):
        """Retorna informações completas da conta vinculada."""
        if obj.conta:
            return {
                "id": obj.conta.id,
                "nome": obj.conta.nome,
                "razao_social": obj.conta.razao_social,
                "cnpj": obj.conta.cnpj,
                "inscricao_estadual": obj.conta.inscricao_estadual,
                "email": obj.conta.email,
                "telefone": obj.conta.telefone,
                "site": obj.conta.site,
                "cep": obj.conta.cep,
                "logradouro": obj.conta.logradouro,
                "numero": obj.conta.numero,
                "complemento": obj.conta.complemento,
                "bairro": obj.conta.bairro,
                "cidade": obj.conta.cidade,
                "uf": obj.conta.uf,
            }
        return None

    def get_contato_info(self, obj):
        """Retorna informações do contato vinculado."""
        if obj.contato:
            return {
                "id": obj.contato.id,
                "nome": obj.contato.nome,
                "email": obj.contato.email,
                "telefone": obj.contato.telefone,
                "cargo": obj.contato.cargo,
            }
        return None

    def create(self, validated_data):
        cargo = validated_data.pop("cargo", "")
        conta = validated_data.get("conta")
        if conta and not validated_data.get("contato"):
            validated_data["contato"] = self._contato_da_empresa(conta, validated_data, cargo)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        cargo = validated_data.pop("cargo", None)
        if "conta" in validated_data or cargo is not None:
            conta = validated_data.get("conta", instance.conta)
            if conta is None:
                validated_data["contato"] = None
            elif "contato" not in validated_data:
                atual = instance.contato if instance.contato_id and instance.contato.conta_id == conta.id else None
                dados = {
                    "nome": validated_data.get("nome", instance.nome),
                    "email": validated_data.get("email", instance.email),
                    "telefone": validated_data.get("telefone", instance.telefone),
                }
                validated_data["contato"] = self._contato_da_empresa(conta, dados, cargo, atual=atual)
        return super().update(instance, validated_data)

    def _contato_da_empresa(self, conta, dados, cargo, atual=None):
        """Grava a pessoa do lead como contato da empresa. Não apaga contato antigo de outra empresa."""
        nome = (dados.get("nome") or "").strip() or "Contato"
        email = dados.get("email") or None
        telefone = dados.get("telefone") or ""
        if atual is not None:
            atual.nome = nome
            atual.email = email
            atual.telefone = telefone
            if cargo is not None:
                atual.cargo = cargo
            atual.save()
            return atual
        existente = Contato.objects.filter(conta=conta, nome__iexact=nome).first()
        if existente:
            if email:
                existente.email = email
            if telefone:
                existente.telefone = telefone
            if cargo:
                existente.cargo = cargo
            existente.save()
            return existente
        return Contato.objects.create(
            conta=conta,
            nome=nome,
            email=email,
            telefone=telefone,
            cargo=cargo or "",
        )


class LeadListSerializer(CpfCnpjNormalizationMixin, TextNormalizationMixin, serializers.ModelSerializer):
    conta_nome = serializers.CharField(source="conta.nome", read_only=True)
    conta_cnpj = serializers.CharField(source="conta.cnpj", read_only=True)
    conta_razao_social = serializers.CharField(source="conta.razao_social", read_only=True)
    contato_nome = serializers.CharField(source="contato.nome", read_only=True)
    phone_fields = ["telefone"]
    uppercase_fields = ["nome", "empresa", "cidade", "bairro", "uf"]

    class Meta:
        model = Lead
        fields = [
            "id", "nome", "empresa", "cpf_cnpj", "email", "telefone", "origem", "status", "valor_estimado",
            "conta", "conta_nome", "conta_cnpj", "conta_razao_social", "contato", "contato_nome",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "created_at",
        ]
