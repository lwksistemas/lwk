from rest_framework import serializers

from .models import Consulta, ConvenioPaciente, Paciente, Responsavel


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
            "nome_mae",
            "tipo_sanguineo",
            "telefone",
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
        fields = ("id", "nome", "nome_social", "telefone", "email", "cpf")


class ConsultaSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.SerializerMethodField()
    paciente_telefone = serializers.SerializerMethodField()
    paciente_email = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = (
            "id",
            "paciente",
            "paciente_nome",
            "paciente_telefone",
            "paciente_email",
            "data",
            "hora",
            "tipo",
            "modalidade",
            "convenio",
            "status",
            "observacoes",
        )
        read_only_fields = ("id", "paciente_nome", "paciente_telefone", "paciente_email")

    def get_paciente_nome(self, obj):
        p = obj.paciente
        if p.nome_social:
            return f"{p.nome_social} ({p.nome})"
        return p.nome

    def get_paciente_telefone(self, obj):
        return obj.paciente.telefone

    def get_paciente_email(self, obj):
        return obj.paciente.email
