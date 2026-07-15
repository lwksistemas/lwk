from rest_framework import serializers

from core.serializer_mixins import (
    CpfNormalizationMixin,
    TenantQuerysetMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from clinica_beleza.bloqueio_utils import bloqueio_datetime_range, split_datetime_range

from .models import (
    Agendamento,
    BloqueioHorario,
    CategoriaServico,
    Cliente,
    HorarioTrabalhoProfissional,
    Profissional,
    Servico,
)


class ClienteSerializer(
    TenantQuerysetMixin,
    UniqueDocumentoPerLojaMixin,
    CpfNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    """Alinhado ao PatientSerializer da clínica (aliases phone/birth_date/notes)."""

    unique_documento_fields = ["cpf"]
    unique_documento_entidade = "cliente"
    unique_documento_apenas_ativos = True
    phone_fields = ["phone", "telefone"]
    uppercase_fields = ["name", "nome", "cidade", "estado", "logradouro", "bairro", "endereco"]

    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"],
    )

    class Meta:
        model = Cliente
        exclude = ["loja_id"]
        extra_kwargs = {
            "nome": {"required": True},
            "telefone": {"required": False, "allow_blank": True, "default": ""},
            "email": {"required": False, "allow_blank": True, "allow_null": True},
            "cpf": {"required": False, "allow_blank": True, "allow_null": True},
            "data_nascimento": {"required": False, "allow_null": True},
            "endereco": {"required": False, "allow_blank": True, "default": ""},
            "cidade": {"required": False, "allow_blank": True, "default": ""},
            "estado": {"required": False, "allow_blank": True, "default": ""},
            "observacoes": {"required": False, "allow_blank": True, "default": ""},
            "allow_whatsapp": {"required": False, "default": True},
            "foto_url": {"required": False, "allow_blank": True, "default": ""},
            "cep": {"required": False, "allow_blank": True, "default": ""},
            "logradouro": {"required": False, "allow_blank": True, "default": ""},
            "numero": {"required": False, "allow_blank": True, "default": ""},
            "complemento": {"required": False, "allow_blank": True, "default": ""},
            "bairro": {"required": False, "allow_blank": True, "default": ""},
        }

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if data.get("birth_date") and not data.get("data_nascimento"):
            data["data_nascimento"] = data.get("birth_date")
        if data.get("notes") is not None and data.get("observacoes") is None:
            data["observacoes"] = data.get("notes")
        if data.get("name") and not data.get("nome"):
            data["nome"] = data.get("name")
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["phone"] = instance.telefone or ""
        data["birth_date"] = instance.data_nascimento.isoformat() if instance.data_nascimento else None
        data["notes"] = instance.observacoes or ""
        data["name"] = instance.nome
        return data

    def _strip_aliases(self, validated_data):
        """Remove aliases EN que não existem no model (phone/birth_date/name/notes)."""
        phone = validated_data.pop("phone", None)
        if phone is not None and not validated_data.get("telefone"):
            validated_data["telefone"] = phone or ""
        birth = validated_data.pop("birth_date", serializers.empty)
        if birth is not serializers.empty and validated_data.get("data_nascimento") is None:
            validated_data["data_nascimento"] = birth
        name = validated_data.pop("name", None)
        if name and not validated_data.get("nome"):
            validated_data["nome"] = name
        notes = validated_data.pop("notes", serializers.empty)
        if notes is not serializers.empty and not validated_data.get("observacoes"):
            validated_data["observacoes"] = notes or ""
        return validated_data

    def create(self, validated_data):
        return super().create(self._strip_aliases(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._strip_aliases(validated_data))


class ProfissionalSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome", "especialidade"]

    class Meta:
        model = Profissional
        exclude = ["loja_id"]


class ServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome", "categoria"]

    class Meta:
        model = Servico
        exclude = ["loja_id"]


class CategoriaServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome"]

    class Meta:
        model = CategoriaServico
        exclude = ["loja_id"]
        read_only_fields = ["created_at", "updated_at"]


class HorarioTrabalhoProfissionalSerializer(serializers.ModelSerializer):
    dia_semana_display = serializers.CharField(source="get_dia_semana_display", read_only=True)
    # Alias EN para reutilizar ModalHorariosTrabalho da clínica
    professional = serializers.IntegerField(source="profissional_id", read_only=True)

    class Meta:
        model = HorarioTrabalhoProfissional
        fields = [
            "id",
            "profissional",
            "professional",
            "dia_semana",
            "dia_semana_display",
            "hora_entrada",
            "hora_saida",
            "intervalo_inicio",
            "intervalo_fim",
            "ativo",
        ]
        read_only_fields = ["profissional", "professional"]


class AgendamentoSerializer(TenantQuerysetMixin, serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)
    profissional_nome = serializers.SerializerMethodField()
    servico_nome = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    def get_profissional_nome(self, obj):
        return obj.profissional.nome if obj.profissional_id else ""

    def get_servico_nome(self, obj):
        return obj.servico.nome if obj.servico_id else ""

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset("cliente", Cliente.objects.filter(is_active=True))
        self.bind_tenant_queryset("profissional", Profissional.objects.filter(is_active=True))
        self.bind_tenant_queryset("servico", Servico.objects.filter(is_active=True))

    class Meta:
        model = Agendamento
        exclude = ["loja_id"]
        read_only_fields = ["created_at", "updated_at"]


class BloqueioHorarioSerializer(serializers.ModelSerializer):
    """API alinhada à clínica: data_inicio/fim como datetime ISO; aceita professional ou profissional."""

    professional = serializers.IntegerField(required=False, allow_null=True)
    professional_name = serializers.SerializerMethodField()
    data_inicio = serializers.DateTimeField()
    data_fim = serializers.DateTimeField()

    class Meta:
        model = BloqueioHorario
        fields = [
            "id",
            "professional",
            "professional_name",
            "data_inicio",
            "data_fim",
            "motivo",
            "observacoes",
            "criado_em",
        ]
        read_only_fields = ["criado_em"]

    def get_professional_name(self, obj):
        return obj.profissional.nome if obj.profissional_id else None

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if data.get("profissional") is not None and data.get("professional") is None:
            data["professional"] = data.get("profissional")
        return super().to_internal_value(data)

    def to_representation(self, instance):
        inicio, fim = bloqueio_datetime_range(instance)
        return {
            "id": instance.id,
            "professional": instance.profissional_id,
            "profissional": instance.profissional_id,
            "professional_name": self.get_professional_name(instance),
            "data_inicio": inicio.isoformat(),
            "data_fim": fim.isoformat(),
            "motivo": instance.motivo,
            "observacoes": instance.observacoes,
            "criado_em": instance.criado_em,
        }

    def _dia_inteiro_flag(self) -> bool:
        raw = self.initial_data.get("dia_inteiro") if hasattr(self, "initial_data") else None
        return (
            raw is True
            or raw == 1
            or (isinstance(raw, str) and raw.strip().lower() in ("1", "true", "yes", "sim"))
        )

    def validate(self, attrs):
        inicio = attrs.get("data_inicio")
        fim = attrs.get("data_fim")
        if inicio and fim and fim <= inicio:
            raise serializers.ValidationError({"data_fim": "O fim deve ser depois do início."})
        prof_id = attrs.get("professional")
        if prof_id is not None:
            if not Profissional.objects.filter(pk=prof_id, is_active=True).exists():
                raise serializers.ValidationError({"professional": "Profissional inválido."})
        return attrs

    def create(self, validated_data):
        start = validated_data.pop("data_inicio")
        end = validated_data.pop("data_fim")
        prof_id = validated_data.pop("professional", None)
        parts = split_datetime_range(start, end, dia_inteiro=self._dia_inteiro_flag())
        motivo = (validated_data.get("motivo") or "").strip() or "Bloqueio"
        return BloqueioHorario.objects.create(
            profissional_id=prof_id,
            **validated_data,
            **parts,
            titulo=motivo,
            tipo="outros",
        )

    def update(self, instance, validated_data):
        start = validated_data.pop("data_inicio", None)
        end = validated_data.pop("data_fim", None)
        if "professional" in validated_data:
            instance.profissional_id = validated_data.pop("professional")
        if start is not None and end is not None:
            for k, v in split_datetime_range(start, end, dia_inteiro=self._dia_inteiro_flag()).items():
                setattr(instance, k, v)
        motivo = validated_data.get("motivo")
        if motivo is not None:
            instance.titulo = motivo
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
