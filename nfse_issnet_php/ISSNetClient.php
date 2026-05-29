<?php
/**
 * Cliente ISSNet ABRASF 2.04 — Ribeirão Preto
 * Operações: Emissão, Cancelamento, Consulta URL (DANFE), Reenvio Email
 * 
 * Requisitos: PHP 8.1+, ext-openssl, ext-curl, ext-dom
 * Dependência: composer require robrichards/xmlseclibs
 * Certificado: A1 (.pfx) | Assinatura: RSA-SHA1
 */

namespace LWK\NFSe;

class ISSNetClient
{
    private string $usuario;
    private string $senha;
    private string $certificadoPath;
    private string $senhaCertificado;
    private string $baseUrl;

    const WSDL_PRODUCAO = 'https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx';
    const NS_NFSE = 'http://www.abrasf.org.br/nfse.xsd';
    const COD_MUNICIPIO = '3543402';
    const CABEC_MSG = '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.04</versaoDados></cabecalho>';

    public function __construct(string $usuario, string $senha, string $certificadoPath, string $senhaCertificado, string $ambiente = 'producao')
    {
        $this->usuario = $usuario;
        $this->senha = $senha;
        $this->certificadoPath = $certificadoPath;
        $this->senhaCertificado = $senhaCertificado;
        $this->baseUrl = $ambiente === 'homologacao'
            ? 'https://nfse.issnetonline.com.br/wsnfsenacional/homologacao/nfse.asmx'
            : self::WSDL_PRODUCAO;
    }

    // ═══════════════════════════════════════════════════════════════════
    // EMISSÃO
    // ═══════════════════════════════════════════════════════════════════

    public function emitirNfse(array $dados): array
    {
        $xml = $this->construirXmlEmissao($dados);
        $xmlAssinado = $this->assinarEmissao($xml);
        $envelope = $this->envelope('RecepcionarLoteRps', $xmlAssinado);
        $resp = $this->post($envelope, 'http://nfse.abrasf.org.br/RecepcionarLoteRps');

        if ($this->isFault($resp)) {
            $xmlSync = str_replace(['EnviarLoteRpsEnvio'], ['EnviarLoteRpsSincronoEnvio'], $xmlAssinado);
            $envelope = $this->envelope('RecepcionarLoteRpsSincrono', $xmlSync);
            $resp = $this->post($envelope, 'http://nfse.abrasf.org.br/RecepcionarLoteRpsSincrono');
        }
        return $this->parseEmissao($resp);
    }

    // ═══════════════════════════════════════════════════════════════════
    // CANCELAMENTO
    // ═══════════════════════════════════════════════════════════════════

    public function cancelarNfse(string $numeroNf, string $cnpj, string $im, string $codigo = '1'): array
    {
        $cnpj = preg_replace('/\D/', '', $cnpj);
        $ns = self::NS_NFSE;
        $xml = "<CancelarNfseEnvio xmlns=\"{$ns}\"><Pedido Id=\"Pedido1\"><InfPedidoCancelamento>"
            . "<IdentificacaoNfse><Numero>{$numeroNf}</Numero><CpfCnpj><Cnpj>{$cnpj}</Cnpj></CpfCnpj>"
            . "<InscricaoMunicipal>{$im}</InscricaoMunicipal><CodigoMunicipio>3543402</CodigoMunicipio>"
            . "</IdentificacaoNfse><CodigoCancelamento>{$codigo}</CodigoCancelamento>"
            . "</InfPedidoCancelamento></Pedido></CancelarNfseEnvio>";

        $xmlAssinado = $this->assinarCancelamento($xml);
        $envelope = $this->envelope('CancelarNfse', $xmlAssinado);
        $resp = $this->post($envelope, 'http://nfse.abrasf.org.br/CancelarNfse');
        return $this->parseCancelamento($resp);
    }

    // ═══════════════════════════════════════════════════════════════════
    // CONSULTAR URL (PDF DANFE REAL)
    // ═══════════════════════════════════════════════════════════════════

    public function consultarUrlNfse(string $numeroNf, string $cnpj, string $im): array
    {
        $cnpj = preg_replace('/\D/', '', $cnpj);
        $ns = self::NS_NFSE;
        $xml = "<ConsultarUrlNfseEnvio xmlns=\"{$ns}\"><Prestador><CpfCnpj><Cnpj>{$cnpj}</Cnpj></CpfCnpj>"
            . "<InscricaoMunicipal>{$im}</InscricaoMunicipal></Prestador>"
            . "<NumeroNfse>{$numeroNf}</NumeroNfse></ConsultarUrlNfseEnvio>";

        $xmlAssinado = $this->assinarConsulta($xml);
        $envelope = $this->envelope('ConsultarUrlNfse', $xmlAssinado);
        $resp = $this->post($envelope, 'http://nfse.abrasf.org.br/ConsultarUrlNfse');

        if (preg_match('/<Url[^>]*>(https?:\/\/[^<]+)<\/Url>/i', $resp, $m)) {
            return ['success' => true, 'url' => trim($m[1])];
        }
        if (preg_match('/>(https?:\/\/nfse[^<]+)</i', $resp, $m)) {
            return ['success' => true, 'url' => trim($m[1])];
        }
        return ['success' => false, 'error' => 'URL não encontrada'];
    }

