"""Serializers — biblioteca de termos de consentimento."""
from rest_framework import serializers

from ..models import Procedure, TermoConsentimentoConfig, TermoConsentimentoTemplate
from ..termos_consentimento_service import nome_sem_anadem, normalizar_secoes
from ..models.termos_consentimento import TIPO_INTERATIVO, TIPO_SIMPLES


class TermoConsentimentoTemplateSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    procedimentos = serializers.SerializerMethodField()

    class Meta:
        model = TermoConsentimentoTemplate
        exclude = ["loja_id"]

    def get_procedimentos(self, obj):
        return [
            {"id": p.id, "nome": p.nome}
            for p in Procedure.objects.filter(termo_template_id=obj.id, is_active=True).order_by("nome")
        ]

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
        return attrs


class TermoConsentimentoConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermoConsentimentoConfig
        fields = ["pdf_cabecalho"]
