from datetime import datetime

from rest_framework import serializers

from .models import (
    ConfiguracaoConsultorio,
    Consulta,
    ConvenioConsultorio,
    ConvenioPaciente,
    Evolucao,
    Especialidade,
    FechamentoCaixa,
    Funcionario,
    GuiaTiss,
    LoteTiss,
    Paciente,
    PacienteAnexo,
    Prescricao,
    PrescricaoItem,
    Profissional,
    Responsavel,
    Tarefa,
    TipoConsulta,
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
            from .catalog_service import montar_numero_prontuario

            paciente.numero_prontuario = montar_numero_prontuario(paciente.id)
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
    tele_link = serializers.SerializerMethodField()

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
            "tele_token",
            "tele_link",
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
            "tele_token",
            "tele_link",
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

    def get_tele_link(self, obj):
        from .tele_service import link_paciente

        return link_paciente(obj) if getattr(obj, "tele_token", "") else ""

    def create(self, validated_data):
        from .catalog_service import aplicar_tipo_na_consulta

        aplicar_tipo_na_consulta(validated_data, self.initial_data)
        return super().create(validated_data)


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
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "telefone",
            "especialidade",
            "crm",
            "medico_nome",
            "teto_tele_minutos",
            "prontuario_prefixo",
            "prontuario_abas_ocultas",
        )

    def validate_uf(self, value):
        from .equipe_service import normalizar_uf

        return normalizar_uf(value)

    def update(self, instance, validated_data):
        from .catalog_service import montar_endereco

        obj = super().update(instance, validated_data)
        montado = montar_endereco(
            obj.logradouro, obj.numero, obj.complemento, obj.bairro, obj.cidade, obj.uf, obj.cep
        )
        if montado and obj.endereco != montado:
            obj.endereco = montado
            obj.save(update_fields=["endereco"])
        return obj

    def validate_prontuario_abas_ocultas(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Informe uma lista de abas.")
        return [str(item).strip() for item in value if str(item).strip()]

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


class ProfissionalSerializer(serializers.ModelSerializer):
    especialidade_nome = serializers.CharField(source="especialidade.nome", read_only=True)

    class Meta:
        model = Profissional
        fields = (
            "id",
            "especialidade",
            "especialidade_nome",
            "nome",
            "conselho",
            "registro",
            "uf",
            "email",
            "telefone",
            "cbo",
        )
        read_only_fields = ("id",)

    def validate_nome(self, value):
        from .equipe_service import normalizar_nome

        nome = normalizar_nome(value)
        if not nome:
            raise serializers.ValidationError("Informe o nome do profissional.")
        return nome

    def validate_uf(self, value):
        from .equipe_service import normalizar_uf

        return normalizar_uf(value)


class EspecialidadeSerializer(serializers.ModelSerializer):
    profissionais = ProfissionalSerializer(many=True, read_only=True)

    class Meta:
        model = Especialidade
        fields = ("id", "nome", "profissionais")
        read_only_fields = ("id",)

    def validate_nome(self, value):
        from .equipe_service import normalizar_nome

        nome = normalizar_nome(value)
        if not nome:
            raise serializers.ValidationError("Informe o nome da especialidade.")
        return nome


class FuncionarioSerializer(serializers.ModelSerializer):
    cargo_label = serializers.SerializerMethodField()

    class Meta:
        model = Funcionario
        fields = ("id", "nome", "cargo", "cargo_label", "email", "telefone")
        read_only_fields = ("id",)

    def get_cargo_label(self, obj):
        from .equipe_service import cargo_label

        return cargo_label(obj.cargo)

    def validate_nome(self, value):
        from .equipe_service import normalizar_nome

        nome = normalizar_nome(value)
        if not nome:
            raise serializers.ValidationError("Informe o nome do funcionário.")
        return nome


class TipoConsultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoConsulta
        fields = ("id", "codigo", "nome", "duracao_minutos", "valor", "ordem")
        read_only_fields = ("id", "codigo")

    def validate_nome(self, value):
        from .equipe_service import normalizar_nome

        nome = normalizar_nome(value)
        if not nome:
            raise serializers.ValidationError("Informe o nome do tipo de consulta.")
        qs = TipoConsulta.objects.filter(nome__iexact=nome, is_active=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe um tipo com este nome.")
        return nome

    def create(self, validated_data):
        from .catalog_service import codigo_unico_tipo

        validated_data["codigo"] = codigo_unico_tipo(validated_data["nome"])
        if "ordem" not in validated_data or validated_data.get("ordem") in (None, 0):
            ultimo = TipoConsulta.objects.filter(is_active=True).order_by("-ordem").first()
            validated_data["ordem"] = (ultimo.ordem + 1) if ultimo else 1
        return super().create(validated_data)


class ConvenioConsultorioSerializer(serializers.ModelSerializer):
    tipo_label = serializers.SerializerMethodField()

    class Meta:
        model = ConvenioConsultorio
        fields = ("id", "nome", "tipo", "tipo_label", "registro_ans", "telefone", "observacoes", "ordem")
        read_only_fields = ("id",)

    def get_tipo_label(self, obj):
        return dict(ConvenioConsultorio.TIPO_CHOICES).get(obj.tipo, obj.tipo)

    def validate_nome(self, value):
        from .equipe_service import normalizar_nome

        nome = normalizar_nome(value)
        if not nome:
            raise serializers.ValidationError("Informe o nome do convênio.")
        qs = ConvenioConsultorio.objects.filter(nome__iexact=nome, is_active=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe um convênio com este nome.")
        return nome

    def validate_tipo(self, value):
        tipos = {k for k, _ in ConvenioConsultorio.TIPO_CHOICES}
        tipo = (value or "convenio").strip().lower()
        if tipo not in tipos:
            raise serializers.ValidationError("Tipo inválido.")
        return tipo

    def create(self, validated_data):
        inativo = ConvenioConsultorio.objects.filter(nome=validated_data["nome"], is_active=False).first()
        if inativo:
            for key, value in validated_data.items():
                setattr(inativo, key, value)
            inativo.is_active = True
            inativo.save()
            return inativo
        if "ordem" not in validated_data or validated_data.get("ordem") in (None, 0):
            ultimo = ConvenioConsultorio.objects.filter(is_active=True).order_by("-ordem").first()
            validated_data["ordem"] = (ultimo.ordem + 1) if ultimo else 1
        return super().create(validated_data)