    // ═══════════════════════════════════════════════════════════════════
    // ASSINATURA DIGITAL (RSA-SHA1 com xmlseclibs)
    // ═══════════════════════════════════════════════════════════════════

    private function assinarEmissao(string $xml): string
    {
        $doc = new \DOMDocument(); $doc->loadXML($xml);
        $pem = $this->getPem();
        // 1ª: Rps
        $rps = $doc->getElementsByTagNameNS(self::NS_NFSE, 'Rps')->item(0);
        if ($rps) $this->sign($doc, $rps, $pem, '');
        // 2ª: raiz
        $this->sign($doc, $doc->documentElement, $pem, '');
        return $doc->saveXML();
    }

    private function assinarCancelamento(string $xml): string
    {
        $doc = new \DOMDocument(); $doc->loadXML($xml);
        $pem = $this->getPem();
        $pedido = $doc->getElementsByTagNameNS(self::NS_NFSE, 'Pedido')->item(0);
        if ($pedido) {
            $pedido->setAttribute('Id', 'Pedido1');
            $this->sign($doc, $pedido, $pem, '#Pedido1');
        }
        return $doc->saveXML();
    }

    private function assinarConsulta(string $xml): string
    {
        $doc = new \DOMDocument(); $doc->loadXML($xml);
        $pem = $this->getPem();
        $this->sign($doc, $doc->documentElement, $pem, '');
        return $doc->saveXML();
    }

    private function sign(\DOMDocument $doc, \DOMElement $node, array $pem, string $uri): void
    {
        $dSig = new \RobRichards\XMLSecLibs\XMLSecurityDSig();
        $dSig->setCanonicalMethod(\RobRichards\XMLSecLibs\XMLSecurityDSig::EXC_C14N);
        $dSig->addReference($node, \RobRichards\XMLSecLibs\XMLSecurityDSig::SHA1,
            ['http://www.w3.org/2000/09/xmldsig#enveloped-signature'], ['uri' => $uri]);
        $key = new \RobRichards\XMLSecLibs\XMLSecurityKey(
            \RobRichards\XMLSecLibs\XMLSecurityKey::RSA_SHA1, ['type' => 'private']);
        $key->loadKey($pem['pkey']);
        $dSig->sign($key, $node);
        $dSig->add509Cert($pem['cert']);
    }

    // ═══════════════════════════════════════════════════════════════════
    // TRANSPORTE SOAP + mTLS
    // ═══════════════════════════════════════════════════════════════════

    private function envelope(string $op, string $dados): string
    {
        $c = self::CABEC_MSG;
        return "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
            . "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" "
            . "xmlns:nfse=\"http://nfse.abrasf.org.br\">"
            . "<soap:Header/><soap:Body><nfse:{$op}>"
            . "<nfseCabecMsg>{$c}</nfseCabecMsg>"
            . "<nfseDadosMsg>{$dados}</nfseDadosMsg>"
            . "</nfse:{$op}></soap:Body></soap:Envelope>";
    }

    private function post(string $envelope, string $action): string
    {
        $pem = $this->getPem();
        $keyFile = tempnam(sys_get_temp_dir(), 'k_'); file_put_contents($keyFile, $pem['pkey']);
        $certFile = tempnam(sys_get_temp_dir(), 'c_'); file_put_contents($certFile, $pem['cert']);

        $ch = curl_init($this->baseUrl);
        curl_setopt_array($ch, [
            CURLOPT_POST => true, CURLOPT_POSTFIELDS => $envelope,
            CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 30,
            CURLOPT_HTTPHEADER => ["Content-Type: text/xml; charset=utf-8", "SOAPAction: {$action}"],
            CURLOPT_SSLCERT => $certFile, CURLOPT_SSLKEY => $keyFile, CURLOPT_SSL_VERIFYPEER => true,
        ]);
        $resp = curl_exec($ch); curl_close($ch);
        @unlink($keyFile); @unlink($certFile);
        return $resp ?: '';
    }

    private function getPem(): array
    {
        $certs = [];
        openssl_pkcs12_read(file_get_contents($this->certificadoPath), $certs, $this->senhaCertificado);
        return ['pkey' => $certs['pkey'], 'cert' => $certs['cert']];
    }

    // ═══════════════════════════════════════════════════════════════════
    // PARSERS
    // ═══════════════════════════════════════════════════════════════════

    private function parseEmissao(string $xml): array
    {
        if (preg_match('/<Numero>(\d+)<\/Numero>/', $xml, $m)) {
            preg_match('/<CodigoVerificacao>([^<]+)</', $xml, $cv);
            return ['success' => true, 'numero_nf' => $m[1], 'codigo_verificacao' => $cv[1] ?? '', 'xml' => $xml];
        }
        if (preg_match('/<Mensagem>([^<]+)</', $xml, $e)) return ['success' => false, 'error' => $e[1]];
        return ['success' => false, 'error' => 'Resposta não reconhecida'];
    }

