import re
from decimal import Decimal

from rest_framework import serializers

from .caixa_service import rotulo_formas
from .models import PAINEIS, Agendamento, Cliente, Profissional, Servico


def cpf_valido(digitos: str) -> bool:
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(digitos[indice]) * ((tamanho + 1) - indice) for indice in range(tamanho))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[tamanho]):
            return False
    return True


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id",
            "nome",
            "telefone",
            "email",
            "cpf",
            "data_nascimento",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "endereco",
            "observacoes",
            "is_active",
        ]
        read_only_fields = ["endereco"]

    def validate_nome(self, valor):
        nome = (valor or "").strip()
        if len(nome) < 2:
            raise serializers.ValidationError("Informe o nome do cliente.")
        return nome

    def validate_telefone(self, valor):
        telefone = "".join(ch for ch in (valor or "") if ch.isdigit())
        if len(telefone) < 8:
            raise serializers.ValidationError("Informe o telefone do cliente.")
        return telefone

    def validate_cpf(self, valor):
        digitos = re.sub(r"\D", "", valor or "")
        if not digitos:
            return ""
        if not cpf_valido(digitos):
            raise serializers.ValidationError("Informe um CPF válido.")
        consulta = Cliente.objects.filter(is_active=True).exclude(cpf__isnull=True).exclude(cpf="")
        if self.instance is not None:
            consulta = consulta.exclude(pk=self.instance.pk)
        for outro in consulta.only("id", "cpf"):
            if re.sub(r"\D", "", outro.cpf or "") == digitos:
                raise serializers.ValidationError("Já existe um cliente com este CPF.")
        return digitos

    def validate_cep(self, valor):
        digitos = re.sub(r"\D", "", valor or "")
        if digitos and len(digitos) != 8:
            raise serializers.ValidationError("Informe o CEP com 8 números.")
        return digitos

    def validate_estado(self, valor):
        uf = (valor or "").strip().upper()
        if uf and (len(uf) != 2 or not uf.isalpha()):
            raise serializers.ValidationError("Informe a sigla do estado.")
        return uf

    def _montar_endereco(self, dados):
        cep = dados.get("cep") or ""
        if len(cep) == 8:
            cep = f"{cep[:5]}-{cep[5:]}"
        partes = [
            (dados.get("logradouro") or "").strip(),
            f"Nº {(dados.get('numero') or '').strip()}" if (dados.get("numero") or "").strip() else "",
            (dados.get("complemento") or "").strip(),
            (dados.get("bairro") or "").strip(),
            f"CEP {cep}" if cep else "",
        ]
        return ", ".join(parte for parte in partes if parte)

    def create(self, validated_data):
        validated_data["endereco"] = self._montar_endereco(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        campos = ("cep", "logradouro", "numero", "complemento", "bairro")
        if any(campo in validated_data for campo in campos):
            atual = {campo: getattr(instance, campo, "") for campo in campos}
            atual.update(validated_data)
            validated_data["endereco"] = self._montar_endereco(atual)
        return super().update(instance, validated_data)


class ProfissionalSerializer(serializers.ModelSerializer):
    comissoes = serializers.SerializerMethodField()

    class Meta:
        model = Profissional
        fields = [
            "id",
            "nome",
            "telefone",
            "email",
            "especialidade",
            "comissao_tipo",
            "comissao_percentual",
            "comissao_fixa",
            "comissoes",
            "is_active",
        ]

    def get_comissoes(self, profissional):
        return [
            {
                "servico": item.servico_id,
                "nome": item.servico.nome,
                "tipo": item.tipo,
                "valor": f"{item.valor:.2f}",
            }
            for item in profissional.comissoes.select_related("servico").all()
        ]

    def validate_comissao_tipo(self, valor):
        tipo = (valor or "percentual").strip()
        if tipo not in {"percentual", "fixo"}:
            raise serializers.ValidationError("Escolha porcentagem ou valor fixo.")
        return tipo

    def validate_comissao_percentual(self, valor):
        percentual = Decimal(str(valor or 0))
        if percentual < 0 or percentual > 100:
            raise serializers.ValidationError("A porcentagem fica entre 0 e 100.")
        return percentual

    def validate_comissao_fixa(self, valor):
        fixa = Decimal(str(valor or 0))
        if fixa < 0:
            raise serializers.ValidationError("O valor fixo não pode ser negativo.")
        return fixa

    def validate_nome(self, valor):
        nome = (valor or "").strip()
        if len(nome) < 2:
            raise serializers.ValidationError("Informe o nome do profissional.")
        return nome

    def validate_especialidade(self, valor):
        return (valor or "").strip() or "Cabeleireiro"

    def validate_telefone(self, valor):
        telefone = "".join(ch for ch in (valor or "") if ch.isdigit())
        if len(telefone) < 8:
            raise serializers.ValidationError("Informe o telefone do profissional.")
        return telefone


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = ["id", "nome", "descricao", "duracao_minutos", "preco", "categoria", "is_active"]

    def validate_nome(self, valor):
        nome = (valor or "").strip()
        if len(nome) < 2:
            raise serializers.ValidationError("Informe o nome do serviço.")
        return nome

    def validate_duracao_minutos(self, valor):
        if not valor or int(valor) < 5 or int(valor) > 480:
            raise serializers.ValidationError("A duração fica entre 5 e 480 minutos.")
        return int(valor)

    def validate_preco(self, valor):
        preco = Decimal(str(valor or 0))
        if preco < 0:
            raise serializers.ValidationError("O preço não pode ser negativo.")
        return preco

    def validate_categoria(self, valor):
        from .categoria_service import categoria_valida

        nome = categoria_valida(valor)
        if not nome:
            raise serializers.ValidationError("Escolha uma categoria cadastrada.")
        return nome


class AgendamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)
    profissional_nome = serializers.CharField(source="profissional.nome", read_only=True)
    servico_nome = serializers.SerializerMethodField()
    preco = serializers.SerializerMethodField()
    procedimentos = serializers.SerializerMethodField()
    fim = serializers.DateTimeField(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    recebido = serializers.SerializerMethodField()

    class Meta:
        model = Agendamento
        fields = [
            "id",
            "inicio",
            "fim",
            "duracao_minutos",
            "status",
            "status_label",
            "cliente",
            "cliente_nome",
            "profissional",
            "profissional_nome",
            "servico",
            "servico_nome",
            "preco",
            "procedimentos",
            "observacoes",
            "recebido",
        ]

    def get_servico_nome(self, obj):
        from .procedimentos_service import nomes_do_agendamento

        return nomes_do_agendamento(obj)

    def get_preco(self, obj):
        from .caixa_service import quantia
        from .procedimentos_service import preco_do_agendamento

        return f"{quantia(preco_do_agendamento(obj)):.2f}"

    def get_procedimentos(self, obj):
        from .caixa_service import quantia
        from .procedimentos_service import servicos_do_agendamento

        return [
            {
                "id": servico.id,
                "nome": servico.nome,
                "categoria": servico.categoria,
                "duracao_minutos": servico.duracao_minutos,
                "preco": f"{quantia(servico.preco):.2f}",
            }
            for servico in servicos_do_agendamento(obj)
        ]

    def get_recebido(self, obj):
        item = next((recebimento for recebimento in obj.recebimentos.all() if recebimento.is_active), None)
        if item is None:
            return None
        return {
            "id": item.id,
            "valor": f"{item.valor:.2f}",
            "desconto": f"{item.desconto:.2f}",
            "forma": item.forma,
            "forma_label": rotulo_formas(item.partes, item.forma),
            "comissao_valor": f"{item.comissao_valor:.2f}",
        }


def painel_valido(valor: str) -> bool:
    return valor in {codigo for codigo, _ in PAINEIS}
