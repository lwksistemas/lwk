from rest_framework import serializers

from core.serializers import BaseLojaSerializer

from .models import (
    AuditoriaAcessoEstudo,
    Equipamento,
    Laudo,
    PacienteRadiologia,
    PedidoExame,
    Procedimento,
)


class PacienteRadiologiaSerializer(BaseLojaSerializer):
    class Meta:
        model = PacienteRadiologia
        fields = [
            "id",
            "nome",
            "cpf",
            "data_nascimento",
            "sexo",
            "telefone",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "loja_id"]


class EquipamentoSerializer(BaseLojaSerializer):
    class Meta:
        model = Equipamento
        fields = [
            "id",
            "nome",
            "ae_title",
            "modality",
            "fabricante",
            "modelo",
            "station_name",
            "suporte_dicom_storage",
            "suporte_mwl",
            "suporte_sr",
            "cobranca_mensal",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "loja_id"]


class ProcedimentoSerializer(BaseLojaSerializer):
    class Meta:
        model = Procedimento
        fields = [
            "id",
            "codigo",
            "nome",
            "modality",
            "descricao",
            "template_laudo",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "loja_id"]


class PedidoExameSerializer(BaseLojaSerializer):
    paciente_nome = serializers.CharField(source="paciente.nome", read_only=True)
    procedimento_nome = serializers.CharField(source="procedimento.nome", read_only=True)
    equipamento_nome = serializers.CharField(source="equipamento.nome", read_only=True, allow_null=True)
    equipamento_ae_title = serializers.CharField(
        source="equipamento.ae_title", read_only=True, allow_null=True
    )

    class Meta:
        model = PedidoExame
        fields = [
            "id",
            "paciente",
            "paciente_nome",
            "procedimento",
            "procedimento_nome",
            "equipamento",
            "equipamento_nome",
            "equipamento_ae_title",
            "medico_solicitante",
            "crm_solicitante",
            "indicacao_clinica",
            "agendado_para",
            "status",
            "accession_number",
            "study_instance_uid",
            "orthanc_study_id",
            "dicom_media_url",
            "dicom_instance_count",
            "dicom_synced_at",
            "mwl_synced_at",
            "observacoes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "accession_number",
            "study_instance_uid",
            "orthanc_study_id",
            "dicom_media_url",
            "dicom_instance_count",
            "dicom_synced_at",
            "mwl_synced_at",
            "created_at",
            "updated_at",
            "loja_id",
        ]

    def validate_equipamento(self, value):
        if self.instance is None and value is None:
            raise serializers.ValidationError(
                "Selecione o equipamento (ultrassom) para vincular ao exame do paciente."
            )
        return value


class LaudoSerializer(BaseLojaSerializer):
    accession_number = serializers.CharField(source="pedido.accession_number", read_only=True)
    paciente_nome = serializers.CharField(source="pedido.paciente.nome", read_only=True)

    class Meta:
        model = Laudo
        fields = [
            "id",
            "pedido",
            "accession_number",
            "paciente_nome",
            "medico_laudador",
            "crm_laudador",
            "texto",
            "conclusao",
            "bi_rads",
            "status",
            "pdf_url",
            "assinado_em",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "pdf_url",
            "assinado_em",
            "created_at",
            "updated_at",
            "loja_id",
            "status",
        ]


class AuditoriaAcessoEstudoSerializer(BaseLojaSerializer):
    class Meta:
        model = AuditoriaAcessoEstudo
        fields = [
            "id",
            "pedido",
            "study_instance_uid",
            "usuario_id",
            "usuario_nome",
            "acao",
            "ip",
            "detalhe",
            "created_at",
        ]
        read_only_fields = fields
