"""Helpers de aplicacao para emissao de NFS-e."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DadosTomadorNFSe:
    cpf_cnpj: str
    nome: str
    email: str
    endereco: dict[str, str]


class ContaTomadorNaoEncontrada(Exception):
    """Sinaliza que a conta informada para emissao nao pertence a loja."""

    def __init__(self, conta_id: int):
        self.conta_id = conta_id
        super().__init__(f"Conta {conta_id} nao encontrada")


def montar_dados_tomador_nfse(validated_data: dict[str, Any], loja_id: int) -> DadosTomadorNFSe:
    """Monta os dados do tomador a partir de uma conta CRM ou dos campos manuais.

    A view continua responsavel por validar HTTP/serializer; este helper concentra
    a regra de aplicacao usada para transformar entrada validada em dados de emissao.
    """
    conta_id = validated_data.get("conta_id")

    if conta_id:
        from crm_vendas.models import Conta

        try:
            conta = Conta.objects.get(id=conta_id, loja_id=loja_id)
        except Conta.DoesNotExist as exc:
            raise ContaTomadorNaoEncontrada(conta_id) from exc

        return DadosTomadorNFSe(
            cpf_cnpj=conta.cnpj or "",
            nome=conta.razao_social or conta.nome,
            email=conta.email or "",
            endereco={
                "logradouro": conta.logradouro or "",
                "numero": conta.numero or "S/N",
                "complemento": conta.complemento or "",
                "bairro": conta.bairro or "",
                "cidade": conta.cidade or "",
                "uf": conta.uf or "",
                "cep": conta.cep or "",
                "telefone": getattr(conta, "telefone", "") or "",
            },
        )

    return DadosTomadorNFSe(
        cpf_cnpj=validated_data.get("tomador_cpf_cnpj", ""),
        nome=validated_data.get("tomador_nome", ""),
        email=validated_data.get("tomador_email", ""),
        endereco={
            "logradouro": validated_data.get("tomador_logradouro", ""),
            "numero": validated_data.get("tomador_numero", "S/N"),
            "complemento": validated_data.get("tomador_complemento", ""),
            "bairro": validated_data.get("tomador_bairro", ""),
            "cidade": validated_data.get("tomador_cidade", ""),
            "uf": validated_data.get("tomador_uf", ""),
            "cep": validated_data.get("tomador_cep", ""),
        },
    )
