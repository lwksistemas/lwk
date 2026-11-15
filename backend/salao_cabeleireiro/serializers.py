from decimal import Decimal

from rest_framework import serializers

from .models import PAINEIS, Agendamento, Cliente, Profissional, Servico


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nome", "telefone", "email", "data_nascimento", "observacoes", "is_active"]

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


class ProfissionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profissional
        fields = ["id", "nome", "telefone", "email", "especialidade", "comissao_percentual", "is_active"]

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
        return (valor or "").strip() or "Serviço"


class AgendamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)
    profissional_nome = serializers.CharField(source="profissional.nome", read_only=True)
    servico_nome = serializers.CharField(source="servico.nome", read_only=True)
    preco = serializers.DecimalField(source="servico.preco", max_digits=10, decimal_places=2, read_only=True)
    fim = serializers.DateTimeField(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

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
            "observacoes",
        ]


def painel_valido(valor: str) -> bool:
    return valor in {codigo for codigo, _ in PAINEIS}
