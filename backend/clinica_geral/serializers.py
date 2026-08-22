from datetime import datetime

from rest_framework import serializers

from .models import ConfiguracaoConsultorio, Consulta, ConvenioPaciente, Paciente, Responsavel, Tarefa


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
        fields = ("id", "nome", "nome_social", "telefone", "email", "cpf", "numero_prontuario")


class ConsultaSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.SerializerMethodField()
    paciente_telefone = serializers.SerializerMethodField()
    paciente_email = serializers.SerializerMethodField()
    paciente_idade = serializers.SerializerMethodField()
    paciente_prontuario = serializers.SerializerMethodField()
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
            "data",
            "hora",
            "tipo",
            "modalidade",
            "convenio",
            "status",
            "duracao_minutos",
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
        fields = ("hora_inicio", "hora_fim", "duracao_minutos", "endereco", "telefone")

    def validate(self, attrs):
        inicio = attrs.get("hora_inicio", getattr(self.instance, "hora_inicio", None))
        fim = attrs.get("hora_fim", getattr(self.instance, "hora_fim", None))
        if inicio and fim and fim <= inicio:
            raise serializers.ValidationError("O horário de fim deve ser depois do início.")
        duracao = attrs.get("duracao_minutos")
        if duracao is not None and duracao not in (5, 10, 15, 20, 30, 45, 60):
            raise serializers.ValidationError("Duração deve ser 5, 10, 15, 20, 30, 45 ou 60 minutos.")
        return attrs
