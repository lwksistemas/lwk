# Email para suporte@notacontrol.com.br (att. Caio)

**Assunto:** E0714 "Erro na assinatura" persiste após aplicar todas as orientações — RecepcionarLoteDpsSincrono (Felix Representações, IM 20130440)

---

Prezados, olá Caio,

Seguindo nossa conversa de hoje e de 03/08, implementamos **todas** as orientações passadas para corrigir o erro `E0714 - Arquivo enviado com erro na assinatura` na operação `RecepcionarLoteDpsSincrono`:

1. Assinatura **RSA-SHA1** com canonização **inclusiva** (C14N `REC-xml-c14n-20010315`), conforme orientado.
2. Envelope SOAP declarando **apenas** `xmlns:soapenv` e `xmlns:nfse` (removemos `xsi`/`xsd`).
3. Elemento de dados (`EnviarLoteDpsSincronoEnvio`, equivalente ao `GerarNfseEnvio` do print que você enviou) declarando `xmlns="http://www.sped.fazenda.gov.br/nfse"` localmente.
4. `nfseCabecMsg`/`nfseDadosMsg` com prefixo `nfse:`, conforme seu exemplo de referência.
5. Cabeçalho `<cabecalho versao="1.01" xmlns="...">` com a ordem de atributos exatamente como no print que você enviou.
6. Testamos também assinar o DPS/LoteDps **já dentro do documento final montado** (não como XML isolado inserido depois via string), para eliminar qualquer efeito de canonização por namespaces herdados do envelope.

**Resultado: o erro `E0714` persiste, idêntico, em todas as combinações testadas.**

## Envelope de exemplo (anexo)

Anexamos o **envelope SOAP completo** que estamos enviando para `RecepcionarLoteDpsSincrono` (arquivo `envelope_issnet_para_suporte.xml`), incluindo as tags `<Signature>` da DPS e do Lote. Usamos um número de DPS fictício (999001) e como tomador a nossa própria empresa (LWK Sistemas), então não há dados sensíveis de terceiros.

- Certificado: e-CNPJ A1 da Felix Representações (AC Soluti), válido até 16/10/2026.
- `Reference URI="#DPS354340224144919800017200001000000000000999001"` (DPS) e `Reference URI="#Lote999001"` (Lote).
- Verificação **local** da assinatura (usando o certificado público, antes do envio) passa sem erros.

## Pergunta direta

Você mencionou que a assinatura estava passando nos dias 01 e 02/08 e que pode ter havido alteração em "nosso assinador". Não identificamos nenhuma mudança estrutural na lógica de assinatura em si (mesma biblioteca `xmlsec`, mesmo algoritmo desde então) — apenas ajustes no envelope/namespaces conforme suas orientações.

Poderia comparar o envelope anexo com uma requisição que vocês têm registrada como aceita para este mesmo contribuinte (IM 20130440) nos dias 01-02/08, e apontar exatamente qual campo/estrutura está diferente?

## Dados para contato

- Empresa: LWK Sistemas LTDA (CNPJ 24.758.458/0001-72)
- Responsável: Luiz Henrique Felix
- Telefone: (16) 98140-2966
- Contribuinte: FELIX REPRESENTACOES E COMERCIO LTDA (CNPJ 41.449.198/0001-72, IM 20130440)

Agradeço a atenção e aguardo retorno.

Atenciosamente,
Luiz Henrique Felix
LWK Sistemas
