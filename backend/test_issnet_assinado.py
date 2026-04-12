"""Teste ISSNet com assinatura digital usando certificado da loja."""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_production'
django.setup()

from nfse_integration.issnet_client import ISSNetClient
from decimal import Decimal
from datetime import datetime
import tempfile

# Buscar config da loja FELIX via ORM
from superadmin.models import Loja
from crm_vendas.models import CRMConfig
from django_tenants.utils import schema_context

loja = Loja.objects.get(cpf_cnpj__contains='41449198000172')
print(f'Loja: {loja.nome} (schema: {loja.database_name})')

with schema_context(loja.database_name):
    config = CRMConfig.objects.first()
    if not config or not config.issnet_certificado:
        print('Certificado nao encontrado')
        sys.exit(1)
    cert_data = bytes(config.issnet_certificado)
    senha_cert = config.issnet_senha_certificado or ''
    usuario = config.issnet_usuario or ''
    senha = config.issnet_senha or ''
print(f'Certificado: {len(bytes(cert_data))} bytes')
print(f'Usuario: {usuario}')

# Salvar cert em temp file
cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
cert_tmp.write(bytes(cert_data))
cert_tmp.close()

try:
    client = ISSNetClient(
        usuario=usuario or '',
        senha=senha or '',
        certificado_path=cert_tmp.name,
        senha_certificado=senha_cert or '',
        ambiente='producao'
    )
    client._optante_simples = True
    client._incentivador_cultural = False
    client._regime_especial = '0'

    resultado = client.emitir_nfse(
        prestador_cnpj='41449198000172',
        prestador_inscricao_municipal='20130440',
        prestador_razao_social='FELIX REPRESENTACOES',
        tomador_cpf_cnpj='24758458000172',
        tomador_nome='LWK SISTEMAS LTDA',
        tomador_endereco={
            'logradouro': 'MARCOS MARKARIAN',
            'numero': '1025',
            'bairro': 'NOVA ALIANCA',
            'cidade': 'Ribeirao Preto',
            'uf': 'SP',
            'cep': '14026583',
        },
        servico_codigo='170602',
        servico_descricao='Teste emissao NFS-e via sistema',
        valor_servicos=Decimal('10.00'),
        aliquota_iss=Decimal('2.00'),
        numero_rps=998,
        serie_rps='NF',
    )
    print(f'Resultado: {resultado}')
finally:
    os.unlink(cert_tmp.name)