    private function parseCancelamento(string $xml): array
    {
        if (preg_match('/<Sucesso>true<\/Sucesso>/i', $xml)) return ['success' => true];
        if (preg_match('/<Mensagem>([^<]+)</', $xml, $e)) return ['success' => false, 'error' => $e[1]];
        return ['success' => false, 'error' => $this->isFault($xml) ? 'SOAP Fault' : 'Resposta não reconhecida'];
    }

    private function isFault(string $xml): bool
    {
        return str_contains($xml, 'faultcode') && str_contains($xml, 'faultstring');
    }

    private function construirXmlEmissao(array $d): string
    {
        // Implementação completa no arquivo separado (ver construirXmlEmissao acima)
        // Aqui simplificado para referência
        $ns = self::NS_NFSE;
        $cnpj = preg_replace('/\D/', '', $d['prestador_cnpj']);
        $im = $d['prestador_inscricao_municipal'];
        $nRps = $d['numero_rps'];
        $serie = $d['serie_rps'] ?? 'E';
        $valor = number_format((float)$d['valor_servicos'], 2, '.', '');
        $aliq = number_format((float)($d['aliquota_iss'] ?? 2), 2, '.', '');
        $iss = number_format((float)$d['valor_servicos'] * (float)($d['aliquota_iss'] ?? 2) / 100, 2, '.', '');
        $docTom = preg_replace('/\D/', '', $d['tomador_cpf_cnpj']);
        $tagDoc = strlen($docTom) === 11 ? 'Cpf' : 'Cnpj';
        $item = $d['item_lista_servico'] ?? '14.01';
        $cod = $d['codigo_tributacao'] ?? preg_replace('/\D/', '', $item);
        $data = date('Y-m-d');
        $cep = str_pad(preg_replace('/\D/', '', $d['tomador_cep'] ?? ''), 8, '0');

        return "<EnviarLoteRpsEnvio xmlns=\"{$ns}\"><LoteRps versao=\"2.04\">"
            . "<NumeroLote>{$nRps}</NumeroLote>"
            . "<Prestador><CpfCnpj><Cnpj>{$cnpj}</Cnpj></CpfCnpj><InscricaoMunicipal>{$im}</InscricaoMunicipal></Prestador>"
            . "<QuantidadeRps>1</QuantidadeRps><ListaRps><Rps>"
            . "<InfDeclaracaoPrestacaoServico Id=\"rps{$nRps}\">"
            . "<Rps><IdentificacaoRps><Numero>{$nRps}</Numero><Serie>{$serie}</Serie><Tipo>1</Tipo></IdentificacaoRps>"
            . "<DataEmissao>{$data}</DataEmissao><Status>1</Status></Rps>"
            . "<Competencia>{$data}</Competencia>"
            . "<Servico><Valores><ValorServicos>{$valor}</ValorServicos><ValorDeducoes>0.00</ValorDeducoes>"
            . "<ValorPis>0.00</ValorPis><ValorCofins>0.00</ValorCofins><ValorInss>0.00</ValorInss>"
            . "<ValorIr>0.00</ValorIr><ValorCsll>0.00</ValorCsll><OutrasRetencoes>0.00</OutrasRetencoes>"
            . "<ValTotTributos>0.00</ValTotTributos><ValorIss>{$iss}</ValorIss><Aliquota>{$aliq}</Aliquota>"
            . "<DescontoIncondicionado>0.00</DescontoIncondicionado><DescontoCondicionado>0.00</DescontoCondicionado>"
            . "</Valores><IssRetido>2</IssRetido><ItemListaServico>{$item}</ItemListaServico>"
            . "<CodigoTributacaoMunicipio>{$cod}</CodigoTributacaoMunicipio>"
            . "<Discriminacao>{$d['descricao_servico']}</Discriminacao>"
            . "<CodigoMunicipio>3543402</CodigoMunicipio><ExigibilidadeISS>1</ExigibilidadeISS>"
            . "<MunicipioIncidencia>3543402</MunicipioIncidencia></Servico>"
            . "<Prestador><CpfCnpj><Cnpj>{$cnpj}</Cnpj></CpfCnpj><InscricaoMunicipal>{$im}</InscricaoMunicipal></Prestador>"
            . "<TomadorServico><IdentificacaoTomador><CpfCnpj><{$tagDoc}>{$docTom}</{$tagDoc}></CpfCnpj></IdentificacaoTomador>"
            . "<RazaoSocial>{$d['tomador_nome']}</RazaoSocial>"
            . "<Endereco><Endereco>{$d['tomador_logradouro']}</Endereco><Numero>{$d['tomador_numero']}</Numero>"
            . "<Bairro>{$d['tomador_bairro']}</Bairro><CodigoMunicipio>3543402</CodigoMunicipio>"
            . "<Uf>{$d['tomador_uf']}</Uf><Cep>{$cep}</Cep></Endereco></TomadorServico>"
            . "<OptanteSimplesNacional>1</OptanteSimplesNacional><IncentivoFiscal>2</IncentivoFiscal>"
            . "</InfDeclaracaoPrestacaoServico></Rps></ListaRps></LoteRps></EnviarLoteRpsEnvio>";
    }
}
