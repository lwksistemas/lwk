"""Teste de emissão NFS-e via ISSNet Nacional em produção.
Executa no worker Railway via: python3 manage.py shell < scripts/test_emissao_nfse_prod.py
"""
import traceback
from decimal import Decimal

from superadmin.models import Loja
from tenants.middleware import _configure_tenant_db_for_loja

loja = Loja.objects.using("default").get(id=4)
print(f"Loja: {loja.nome} ({loja.cpf_cnpj})")

_configure_tenant_db_for_loja(loja)

from crm_vendas.models import NfseConfigLoja
config = NfseConfigLoja.objects.first()
print(f"Provedor: {config.provedor_nfse}")
print(f"IM: {getattr(config, 'inscricao_municipal', 'N/A')}")
print(f"Cert: {bool(config.issnet_certificado)}")

from nfse_integration.emissao_issnet_nacional_loja import emitir_via_issnet_nacional_loja

resultado = emitir_via_issnet_nacional_loja(
    loja=loja,
    config=config,
    tomador_cpf_cnpj="24758458000172",
    tomador_nome="LWK SISTEMAS LTDA",
    tomador_email="contato@lwksistemas.com.br",
    tomador_endereco={
        "logradouro": "MARCOS MARKARIAN",
        "numero": "1025",
        "bairro": "NOVA ALIANCA",
        "cep": "14026583",
        "codigo_municipio": "3543402",
        "cidade": "Ribeirao Preto",
        "uf": "SP",
    },
    servico_descricao="Conserto Restauracao de Computadores e Similar",
    valor_servicos=Decimal("1.00"),
    enviar_email=False,
    enviar_email_fn=lambda **kw: None,
)

print(f"\n{'='*60}")
print(f"RESULTADO: {'SUCESSO' if resultado.get('success') else 'FALHA'}")
print(f"{'='*60}")
for k, v in resultado.items():
    if k == "xml_nfse":
        print(f"  {k}: ({len(str(v))} chars)")
    else:
        print(f"  {k}: {v}")
