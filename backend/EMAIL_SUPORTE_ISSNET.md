# Email para suporte@notacontrol.com.br

**Assunto:** Código de tributação municipal (cTribMun) para NFS-e Nacional (DPS v1.01) — Ribeirão Preto

---

Prezados,

Somos a empresa **LWK Sistemas** (CNPJ 24.758.458/0001-72), desenvolvedora de software de gestão que realiza integração via webservice para emissão de NFS-e em nome do contribuinte **FELIX REPRESENTACOES E COMERCIO LTDA** (CNPJ 41.449.198/0001-72, IM 20130440) de Ribeirão Preto/SP.

Já concluímos a migração técnica do padrão ABRASF 2.04 para o **Padrão Nacional (DPS v1.01)**: envelope SOAP, assinatura digital (RSA-SHA256) da DPS e do lote, e o bloco IBSCBS estão implementados e sendo aceitos pelo webservice de produção (`https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx`, operação `RecepcionarLoteDpsSincrono`).

## Problema atual

Ao enviar a DPS, recebemos os seguintes retornos de negócio:

```
O código de tributação municipal informado não existe ou não está
administrado pelo município de incidência do ISSQN na data de competência
informada na DPS.

O Código de tributação informado não pertence a este contribuinte.
```

## O que já confirmamos

Consultamos a **Ficha Cadastral** da Felix Representações no sistema Nota Control e confirmamos:

- **Atividade Principal cadastrada**: item **14.01 - Conserto, Restauração de Computadores e Similares** (Grupo Fiscal 14 - Serviços relativos a bens de terceiros), código interno do sistema **140118**, marcado como atividade principal (X).
- Optante Simples Nacional: Sim
- Alíquota ISS: 2,50%
- Inscrição Municipal: 20130440

Com base nisso, estamos enviando `cTribNac=140101` (item nacional 14.01) no campo `cServ/cTribNac` da DPS, mas o webservice rejeita esse código como não pertencente ao contribuinte.

**Testamos também o item 17.06** (`cTribNac=170601`) e obtivemos exatamente o mesmo erro — ou seja, o problema **não depende do item escolhido**.

## Evidência: NFS-e reais já emitidas e aceitas para este contribuinte

Temos duas NFS-e emitidas com sucesso pelo webservice ABRASF 2.04 (antes da migração), comprovando que ambos os itens estão devidamente cadastrados:

| NFS-e | Data | ItemListaServico | CodigoTributacaoMunicipio | CNAE |
|---|---|---|---|---|
| 157 | 31/07/2026 | 17.06 | **170602** | 7319002 |
| 158 | 31/07/2026 | 14.01 | **140118** | 9511800 |

Ou seja, o código municipal real de 6 dígitos cadastrado é `140118`/`170602` — não conseguimos derivar a partir disso um valor de 3 dígitos válido para o campo `cTribMun` da DPS Nacional.

## Dúvidas específicas

1. Qual é o valor correto de **`cTribMun`** (código de 3 dígitos, conforme `xs:pattern [0-9]{3}` do XSD nacional `TCCodTribMun`) para o item 14.01 no município de Ribeirão Preto? O código interno "140118" do sistema Nota Control tem 6 dígitos e não se encaixa nesse padrão.
2. O cadastro do contribuinte (IM 20130440) já foi migrado/vinculado à tabela de correlação `cTribNac` ↔ `cTribMun` do **Sistema Nacional NFS-e** (Reforma Tributária)? Se não, como solicitamos essa vinculação?
3. Existe uma tabela pública de correlação entre os códigos locais do Nota Control (ex.: "140118") e os códigos `cTribNac`/`cTribMun` do padrão nacional para Ribeirão Preto?

## Dados para contato

- Empresa: LWK Sistemas LTDA (CNPJ 24.758.458/0001-72)
- Responsável: Luiz Henrique Felix
- Email: consultorluizfelix@hotmail.com
- Telefone: (16) 98140-2966
- Contribuinte: FELIX REPRESENTACOES E COMERCIO LTDA (CNPJ 41.449.198/0001-72, IM 20130440)

Agradeço a atenção e aguardo orientações.

Atenciosamente,
Luiz Henrique Felix
LWK Sistemas
