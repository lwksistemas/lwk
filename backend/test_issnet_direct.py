"""Teste direto do webservice ISSNet sem zeep."""
import os
import sys
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_production'
django.setup()

import requests

url = 'https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx'

xml_nfse = (
    '<EnviarLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">'
    '<LoteRps versao="2.04">'
    '<NumeroLote>999</NumeroLote>'
    '<Prestador>'
    '<CpfCnpj><Cnpj>41449198000172</Cnpj></CpfCnpj>'
    '<InscricaoMunicipal>20130440</InscricaoMunicipal>'
    '</Prestador>'
    '<QuantidadeRps>1</QuantidadeRps>'
    '<ListaRps>'
    '<Rps>'
    '<InfDeclaracaoPrestacaoServico Id="rps999">'
    '<Rps>'
    '<IdentificacaoRps>'
    '<Numero>999</Numero>'
    '<Serie>NF</Serie>'
    '<Tipo>1</Tipo>'
    '</IdentificacaoRps>'
    '<DataEmissao>2026-04-12T18:00:00</DataEmissao>'
    '<Status>1</Status>'
    '</Rps>'
    '<Competencia>2026-04-12</Competencia>'
    '<Servico>'
    '<Valores>'
    '<ValorServicos>10.00</ValorServicos>'
    '<ValorDeducoes>0.00</ValorDeducoes>'
    '<ValorIss>0.20</ValorIss>'
    '<Aliquota>2.00</Aliquota>'
    '<DescontoIncondicionado>0.00</DescontoIncondicionado>'
    '<DescontoCondicionado>0.00</DescontoCondicionado>'
    '</Valores>'
    '<IssRetido>2</IssRetido>'
    '<ItemListaServico>170602</ItemListaServico>'
    '<CodigoTributacaoMunicipio>170602</CodigoTributacaoMunicipio>'
    '<Discriminacao>Teste direto</Discriminacao>'
    '<CodigoMunicipio>3543402</CodigoMunicipio>'
    '<ExigibilidadeISS>1</ExigibilidadeISS>'
    '<MunicipioIncidencia>3543402</MunicipioIncidencia>'
    '</Servico>'
    '<Prestador>'
    '<CpfCnpj><Cnpj>41449198000172</Cnpj></CpfCnpj>'
    '<InscricaoMunicipal>20130440</InscricaoMunicipal>'
    '</Prestador>'
    '<TomadorServico>'
    '<IdentificacaoTomador>'
    '<CpfCnpj><Cnpj>24758458000172</Cnpj></CpfCnpj>'
    '</IdentificacaoTomador>'
    '<RazaoSocial>LWK SISTEMAS LTDA</RazaoSocial>'
    '<Endereco>'
    '<Endereco>MARCOS MARKARIAN</Endereco>'
    '<Numero>1025</Numero>'
    '<Bairro>NOVA ALIANCA</Bairro>'
    '<CodigoMunicipio>3543402</CodigoMunicipio>'
    '<Uf>SP</Uf>'
    '<Cep>14026583</Cep>'
    '</Endereco>'
    '</TomadorServico>'
    '<OptanteSimplesNacional>1</OptanteSimplesNacional>'
    '<IncentivoFiscal>2</IncentivoFiscal>'
    '</InfDeclaracaoPrestacaoServico>'
    '</Rps>'
    '</ListaRps>'
    '</LoteRps>'
    '</EnviarLoteRpsEnvio>'
)

cabec = '<cabecalho xmlns="http://www.abrasf.org.br/nfse.xsd" versao="2.04"><versaoDados>2.04</versaoDados></cabecalho>'

# Escapar XML para dentro do SOAP (usar CDATA)
soap = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:ws="http://nfse.abrasf.org.br">'
    '<soap:Body>'
    '<ws:RecepcionarLoteRpsSincrono>'
    '<ws:nfseCabecMsg><![CDATA[' + cabec + ']]></ws:nfseCabecMsg>'
    '<ws:nfseDadosMsg><![CDATA[' + xml_nfse + ']]></ws:nfseDadosMsg>'
    '</ws:RecepcionarLoteRpsSincrono>'
    '</soap:Body>'
    '</soap:Envelope>'
)

headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://nfse.abrasf.org.br/RecepcionarLoteRpsSincrono',
}

print(f'Enviando para {url}...')
print(f'XML NFS-e ({len(xml_nfse)} bytes)')
r = requests.post(url, data=soap.encode('utf-8'), headers=headers, timeout=30)
print(f'HTTP {r.status_code}')
print(r.text[:3000])
