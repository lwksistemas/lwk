"""Teste ISSNet com assinatura digital usando certificado da loja."""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_production'
django.setup()

from nfse_integration.issnet_client import ISSNetClient
from decimal import Decimal
from datetime import datetime
import tempfile

# Buscar config da loja FELIX
from django.db import connection
with connection.cursor() as c:
    c.execute("SET search_path TO loja_41449198000172")
    c.execute("SELECT issnet_certificado, issnet_senha_certificado, issnet_usuario, issnet_senha FROM crm_vendas_crmconfig LIMIT 1")
    row = c.fetchone()

if not row or not row[0]:
    print('Certificado nao encontrado no banco')
    sys.exit(1)

cert_data, senha_cert, usuario, senha = row
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
