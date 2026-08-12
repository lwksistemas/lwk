from rest_framework import serializers

from superadmin.models import ContratoPacsLoja, Loja, MaquinaRadiologia


class ContratoPacsLojaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source="loja.nome", read_only=True)
    valor_mensal = serializers.SerializerMethodField()

    class Meta:
        model = ContratoPacsLoja
        fields = [
            "id",
            "loja",
            "loja_nome",
            "dicom_contratado",
            "worklist_contratado",
            "cobranca_dicom_mensal",
            "cobranca_worklist_mensal",
            "valor_mensal",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_valor_mensal(self, obj):
        return str(obj.valor_mensal())


class MaquinaRadiologiaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source="loja.nome", read_only=True)
    loja_slug = serializers.CharField(source="loja.slug", read_only=True)
    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    cpf_cnpj = serializers.CharField(source="loja.cpf_cnpj", read_only=True)

    class Meta:
        model = MaquinaRadiologia
        fields = [
            "id",
            "loja",
            "loja_nome",
            "loja_slug",
            "cpf_cnpj",
            "tipo",
            "tipo_label",
            "nome",
            "ae_title",
            "fabricante",
            "modelo",
            "cobranca_mensal",
            "status",
            "status_label",
            "codigo_vinculo",
            "equipamento_tenant_id",
            "is_active",
            "observacoes",
            "liberada_em",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "codigo_vinculo",
            "equipamento_tenant_id",
            "status",
            "liberada_em",
            "created_at",
            "updated_at",
        ]

    def validate_ae_title(self, value):
        raw = (value or "").strip().upper().replace(" ", "")
        if not raw or len(raw) > 16:
            raise serializers.ValidationError("AE Title obrigatório (máx. 16 caracteres, sem espaço).")
        return raw

    def validate_loja(self, value: Loja):
        slug = (getattr(value.tipo_loja, "slug", "") or "").lower()
        if "radiolog" not in slug:
            raise serializers.ValidationError("Selecione uma loja do tipo Radiologia.")
        return value
