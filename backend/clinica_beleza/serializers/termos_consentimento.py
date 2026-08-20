"""Serializers — biblioteca de termos de consentimento."""
from rest_framework import serializers

from ..models import Procedure, TermoConsentimentoConfig, TermoConsentimentoTemplate
from ..termos_consentimento_service import (
    ProcedimentoJaTemTermo,
    nome_sem_anadem,
    normalizar_secoes,
    vincular_procedimento_ao_termo,
)
from ..models.termos_consentimento import TIPO_INTERATIVO, TIPO_SIMPLES


class TermoConsentimentoTemplateSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    procedimentos = serializers.SerializerMethodField()
    procedimento_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = TermoConsentimentoTemplate
        exclude = ["loja_id"]

    def get_procedimentos(self, obj):
        return [
            {"id": p.id, "nome": p.nome}
            for p in Procedure.objects.filter(termo_template_id=obj.id, is_active=True).order_by("nome")
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        procs = data.get("procedimentos") or []
        data["procedimento_id"] = procs[0]["id"] if len(procs) == 1 else None
        return data

    def validate_nome(self, value):
        nome = nome_sem_anadem(value)
        if not nome:
            raise serializers.ValidationError("Informe o nome do termo.")
        return nome

    def validate(self, attrs):
        tipo = attrs.get("tipo") or getattr(self.instance, "tipo", TIPO_SIMPLES)
        if tipo == TIPO_INTERATIVO:
            secoes = normalizar_secoes(attrs.get("secoes", getattr(self.instance, "secoes", [])))
            if not secoes:
                raise serializers.ValidationError(
                    {"secoes": "Inclua pelo menos uma seção no TCLE Interativo."},
                )
            attrs["secoes"] = secoes
        if not self.instance and not attrs.get("procedimento_id"):
            raise serializers.ValidationError(
                {"procedimento_id": "Selecione o procedimento deste termo."},
            )
        return attrs

    def create(self, validated_data):
        procedure_id = validated_data.pop("procedimento_id", None)
        obj = super().create(validated_data)
        self._aplicar_vinculo(obj, procedure_id)
        return obj

    def update(self, instance, validated_data):
        procedure_id = validated_data.pop("procedimento_id", serializers.empty)
        obj = super().update(instance, validated_data)
        if procedure_id is not serializers.empty:
            self._aplicar_vinculo(obj, procedure_id)
        return obj

    def _aplicar_vinculo(self, obj, procedure_id):
        try:
            vincular_procedimento_ao_termo(obj, procedure_id)
        except ProcedimentoJaTemTermo as exc:
            raise serializers.ValidationError({"procedimento_id": str(exc)}) from exc
        except ValueError as exc:
            raise serializers.ValidationError({"procedimento_id": str(exc)}) from exc
