from datetime import datetime

from rest_framework import serializers

from .models import (
    ConfiguracaoConsultorio,
    Consulta,
    ConvenioPaciente,
    Evolucao,
    FechamentoCaixa,
    GuiaTiss,
    LoteTiss,
    Paciente,
    PacienteAnexo,
    Prescricao,
    PrescricaoItem,
    Responsavel,
    Tarefa,
)


class ResponsavelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsavel
        fields = ("id", "nome", "profissao", "parentesco", "telefone")


class ConvenioPacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConvenioPaciente
        fields = ("id", "convenio", "plano", "carteirinha", "validade")


class PacienteSerializer(serializers.ModelSerializer):
    responsaveis = ResponsavelSerializer(many=True, required=False)
    convenios = ConvenioPacienteSerializer(many=True, required=False)

    class Meta:
        model = Paciente
        fields = (
            "id",
            "numero_prontuario",
            "medico_referencia",
            "nome",
            "nome_social",
            "data_nascimento",
            "sexo",
            "estado_civil",
            "cpf",
            "rg",
            "passaporte",
            "rne",
            "pais_emissor",
            "nome_mae",
            "tipo_sanguineo",
            "nacionalidade",
            "profissao",
            "foto_url",
            "telefone",
            "telefone_fixo",
            "quem_indicou",
            "email",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "observacoes",
            "alergias",
            "responsaveis",
            "convenios",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        responsaveis = validated_data.pop("responsaveis", [])
        convenios = validated_data.pop("convenios", [])
        paciente = Paciente.objects.create(**validated_data)
        if not paciente.numero_prontuario:
            paciente.numero_prontuario = str(paciente.id)
            paciente.save(update_fields=["numero_prontuario"])
        for item in responsaveis:
            Responsavel.objects.create(paciente=paciente, **item)
        for item in convenios:
            ConvenioPaciente.objects.create(paciente=paciente, **item)
        return paciente

    def update(self, instance, validated_data):
        responsaveis = validated_data.pop("responsaveis", None)
        convenios = validated_data.pop("convenios", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if responsaveis is not None:
            instance.responsaveis.all().delete()
            for item in responsaveis:
                Responsavel.objects.create(paciente=instance, **item)
        if convenios is not None:
            instance.convenios.all().delete()
            for item in convenios:
                ConvenioPaciente.objects.create(paciente=instance, **item)
        return instance


class PacienteListaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ("id", "nome", "nome_social", "telefone", "email", "cpf", "numero_prontuario", "alergias")


class ConsultaSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.SerializerMethodField()
    paciente_telefone = serializers.SerializerMethodField()
    paciente_email = serializers.SerializerMethodField()
    paciente_idade = serializers.SerializerMethodField()
    paciente_prontuario = serializers.SerializerMethodField()
    paciente_alergias = serializers.SerializerMethodField()
    paciente_foto_url = serializers.SerializerMethodField()
    minutos_espera = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = (
            "id",
            "paciente",
            "paciente_nome",
            "paciente_telefone",
            "paciente_email",
            "paciente_idade",
            "paciente_prontuario",
            "paciente_alergias",
            "paciente_foto_url",
            "data",
            "hora",
            "tipo",
            "modalidade",
            "convenio",
            "status",
            "duracao_minutos",
            "valor",
            "tele_sala_url",
            "tele_minutos",
            "agendado_por",
            "minutos_espera",
            "observacoes",
        )
        read_only_fields = (
            "id",
            "paciente_nome",
            "paciente_telefone",
            "paciente_email",
            "paciente_idade",
            "paciente_prontuario",
            "paciente_alergias",
            "paciente_foto_url",
            "tele_sala_url",
            "minutos_espera",
            "agendado_por",
        )

    def get_paciente_nome(self, obj):
        p = obj.paciente
        if p.nome_social:
            return f"{p.nome_social} ({p.nome})"
        return p.nome

    def get_paciente_telefone(self, obj):
        return obj.paciente.telefone

    def get_paciente_email(self, obj):
        return obj.paciente.email

    def get_paciente_prontuario(self, obj):
        return obj.paciente.numero_prontuario or str(obj.paciente_id)

    def get_paciente_alergias(self, obj):
        return obj.paciente.alergias or ""

    def get_paciente_foto_url(self, obj):
        return obj.paciente.foto_url or ""

    def get_paciente_idade(self, obj):
        nasc = obj.paciente.data_nascimento
        if not nasc:
            return None
        hoje = datetime.now().date()
        idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
        return idade if idade >= 0 else None

    def get_minutos_espera(self, obj):
        if obj.status in ("desmarcado", "faltou", "atendido"):
            return 0
        inicio = datetime.combine(obj.data, obj.hora)
        agora = datetime.now()
        if agora <= inicio:
            return 0
        return int((agora - inicio).total_seconds() // 60)


class TarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarefa
        fields = ("id", "data", "texto", "concluida")
        read_only_fields = ("id",)


class ConfiguracaoConsultorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoConsultorio
        fields = (
            "hora_inicio",
            "hora_fim",
            "duracao_minutos",
            "endereco",
            "telefone",
            "especialidade",
            "crm",
            "medico_nome",
            "teto_tele_minutos",
        )

    def validate(self, attrs):
        inicio = attrs.get("hora_inicio", getattr(self.instance, "hora_inicio", None))
        fim = attrs.get("hora_fim", getattr(self.instance, "hora_fim", None))
        if inicio and fim and fim <= inicio:
            raise serializers.ValidationError("O horário de fim deve ser depois do início.")
        duracao = attrs.get("duracao_minutos")
        if duracao is not None and duracao not in (5, 10, 15, 20, 30, 45, 60):
            raise serializers.ValidationError("Duração deve ser 5, 10, 15, 20, 30, 45 ou 60 minutos.")
        return attrs


class EvolucaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evolucao
        fields = (
            "id",
            "consulta",
            "paciente",
            "especialidade",
            "subjetivo",
            "objetivo",
            "avaliacao",
            "plano",
            "ficha",
            "updated_at",
        )
        read_only_fields = ("id", "updated_at")


class PrescricaoItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescricaoItem
        fields = ("id", "medicamento", "dosagem", "posologia", "quantidade", "alerta_alergia")
        read_only_fields = ("id", "alerta_alergia")


class PrescricaoSerializer(serializers.ModelSerializer):
    itens = PrescricaoItemSerializer(many=True)

    class Meta:
        model = Prescricao
        fields = ("id", "consulta", "paciente", "itens", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        from .alergia_service import medicamento_conflita_alergia

        itens = validated_data.pop("itens", [])
        prescricao = Prescricao.objects.create(**validated_data)
        alergias = prescricao.paciente.alergias
        for item in itens:
            PrescricaoItem.objects.create(
                prescricao=prescricao,
                alerta_alergia=medicamento_conflita_alergia(alergias, item.get("medicamento", "")),
                **item,
            )
        return prescricao


class LoteTissSerializer(serializers.ModelSerializer):
    guias_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = LoteTiss
        fields = ("id", "numero", "competencia", "status", "guias_count", "created_at")
        read_only_fields = ("id", "created_at")


class GuiaTissSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.SerializerMethodField()
    consulta_data = serializers.SerializerMethodField()

    class Meta:
        model = GuiaTiss
        fields = (
            "id",
            "lote",
            "consulta",
            "numero_guia",
            "codigo_procedimento",
            "valor",
            "paciente_nome",
            "consulta_data",
            "created_at",
        )
        read_only_fields = ("id", "numero_guia", "paciente_nome", "consulta_data", "created_at")

    def get_paciente_nome(self, obj):
        return obj.consulta.paciente.nome

    def get_consulta_data(self, obj):
        return obj.consulta.data.isoformat()


class FechamentoCaixaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FechamentoCaixa
        fields = ("id", "data", "total_particular", "total_convenio", "observacoes", "created_at")
        read_only_fields = ("id", "created_at")


class PacienteAnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteAnexo
        fields = ("id", "paciente", "nome", "url", "created_at")
        read_only_fields = ("id", "created_at")
