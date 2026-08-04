# Integração ISSNet — Padrão Nacional (DPS / RTC) — Status

## Resumo Executivo

A integração passou de erros estruturais graves (E183/E160, operação SOAP
inexistente) para **apenas erros de dados cadastrais específicos do
contribuinte** (código de tributação municipal/nacional não registrado para
a Felix em Ribeirão Preto). Faltam apenas os códigos corretos, cadastrados
junto ao município, para a emissão funcionar de ponta a ponta.

---

## ✅ Causas-raiz identificadas e corrigidas nesta sessão

1. **Operação SOAP errada**: código usava `GerarNfse` (não existe no
   WSDL real do padrão nacional). Corrigido para `RecepcionarLoteDpsSincrono`
   (confirmado via WSDL obtido com mTLS). Isso sozinho já eliminava os
   erros crônicos `E183`/`E160` genéricos.
2. **Assinatura em SHA-1**: DPS v1.01 exige RSA-SHA256 (`E0714` se SHA-1).
   Corrigido em `nacional/xml_signer.py` (`_assinar_dps_com_signxml`) e
   `issnet_nacional_client.py` (`usar_sha256=True`).
3. **Lote sem assinatura**: `RecepcionarLoteDpsSincrono` exige também a
   assinatura do `<LoteDps>` (`EM003` se ausente). Implementada
   `_assinar_lote_com_signxml` (signxml, Signature como irmã de `LoteDps`).
4. **IBSCBS com estrutura errada**: a implementação antiga usava elementos
   que não existem no XSD real (`cLocalidadeIncid`, `totCIBS`, etc). Reescrita
   conforme `TCRTCInfoIBSCBS` real: `finNFSe`, `indFinal`, `cIndOp`, `indDest`,
   `valores/trib/gIBSCBS/CST+cClassTrib`.
5. **pTotTribSN**: ME/EPP (Simples Nacional) não pode usar `indTotTrib=0`;
   é obrigatório `pTotTribSN`. Corrigido em `emissao_issnet_nacional_loja.py`
   (fallback usa a própria alíquota do ISS como aproximação declarativa).
6. **`cTribMun` obrigatório na prática**: o XSD publicado declara
   `cTribMun` como `minOccurs="0"`, mas o validador real do ISSNet rejeita
   com `E160` genérico ("Arquivo em desacordo com o XML Schema") quando
   ausente — **confirmado empiricamente** reintroduzindo o campo. Mantido
   sempre presente (usa `codigo_servico_municipal` como fallback).

## ⚠️ Pendências — dados cadastrais reais do contribuinte

Erros de negócio restantes (schema OK, servidor processa a DPS):

```
O código de tributação municipal informado não existe ou não está
administrado pelo município de incidência do ISSQN na data de competência
informada na DPS.

O Código de tributação informado não pertence a este contribuinte.
```

Isso significa que os valores usados (`cTribNac=140101`, `cTribMun=140`,
derivados de `CRMConfig.codigo_tributacao_nacional`/`codigo_servico_municipal`
da loja Felix) **não são os códigos realmente cadastrados** no ISSNet de
Ribeirão Preto para o CNPJ 41.449.198/0001-72. É necessário:

1. Confirmar junto à Prefeitura/ISSNet de Ribeirão Preto (ou no portal do
   contribuinte) qual é o **código de tributação nacional (cTribNac)** e o
   **código de tributação municipal (cTribMun)** efetivamente cadastrados
   para a Felix.
2. Atualizar `CRMConfig.codigo_tributacao_nacional` e
   `CRMConfig.codigo_servico_municipal` da loja com os valores corretos.
3. Re-testar (`python3 manage.py shell < scripts/test_issnet_felix.py`, ou
   script equivalente).

---

## Envelope SOAP (atualizado)
- Endpoint produção: `https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx`
- Endpoint homologação: `https://nfse.issnetonline.com.br/wsnfsenacional/homologacao/nfse.asmx`
- Operação: `RecepcionarLoteDpsSincrono` (não `GerarNfse` — esta operação **não existe**)
- SOAPAction: `http://www.sped.fazenda.gov.br/nfse/RecepcionarLoteDpsSincrono`
- mTLS com certificado ICP-Brasil A1

## Certificado Digital
- CNPJ: 41449198000172 (FELIX REPRESENTACOES E COMERCIO LTDA)
- Tipo: A1 (PJ), Soluti Multipla v5
- Validade: 16/10/2025 a 16/10/2026 (**válido**)

---

## Configuração da Loja Felix (loja_id=4)

| Campo | Valor |
|-------|-------|
| CNPJ Prestador | 41.449.198/0001-72 |
| Inscrição Municipal | 20130440 |
| Optante Simples Nacional | Sim |
| Código Tributação Nacional | 140101 (**a confirmar se é o cadastrado**) |
| Código Tributação Municipal | 140 (**a confirmar se é o cadastrado**) |
| cNBS | 104033000 |
| Alíquota ISS | 2.50% |
| Ambiente | Produção |
| Certificado | Configurado (BinaryField) |

---

## Arquivos Relevantes

| Arquivo | Função |
|---------|--------|
| `nfse_integration/nacional/xml_builder.py` | Constrói XML DPS base |
| `nfse_integration/issnet_nacional_xml_builder.py` | Extensões ISSNet (cNBS, IBSCBS, envelope) |
| `nfse_integration/issnet_nacional_client.py` | Cliente SOAP + assinatura |
| `nfse_integration/nacional/xml_signer.py` | Assinatura digital (xmlsec/signxml) |
| `nfse_integration/issnet_soap.py` | Montagem envelope SOAP |
| `nfse_integration/issnet_constants.py` | URLs, namespaces, SOAP actions |
| `nfse_integration/emissao_issnet_nacional_loja.py` | Orquestrador emissão loja |
| `nfse_integration/service.py` | NFSeService (entry point) |
| `nfse_integration/queue_tasks.py` | Tarefas django-q |

---

## Documentação de Referência

- Manual integração: `https://www.notacontrol.com.br/download/nfse/Manual_integracao_v101.pdf`
- XSD local: `/home/luiz/Documentos/LWK/nacional/Schemas/1.01/`
- Suporte técnico: `suporte@notacontrol.com.br`
