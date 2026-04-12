"""Teste ISSNet com assinatura digital usando certificado da loja."""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_production'
django.setup()

from nfse_integration.issnet_client import ISSNetClient
from decimal import Decimal
from datetime import datetime
import tempfile

# Buscar config da loja FELIX via SQL direto
from superadmin.models import Loja
loja = Loja.objects.get(cpf_cnpj__contains='41449198000172')
print(f'Loja: {loja.nome} (schema: {loja.database_name})')

import psycopg2
db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()
cur.execute(f"SET search_path TO {loja.database_name}, public")
cur.execute("SELECT issnet_certificado, issnet_senha_certificado, issnet_usuario, issnet_senha FROM crm_vendas_crmconfig LIMIT 1")
row = cur.fetchone()
cur.close()
conn.close()

if not row or not row[0]:
    print('Certificado nao encontrado')
    sys.exit(1)

cert_data = bytes(row[0])
senha_cert = row[1] or ''
usuario = row[2] or ''
senha = row[3] or ''
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
