# Manual de Integração — ISSNet Padrão Nacional (DPS/RTC)

**Sistema**: LWK Sistemas
**Município**: Ribeirão Preto/SP (cMun: 3543402)
**Provedor**: ISSNet (NotaControl)
**Padrão**: Nacional NFS-e (DPS — Declaração de Prestação de Serviço)
**Vigência**: A partir de 03/08/2026 (substituiu ABRASF 2.04)
**Atualizado em**: 09/08/2026

---

## 1. Visão Geral

O ISSNet Nacional usa o padrão DPS (Declaração de Prestação de Serviço) definido pela
Reforma Tributária. Diferente do ABRASF (que usava RPS), o Nacional trabalha com:

- **DPS** em vez de RPS
- **GerarNfse** para emissão síncrona de uma única DPS
- **EnviarLoteDpsSincrono** para lote (múltiplas DPS)
- Namespace: `http://www.sped.fazenda.gov.br/nfse`
- Assinatura: **RSA-SHA256** + C14N inclusiva (signxml)

### Endpoint

```
Produção: https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx
```

### Métodos Disponíveis (SOAPAction)

| Método | SOAPAction |
|--------|-----------|
| GerarNfse | http://www.sped.fazenda.gov.br/nfse/GerarNfse |
| RecepcionarLoteDpsSincrono | http://www.sped.fazenda.gov.br/nfse/RecepcionarLoteDpsSincrono |
| CancelarNfse | http://www.sped.fazenda.gov.br/nfse/CancelarNfse |
| ConsultarNfseDps | http://www.sped.fazenda.gov.br/nfse/ConsultarNfseDps |
| ConsultarUrlNfse | http://www.sped.fazenda.gov.br/nfse/ConsultarUrlNfse |

---

## 2. Autenticação

- **mTLS** (Mutual TLS): Certificado ICP-Brasil A1 (.pfx) do prestador
- O certificado é enviado no handshake TLS (não no XML)
- Senha do certificado: armazenada criptografada no banco

---

## 3. Estrutura do XML — DPS

### 3.1. Elemento DPS (versão 1.00)

```xml
<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
  <infDPS Id="DPS{cMun7}{tipoInsc1}{CNPJ14}{serie5}{nDPS15}">
    <tpAmb>1</tpAmb>                          <!-- 1=Produção -->
    <dhEmi>2026-08-07T00:00:00-03:00</dhEmi>  <!-- Data/hora emissão -->
    <verAplic>1.00</verAplic>                  <!-- Versão aplicativo -->
    <serie>00001</serie>                       <!-- Série (5 dígitos, zeros à esquerda) -->
    <nDPS>170</nDPS>                           <!-- Número sequencial da DPS -->
    <dCompet>2026-08-07</dCompet>              <!-- Data competência -->
    <tpEmit>1</tpEmit>                         <!-- 1=Prestador -->
    <cLocEmi>3543402</cLocEmi>                 <!-- Código município emissor -->

    <!-- PRESTADOR -->
    <prest>
      <CNPJ>41449198000172</CNPJ>
      <IM>20130440</IM>                        <!-- Inscrição Municipal -->
      <fone>16981402966</fone>                 <!-- Telefone (DDD+número, sem DDI) -->
      <regTrib>
        <opSimpNac>3</opSimpNac>               <!-- 1=Não optante, 3=MEI/Optante -->
        <regApTribSN>1</regApTribSN>           <!-- Regime apuração SN -->
        <regEspTrib>0</regEspTrib>             <!-- Regime especial tributação -->
      </regTrib>
    </prest>

    <!-- TOMADOR -->
    <toma>
      <CNPJ>24758458000172</CNPJ>              <!-- ou <CPF> para PF -->
      <xNome>LWK SISTEMAS LTDA</xNome>
      <end>
        <endNac>
          <cMun>3543402</cMun>                 <!-- Código município IBGE -->
          <CEP>14026583</CEP>
        </endNac>
        <xLgr>Rua Marcos Markarian</xLgr>
        <nro>1025</nro>
        <xBairro>Nova Alianca</xBairro>
      </end>
      <email>contato@empresa.com.br</email>
    </toma>

    <!-- SERVIÇO -->
    <serv>
      <locPrest>
        <cLocPrestacao>3543402</cLocPrestacao>  <!-- Município da prestação -->
      </locPrest>
      <cServ>
        <cTribNac>140101</cTribNac>             <!-- Código tributação nacional (6 dígitos) -->
        <cTribMun>140118</cTribMun>             <!-- Código tributação municipal (6 dígitos) -->
        <xDescServ>Descrição do serviço</xDescServ>
        <cNBS>118032900</cNBS>                  <!-- Código NBS (9 dígitos) -->
      </cServ>
    </serv>

    <!-- VALORES -->
    <valores>
      <vServPrest>
        <vServ>15.00</vServ>                    <!-- Valor total dos serviços -->
      </vServPrest>
      <trib>
        <tribMun>
          <tribISSQN>1</tribISSQN>              <!-- 1=Tributação normal -->
          <tpRetISSQN>1</tpRetISSQN>            <!-- 1=Não retido -->
          <pAliq>2.50</pAliq>                   <!-- Alíquota ISS (%) -->
        </tribMun>
        <totTrib>
          <pTotTribSN>2.50</pTotTribSN>        <!-- % total tributos (Simples Nacional) -->
        </totTrib>
      </trib>
    </valores>
  </infDPS>

  <!-- ASSINATURA DIGITAL (gerada pelo signxml) -->
  <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    ...
  </ds:Signature>
</DPS>
```

