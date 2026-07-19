"""Serializers de consultas, evoluções e prescrições Memed."""
from decimal import Decimal

from rest_framework import serializers

from core.serializer_mixins import TenantQuerysetMixin

from ..models import Consulta, ConsultaEvolucao, Convenio, LocalAtendimento, PrescricaoMemed


class ConsultaEvolucaoSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.nome", read_only=True)
    professional_name = serializers.CharField(source="professional.nome", read_only=True, default=None)

    class Meta:
        model = ConsultaEvolucao
        fields = [
            "id", "consulta", "patient", "patient_name", "professional", "professional_name",
            "descricao", "procedimento_realizado", "produtos_utilizados", "orientacoes",
            "protocolo_snapshot", "satisfacao", "created_at", "updated_at", "loja_id",
        ]
        read_only_fields = ["created_at", "updated_at", "loja_id"]


class PrescricaoMemedSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.nome", read_only=True)
    professional_name = serializers.CharField(source="professional.nome", read_only=True, default=None)

    class Meta:
        model = PrescricaoMemed
        fields = [
            "id", "consulta", "patient", "patient_name", "professional", "professional_name",
            "prescricao_id", "resumo", "itens", "pdf_url", "created_at", "loja_id",
        ]
        read_only_fields = ["created_at", "loja_id"]