### 3.2. Formato do Id da infDPS

```
DPS + cMun(7) + tipoInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
```

Exemplo: `DPS354340224144919800017200001000000000000170`

- `3543402` = Ribeirão Preto
- `2` = Pessoa Jurídica
- `41449198000172` = CNPJ prestador
- `00001` = Série
- `000000000000170` = Número DPS (15 dígitos)

---

## 4. Assinatura Digital

### 4.1. Regras OBRIGATÓRIAS

| Item | Valor |
|------|-------|
| Algoritmo de assinatura | RSA-SHA256 (`rsa-sha256`) |
| Algoritmo de digest | SHA-256 (`sha256`) |
| Canonização (C14N) | Inclusiva (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315`) |
| Transform 1 | Enveloped Signature |
| Transform 2 | C14N Inclusiva |
| Reference URI | `#Id` do elemento `infDPS` |
| Posição | `<Signature>` como último filho do `<DPS>` |
| Namespace | `xmlns:ds="http://www.w3.org/2000/09/xmldsig#"` (prefixo `ds:`) |

### 4.2. Biblioteca utilizada: signxml (Python)

```python
from signxml import XMLSigner, methods

signer = XMLSigner(
    method=methods.enveloped,
    signature_algorithm="rsa-sha256",
    digest_algorithm="sha256",
    c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
)

signed_root = signer.sign(
    dps_element,          # lxml Element do <DPS>
    key=key_pem,          # Chave privada PEM
    cert=cert_pem,        # Certificado PEM
    reference_uri=f"#{inf_id}",  # Ex: #DPS354340224144919800017200001000000000000170
    id_attribute="Id",
)
```

### 4.3. REGRAS CRÍTICAS sobre a assinatura

1. **A DPS deve ser assinada ISOLADAMENTE** (como documento raiz, com `xmlns` declarado no `<DPS>`)
2. **O XML NÃO pode sofrer nenhuma alteração** após ser assinado (sem pretty-print, sem reformatação)
3. **A `<Signature>` deve ser inline** (sem espaços/newlines extras entre tags) — o signxml faz isso automaticamente
4. **O `xmlns="http://www.sped.fazenda.gov.br/nfse"`** deve estar declarado no `<DPS>` quando assinado isoladamente
5. **NÃO usar SHA1** — o signxml 5.x bloqueia por segurança e o ISSNet aceita SHA256

### 4.4. Por que NÃO usar xmlsec (python-xmlsec)

O python-xmlsec gera espaços/newlines entre os elementos da `<Signature>`:
```xml
<Signature>                    <!-- espaços extras! -->
<SignedInfo>
```
Isso causa E0714 (erro na assinatura) no ISSNet porque o servidor não tolera whitespace extra.

O **signxml** gera tudo inline:
```xml
<ds:Signature><ds:SignedInfo><ds:CanonicalizationMethod.../>...
```

---

## 5. Envelope SOAP

### 5.1. Estrutura do Envelope (GerarNfse)

```xml
<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Header/>
  <soapenv:Body>
    <GerarNfse xmlns="http://www.sped.fazenda.gov.br/nfse">
      <nfseCabecMsg>
        <cabecalho versao="1.00" xmlns="http://www.sped.fazenda.gov.br/nfse">
          <versaoDados>1.00</versaoDados>
        </cabecalho>
      </nfseCabecMsg>
      <nfseDadosMsg>
        <GerarNfseEnvio xmlns="http://www.sped.fazenda.gov.br/nfse">
          <!-- DPS assinada inserida aqui como XML literal -->
          <DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
            ...
          </DPS>
        </GerarNfseEnvio>
      </nfseDadosMsg>
    </GerarNfse>
  </soapenv:Body>
</soapenv:Envelope>
```

### 5.2. Regras do Envelope

| Regra | Detalhe |
|-------|---------|
| **NÃO declarar `xmlns:nfse`** no `<soapenv:Envelope>` | Evita herança de namespace na canonização |
| Operação com `xmlns` local | `<GerarNfse xmlns="http://www.sped.fazenda.gov.br/nfse">` |
| Dados aninhados (literal) | XML da DPS inserido SEM escapar (não como xsd:string) |
| Cabeçalho aninhado | `<cabecalho>` inserido literal dentro de `<nfseCabecMsg>` |
| Content-Type | `text/xml; charset=utf-8` |
| SOAPAction | `"http://www.sped.fazenda.gov.br/nfse/GerarNfse"` (entre aspas) |
| User-Agent | Livre (ex: `LWK-Sistemas/ISSNet-Nacional`) |

### 5.3. Por que NÃO usar `xmlns:nfse` no envelope

Se o envelope declarar `xmlns:nfse="http://www.sped.fazenda.gov.br/nfse"`:

```xml
<soapenv:Envelope xmlns:soapenv="..." xmlns:nfse="http://www.sped.fazenda.gov.br/nfse">
```

A canonização C14N **inclusiva** do `infDPS` incluirá `xmlns:soapenv` como namespace ancestor visível, mudando o digest e invalidando a assinatura (E0714).

Com apenas `xmlns:soapenv` no root, o namespace `soapenv` **ainda aparece** na canonização inclusiva, mas o ISSNet valida a assinatura **extraindo o XML do envelope** antes de verificar.

---

## 6. Fluxo de Emissão (Passo a Passo)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Montar XML da DPS (com xmlns no <DPS>)                  │
│  2. Assinar DPS isolada com signxml (SHA256, C14N incl.)    │
│  3. Envolver em <GerarNfseEnvio> (string concatenation)     │
│  4. Montar envelope SOAP (sem xmlns:nfse no root)           │
│  5. POST via mTLS para o endpoint                           │
│  6. Parsear resposta (extrair nNFSe, cStat)                │
│  7. Salvar no banco + enviar email ao tomador               │
└─────────────────────────────────────────────────────────────┘
```

### 6.1. Código resumido

```python
# 1. Construir DPS
dps_xml = construir_xml_dps(...)  # retorna string XML

# 2. Parsear e assinar
dps_element = etree.fromstring(dps_xml.encode())
signed_root = signer.sign(dps_element, key=key_pem, cert=cert_pem, ...)
dps_assinada = etree.tostring(signed_root, encoding="unicode")

# 3. Montar GerarNfseEnvio
xml_dados = f'<GerarNfseEnvio xmlns="{NS}">{dps_assinada}</GerarNfseEnvio>'

# 4. Montar envelope SOAP
envelope = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
    '<soapenv:Header/><soapenv:Body>'
    f'<GerarNfse xmlns="{NS}">'
    f'<nfseCabecMsg>{cabecalho}</nfseCabecMsg>'
    f'<nfseDadosMsg>{xml_dados}</nfseDadosMsg>'
    '</GerarNfse>'
    '</soapenv:Body></soapenv:Envelope>'
)