class ConsultaSerializer(TenantQuerysetMixin, serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.nome", read_only=True)
    patient_foto_url = serializers.CharField(source="patient.foto_url", read_only=True, default="")
    professional_name = serializers.CharField(source="professional.nome", read_only=True, default=None)
    procedure_name = serializers.SerializerMethodField()
    procedures_list = serializers.SerializerMethodField()
    protocol_name = serializers.CharField(source="protocol.nome", read_only=True, default=None)
    appointment_date = serializers.DateTimeField(source="appointment.date", read_only=True)
    appointment_status = serializers.CharField(source="appointment.status", read_only=True)
    duracao_minutos = serializers.ReadOnlyField()
    total_evolucoes = serializers.SerializerMethodField()
    local_atendimento = serializers.PrimaryKeyRelatedField(
        queryset=LocalAtendimento.objects.none(),
        allow_null=True,
        required=False,
    )
    local_atendimento_name = serializers.CharField(
        source="local_atendimento.nome", read_only=True, default=None, allow_null=True,
    )
    local_atendimento_valor_consulta = serializers.SerializerMethodField()
    retorno_dias_prazo = serializers.SerializerMethodField()
    retorno_aviso_recibo = serializers.SerializerMethodField()
    convenio = serializers.PrimaryKeyRelatedField(
        queryset=Convenio.objects.none(),
        allow_null=True,
        required=False,
    )
    convenio_name = serializers.SerializerMethodField()
    nome_agenda_id = serializers.IntegerField(
        source="appointment.nome_agenda.id", read_only=True, allow_null=True, default=None,
    )
    nome_agenda_name = serializers.CharField(
        source="appointment.nome_agenda.nome", read_only=True, allow_null=True, default=None,
    )

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset("local_atendimento", LocalAtendimento.objects.all())
        self.bind_tenant_queryset("convenio", Convenio.objects.filter(is_active=True))
    valor_procedimentos = serializers.SerializerMethodField()
    valor_pagamento = serializers.SerializerMethodField()
    exige_termo_consentimento = serializers.SerializerMethodField()
    valor_pago = serializers.SerializerMethodField()
    valor_restante = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    payment_id = serializers.SerializerMethodField()
    payment_date = serializers.SerializerMethodField()
    numero = serializers.SerializerMethodField()
    status_assinatura_termo_display = serializers.CharField(
        source="get_status_assinatura_termo_display", read_only=True,
    )

    class Meta:
        model = Consulta
        fields = [
            "id", "numero", "appointment", "patient", "patient_name", "patient_foto_url",
            "professional", "professional_name",
            "procedure", "procedure_name", "procedures_list", "protocol", "protocol_name", "status",
            "data_inicio", "data_fim", "duracao_minutos", "observacoes_gerais", "protocolo_notas",
            "valor_consulta", "valor_procedimentos", "valor_pagamento",
            "valor_pago", "valor_restante", "payment_status", "payment_id", "payment_date",
            "retorno_gratuito", "retorno_tipo", "retorno_dias_prazo", "retorno_aviso_recibo",
            "local_atendimento", "local_atendimento_name", "local_atendimento_valor_consulta",
            "convenio", "convenio_name",
            "nome_agenda_id", "nome_agenda_name",
            "appointment_date", "appointment_status", "total_evolucoes",
            "status_assinatura_termo", "status_assinatura_termo_display", "exige_termo_consentimento",
            "created_at", "updated_at", "loja_id",
        ]
        read_only_fields = [
            "numero", "created_at", "updated_at", "loja_id", "appointment",
            "retorno_gratuito", "retorno_tipo", "retorno_dias_prazo", "retorno_aviso_recibo",
            "local_atendimento_valor_consulta",
        ]

    def get_numero(self, obj):
        n = getattr(obj, "numero", None)
        if n is None:
            return None
        return str(n).zfill(3)

    def get_local_atendimento_valor_consulta(self, obj):
        info = self._info_retorno_recibo(obj)
        ref = info.get("taxa_consulta_referencia")
        if ref is None:
            return None
        return float(ref or 0)

    def _info_retorno_recibo(self, obj):
        cache = self.context.setdefault("_info_retorno_recibo", {})
        key = getattr(obj, "pk", None) or id(obj)
        if key not in cache:
            from clinica_beleza.recibo.retorno_info import montar_info_retorno_recibo

            cache[key] = montar_info_retorno_recibo(obj, getattr(obj, "appointment", None))
        return cache[key]

    def get_retorno_dias_prazo(self, obj):
        return self._info_retorno_recibo(obj).get("retorno_dias")

    def get_retorno_aviso_recibo(self, obj):
        return self._info_retorno_recibo(obj).get("retorno_aviso") or ""

    def get_total_evolucoes(self, obj):
        return obj.evolucoes.count()

    def _appointment_procedures(self, obj):
        appointment = getattr(obj, "appointment", None)
        if not appointment:
            return []
        return list(
            appointment.appointment_procedures.select_related("procedure").order_by("ordem", "id"),
        )

    def get_procedure_name(self, obj):
        procs = self._appointment_procedures(obj)
        if procs:
            return ", ".join(ap.procedure.nome for ap in procs)
        if obj.procedure_id and obj.procedure:
            return obj.procedure.nome
        return ""

    def get_procedures_list(self, obj):
        procs = self._appointment_procedures(obj)
        if procs:
            return [
                {
                    "id": ap.procedure_id,
                    "appointment_procedure_id": ap.id,
                    "nome": ap.procedure.nome,
                    "valor": float(ap.get_valor()),
                    "exige_termo": bool(
                        ap.procedure.termo_consentimento_ativo
                        and (ap.procedure.termo_consentimento or "").strip(),
                    ),
                }
                for ap in procs
            ]
        if obj.procedure_id and obj.procedure:
            return [{
                "id": obj.procedure_id,
                "nome": obj.procedure.nome,
                "valor": float(obj.procedure.preco or 0),
            }]
        return []

    def _appointment_valor_procedimentos(self, obj) -> Decimal:
        appointment = getattr(obj, "appointment", None)
        if not appointment:
            return Decimal(0)
        return Decimal(str(appointment.valor_total or 0))

    def get_valor_procedimentos(self, obj):
        return float(self._appointment_valor_procedimentos(obj))

    def get_valor_pagamento(self, obj):
        vc = Decimal(str(obj.valor_consulta or 0))
        return float(vc + self._appointment_valor_procedimentos(obj))

    def _get_payment(self, obj):
        """Payment do appointment; usa prefetch se disponível."""
        appointment = getattr(obj, "appointment", None)
        if not appointment:
            return None
        prefetched = getattr(appointment, "_prefetched_objects_cache", {}).get("payment_set")
        if prefetched is not None:
            return prefetched[0] if prefetched else None
        try:
            from ..models import Payment
            return Payment.objects.filter(appointment=appointment).order_by("-id").first()
        except Exception:
            return None

    def get_valor_pago(self, obj):
        payment = self._get_payment(obj)
        if payment is None:
            return None
        try:
            return float(payment.valor_pago_parcelas)
        except Exception:
            return float(payment.amount or 0)

    def get_valor_restante(self, obj):
        """Saldo em aberto (alinhado a Payment.saldo_devedor)."""
        payment = self._get_payment(obj)
        if payment is None:
            return float(self.get_valor_pagamento(obj) or 0)
        try:
            return float(payment.saldo_devedor)
        except Exception:
            vc = float(self.get_valor_pagamento(obj) or 0)
            return max(0.0, vc - float(payment.amount or 0))

    def get_payment_id(self, obj):
        """ID do Payment vinculado (para acessar parcelas via /payments/<id>/parcelas/)."""
        payment = self._get_payment(obj)
        return payment.id if payment else None

    def get_payment_status(self, obj):
        """Status para UI da consulta.
        DRAFT (rascunho pré-finalização) aparece como PAID/PARTIAL conforme saldo.
        """
        payment = self._get_payment(obj)
        if not payment:
            return None
        if payment.status == "DRAFT":
            try:
                if payment.saldo_devedor <= 0.01:
                    return "PAID"
                return "PARTIAL"
            except Exception:
                return "PARTIAL"
        return payment.status

    def get_payment_date(self, obj):
        """Data/hora do pagamento vinculado (ISO 8601) para exibir no recibo."""
        payment = self._get_payment(obj)
        if not payment:
            return None
        dt = getattr(payment, "payment_date", None)
        if dt:
            from django.utils import timezone as dj_tz
            if dj_tz.is_aware(dt):
                dt = dj_tz.localtime(dt)
            return dt.isoformat()
        return None

    def get_convenio_name(self, obj):
        if obj.convenio_id and obj.convenio:
            return obj.convenio.nome
        return "Particular"

    def get_exige_termo_consentimento(self, obj):
        from ..consentimento_service import consulta_exige_termo_consentimento
        return consulta_exige_termo_consentimento(obj)


class ConsultaListSerializer(ConsultaSerializer):
    """Serializer leve para listagens — evita N+1 em total_evolucoes e consultas de termo.
    Requer queryset com annotate(total_evolucoes_count=Count('evolucoes')).
    """

    total_evolucoes = serializers.IntegerField(source="total_evolucoes_count", read_only=True)

    class Meta(ConsultaSerializer.Meta):
        fields = [
            f for f in ConsultaSerializer.Meta.fields
            if f not in ("exige_termo_consentimento",)
        ]