# 5. Enviar com mTLS
response = requests.post(url, data=envelope.encode(), headers=headers, cert=(pem_cert, pem_key))
```

---

## 7. Resposta de Sucesso

```xml
<GerarNfseResponse xmlns="http://www.sped.fazenda.gov.br/nfse">
  <GerarNfseResposta>
    <ListaNfse>
      <CompNfse>
        <NFSe versao="1.00">
          <infNFSe Id="NFS...">
            <nNFSe>167</nNFSe>       <!-- Número da NFS-e -->
            <cStat>100</cStat>       <!-- 100 = Autorizada -->
            <dhProc>2026-08-07T...</dhProc>
            <nDFSe>167</nDFSe>
            ...
          </infNFSe>
        </NFSe>
      </CompNfse>
    </ListaNfse>
  </GerarNfseResposta>
</GerarNfseResponse>
```

### Indicadores de sucesso:
- `<cStat>100</cStat>` — Autorizada
- `<ListaNfse>` presente (não `<ListaMensagemRetorno>`)
- `<nNFSe>` com número da nota

---

## 8. Erros Comuns

| Código | Mensagem | Causa | Solução |
|--------|----------|-------|---------|
| E0714 | Erro na assinatura | Digest invalidado | Verificar C14N, xmlns, formatação |
| E183 | Desacordo com XML Schema | Campos obrigatórios faltando | Verificar cTribMun, pTotTribSN |
| E160 | Arquivo fora do padrão | Estrutura XML incorreta | Verificar ordem dos elementos |
| E212 | NFS-e não encontrada | Nota não existe (consulta) | Verificar número e série |
| EM003 | Assinatura do Lote obrigatória | Falta assinatura no LoteDps | Usar GerarNfse (DPS única) |
| — | DPS já existe | Número DPS duplicado | Incrementar contador |

---

## 9. Campos Obrigatórios (Ribeirão Preto)

| Campo | Obrigatório | Formato | Observação |
|-------|-------------|---------|------------|
| cTribNac | Sim | 6 dígitos | Ex: 140101 |
| cTribMun | Sim | 6 dígitos | Ex: 140118 (código do contribuinte no ISSNet) |
| cNBS | Sim | 9 dígitos | Ex: 118032900 |
| pTotTribSN | Sim (Simples Nacional) | Decimal | Obrigatório para ME/EPP optante SN |
| IM | Sim | String | Inscrição Municipal do prestador |
| pAliq | Sim | Decimal | Alíquota ISS |

---

## 10. Arquivos do Sistema

| Arquivo | Função |
|---------|--------|
| `issnet_nacional_client.py` | Client principal (emitir, cancelar, consultar) |
| `issnet_nacional_xml_builder.py` | Construção do XML DPS |
| `nacional/xml_signer.py` | Assinatura digital (xmlsec — legado) |
| `issnet_soap.py` | Montagem do envelope SOAP |
| `emissao_issnet_nacional_loja.py` | Orquestração da emissão por loja |
| `service.py` | Service layer (NFSeService) |
| `persistencia_nfse_loja.py` | Gravação no banco |
| `danfe.py` | URL da DANFE / PDF |
| `issnet_response.py` | Parsing de resposta SOAP |
| `issnet_constants.py` | Constantes (URLs, namespaces, SOAPActions) |

---

## 11. Configuração por Loja (CRMConfig)

| Campo | Descrição |
|-------|-----------|
| `provedor_nf` | `"issnet"` |
| `issnet_usar_padrao_nacional` | Boolean — força DPS/RTC (também obrigatório desde 31/07/2026) |
| `issnet_certificado` | Bytes do .pfx (BinaryField) |
| `issnet_senha_certificado` | Senha do certificado (criptografada) |
| `issnet_inscricao_municipal` | IM do prestador |
| `issnet_serie_rps` | Série da DPS (default: "1") |
| `codigo_tributacao_municipal` | cTribMun (6 dígitos) |
| `aliquota_iss` | Alíquota ISS (%) |
| `optante_simples_nacional` | Boolean |

---

## 12. Dependências Python

```
signxml==5.1.0        # Assinatura digital (RSA-SHA256, inline)
lxml                  # Parse/serialização XML
cryptography          # Manipulação de certificados .pfx
requests              # HTTP com mTLS
python-xmlsec         # Legado (não usar para Nacional)
```

---

## 13. Histórico de Problemas Resolvidos

| Data | Problema | Solução |
|------|----------|---------|
| 03/08/2026 | E183 Schema | Adicionar cTribMun, pTotTribSN |
| 03-06/08/2026 | E0714 Assinatura (xmlsec) | Trocar para signxml (inline, sem whitespace) |
| 07/08/2026 | E0714 com C14N inclusiva no SOAP | Remover xmlns:nfse do envelope |
| 07/08/2026 | Falha ao gravar (NOT NULL) | codigo_verificacao aceita vazio |
| 07/08/2026 | Resposta sucesso tratada como erro | Corrigir extrair_erros/issnet_erro_assinatura |
| 08/08/2026 | codigo_verificacao vazio no e-mail | Extrair chave de `infNFSe Id="NFS…"` + fallback portal |

---

## 14. Notas Importantes

1. **O endpoint ABRASF e o Nacional são SEPARADOS** — notas emitidas pelo Nacional não aparecem no ConsultarUrlNfse do ABRASF
2. **O ISSNet RP aceita tpAmb=1 sempre** (mesmo em homologação — não tem ambiente de teste real)
3. **A chave de acesso vem em `infNFSe/@Id`** no formato `NFS{chave50}` (persistida em `codigo_verificacao`)
4. **ConsultarUrlNfse pode falhar (E160)** — o e-mail/WhatsApp usam chave + portal de autenticidade como fallback
5. **Para consultar nota no portal**: acessar `notaeletronica.com.br/ribeiraopreto` logado com certificado
6. **Cada DPS tem número único** — reutilizar número gera erro "DPS já existe"
7. **O certificado deve ser do CNPJ do prestador** (ICP-Brasil A1)
