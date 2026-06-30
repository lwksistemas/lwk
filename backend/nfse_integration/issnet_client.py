"""
Cliente para webservice ISSNet de Ribeirão Preto
Emissão de NFS-e direta na prefeitura — padrão ABRASF 2.04

Referências:
- WSDL: https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx?wsdl
- Operações: RecepcionarLoteRps (EnviarLoteRpsEnvio) + ConsultarLoteRps se vier só Protocolo;
  fallback RecepcionarLoteRpsSincrono (mesmo XML) se Fault genérico no assíncrono.
- WSDL: nfseCabecMsg e nfseDadosMsg sao ``xsd:string``. O ASMX costuma desserializar corretamente quando o
  XML ABRASF vai como *texto* (entidades ``&lt;...&gt;``), CDATA, ou filhos — tentamos nessa ordem em Fault generico.
- Envelope ``nfse:Operacao`` (namespace http://nfse.abrasf.org.br) + mTLS.
"""
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional
from decimal import Decimal

from nfse_integration.issnet_constants import (
    CABEC_MSG,
    ISSNET_RP_NFSE_ASMX,
    ISSNET_RP_NFSE_HOMOLOG,
    ISSNET_URLS,
    SOAP_ACTION_CONSULTAR_LOTE_RPS,
    SOAP_ACTION_RECEPCIONAR_LOTE_RPS,
    SOAP_ACTION_RECEPCIONAR_LOTE_RPS_SINCRONO,
)
from nfse_integration.issnet_response import (
    extrair_body_soap,
    extrair_erros,
    interpretar_cancelamento,
    parse_resposta_cancelamento,
    parse_resposta_xml,
    parse_resposta_xml_nfse_por_numero,
)
from nfse_integration.issnet_cert import carregar_certificado
from nfse_integration.issnet_soap_transport import criar_soap_client, post_soap_operacao
from nfse_integration.issnet_xml_builder import (
    IssnetEmissaoOpts,
    construir_xml_cancelar_nfse,
    construir_xml_consultar_lote_rps,
    construir_xml_consultar_nfse_por_rps,
    construir_xml_consultar_nfse_por_rps_legado,
    construir_xml_consultar_nfse_por_faixa,
    construir_xml_consultar_nfse_servico_prestado,
    construir_xml_consultar_url_nfse,
    construir_xml_enviar_lote_rps,
    extrair_protocolo_lote,
    issnet_erro_parece_negocio_abrasf,
    somente_digitos,
    xml_envio_para_raiz_sincrono_sem_assinar,
)
from nfse_integration.issnet_xml_signer import assinar_xml_issnet

logger = logging.getLogger(__name__)

_carregar_certificado = carregar_certificado


def testar_conexao_issnet(
    usuario: str,
    senha: str,
    certificado_path: str,
    senha_certificado: str,
    ambiente: str = 'producao',
) -> Dict[str, Any]:
    """Teste nao destrutivo: valida PFX/senha e tenta acessar o WSDL."""
    import requests as req

    out: Dict[str, Any] = {
        'success': False, 'message': '', 'detail': '',
        'ambiente': 'homologacao' if ambiente == 'homologacao' else 'producao',
    }
    if not (usuario or '').strip() or not (senha or '').strip():
        out['detail'] = 'Informe usuario e senha ISSNet.'
        return out
    path = (certificado_path or '').strip()
    if not path or not os.path.isfile(path):
        out['detail'] = 'Certificado .pfx nao encontrado no servidor.'
        return out
    if not (senha_certificado or ''):
        out['detail'] = 'Informe a senha do certificado (.pfx).'
        return out

    amb = 'homologacao' if ambiente == 'homologacao' else 'producao'
    base = ISSNET_URLS.get(amb)
    if not base:
        out['detail'] = f'Ambiente ISSNet desconhecido: {ambiente}'
        return out

    try:
        _key, cert, _ = _carregar_certificado(path, senha_certificado)
        try:
            out['certificado_subject'] = cert.subject.rfc4514_string()[:500]
        except Exception:
            pass
    except Exception as e:
        logger.warning('testar_conexao_issnet: falha PFX: %s', e)
        out['detail'] = 'Nao foi possivel abrir o certificado. Verifique .pfx e senha.'
        return out

    try:
        r = req.get(f'{base}?wsdl', timeout=25, headers={'User-Agent': 'LWK-Sistemas/CRM'})
        body = (r.text or '')[:2000].lower()
        if r.status_code == 200 and ('definitions' in body or 'wsdl' in body):
            out['success'] = True
            out['message'] = (
                'Certificado OK e WSDL ISSNet Online (ABRASF 2.04) acessivel. '
                'Credenciais serao validadas na primeira emissao.'
            )
            if amb == 'homologacao':
                out['message'] += (
                    ' Em Ribeirao Preto este WSDL e o mesmo da producao; homologacao de negocio depende '
                    'da prefeitura (liberacao / credenciais de teste), nao de outro hostname.'
                )
        else:
            out['detail'] = f'WSDL retornou HTTP {r.status_code}.'
    except Exception as e:
        logger.warning('testar_conexao_issnet: request WSDL: %s', e)
        out['detail'] = f'Nao foi possivel contatar o ISSNet: {e}'
    return out


class ISSNetClient:
    """
    Cliente SOAP para webservice ISSNet Ribeirao Preto (ABRASF 2.04).

    Emissão: RecepcionarLoteRps + EnviarLoteRpsEnvio (ABRASF 2.04), SOAP + mTLS como sped-nfse-issnet (Focus599Dev).
    Credenciais ISSNet (usuario/senha) são exigidas na configuração; o envelope segue NFePHP envelopSOAP.
    """

    def __init__(
        self,
        usuario: str,
        senha: str,
        certificado_path: str,
        senha_certificado: str,
        ambiente: str = 'producao',
    ):
        self.usuario = usuario
        self.senha = senha
        self.certificado_path = certificado_path
        self.senha_certificado = senha_certificado
        self.ambiente = 'homologacao' if ambiente == 'homologacao' else 'producao'
        self.base_url = ISSNET_URLS[self.ambiente]
        self.wsdl_url = f'{self.base_url}?wsdl'
        self._soap_client = None
        if self.ambiente == 'homologacao':
            logger.warning(
                'ISSNet RP ABRASF 2.04: ambiente homologacao — mesmo WSDL de producao (%s). '
                'Liberacao municipal (ex. E138) e cadastro continuam valendo; confirme com a prefeitura '
                'se existe ambiente de testes separado.',
                self.base_url,
            )

        # Campos configuraveis (setados pelo service.py)
        self._regime_especial = '0'
        self._optante_simples = True
        self._incentivador_cultural = False

    def _get_soap_client(self):
        """Cliente SOAP zeep com lazy loading."""
        if self._soap_client is not None:
            return self._soap_client
        self._soap_client = criar_soap_client(self.wsdl_url, self.base_url)
        logger.info('Cliente SOAP ISSNet inicializado: %s', self.ambiente)
        return self._soap_client

    def _assinar_xml(self, xml_str: str) -> str:
        return assinar_xml_issnet(xml_str, self.certificado_path, self.senha_certificado)

    def _emissao_opts(self) -> IssnetEmissaoOpts:
        return IssnetEmissaoOpts(
            numero_lote_config=int(getattr(self, '_numero_lote_config', 0) or 0),
            regime_especial=getattr(self, '_regime_especial', '0') or '0',
            optante_simples=bool(self._optante_simples),
            incentivador_cultural=bool(self._incentivador_cultural),
        )

    def _construir_xml_gerar_nfse(
        self,
        prestador_cnpj: str,
        prestador_inscricao_municipal: str,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_endereco: Dict[str, str],
        servico_codigo: str,
        servico_descricao: str,
        valor_servicos: Decimal,
        aliquota_iss: Decimal,
        numero_rps: int,
        serie_rps: str,
        tipo_rps: int,
        data_emissao: datetime,
        codigo_cnae: Optional[str] = None,
        item_lista_servico: Optional[str] = None,
        codigo_tributacao_municipio: Optional[str] = None,
    ) -> str:
        return construir_xml_enviar_lote_rps(
            prestador_cnpj=prestador_cnpj,
            prestador_inscricao_municipal=prestador_inscricao_municipal,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            servico_codigo=servico_codigo,
            servico_descricao=servico_descricao,
            valor_servicos=valor_servicos,
            aliquota_iss=aliquota_iss,
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            tipo_rps=tipo_rps,
            data_emissao=data_emissao,
            codigo_cnae=codigo_cnae,
            item_lista_servico=item_lista_servico,
            codigo_tributacao_municipio=codigo_tributacao_municipio,
            opts=self._emissao_opts(),
        )

    # ------------------------------------------------------------------
    # Emitir NFS-e
    # ------------------------------------------------------------------
    def emitir_nfse(
        self,
        prestador_cnpj: str,
        prestador_inscricao_municipal: str,
        prestador_razao_social: str,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_endereco: Dict[str, str],
        servico_codigo: str,
        servico_descricao: str,
        valor_servicos: Decimal,
        aliquota_iss: Decimal,
        numero_rps: int,
        serie_rps: str = 'E',
        tipo_rps: int = 1,
        data_emissao: Optional[datetime] = None,
        codigo_cnae: Optional[str] = None,
        item_lista_servico: Optional[str] = None,
        codigo_tributacao_municipio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e (1 RPS): tenta ``RecepcionarLoteRpsSincrono`` com raiz ABRASF correta; se falha de
        transporte/SOAP, usa ``RecepcionarLoteRps`` e consulta o lote quando vier apenas protocolo.
        """
        try:
            if data_emissao is None:
                data_emissao = datetime.now()

            xml_rps = self._construir_xml_gerar_nfse(
                prestador_cnpj=prestador_cnpj,
                prestador_inscricao_municipal=prestador_inscricao_municipal,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                servico_codigo=servico_codigo,
                servico_descricao=servico_descricao,
                valor_servicos=valor_servicos,
                aliquota_iss=aliquota_iss,
                numero_rps=numero_rps,
                serie_rps=serie_rps,
                tipo_rps=tipo_rps,
                data_emissao=data_emissao,
                codigo_cnae=codigo_cnae,
                item_lista_servico=item_lista_servico,
                codigo_tributacao_municipio=codigo_tributacao_municipio,
            )

            xml_sinc_u = xml_envio_para_raiz_sincrono_sem_assinar(xml_rps)
            xml_sinc_assinado = self._assinar_xml(xml_sinc_u)
            logger.info('ISSNet: tentando RecepcionarLoteRpsSincrono (EnviarLoteRpsSincronoEnvio assinado)')
            parsed_s, _body_s = self._post_soap_operacao(
                nome_operacao='RecepcionarLoteRpsSincrono',
                soap_action_uri=SOAP_ACTION_RECEPCIONAR_LOTE_RPS_SINCRONO,
                dados_xml=xml_sinc_assinado,
            )
            if parsed_s.get('success'):
                resultado = parsed_s
            elif issnet_erro_parece_negocio_abrasf(parsed_s.get('error') or ''):
                resultado = parsed_s
            else:
                xml_assinado = self._assinar_xml(xml_rps)
                resultado = self._enviar_soap_direto(
                    xml_assinado,
                    prestador_cnpj=prestador_cnpj,
                    prestador_inscricao_municipal=prestador_inscricao_municipal,
                )
            resultado['numero_rps'] = numero_rps
            if resultado.get('success'):
                resultado['valor'] = valor_servicos
                resultado.setdefault('tomador_nome', tomador_nome)
                resultado.setdefault('tomador_cpf_cnpj', tomador_cpf_cnpj)
                resultado.setdefault(
                    'servico_descricao',
                    (servico_descricao or '')[:500],
                )
            return resultado

        except Exception as e:
            logger.exception('Erro ao emitir NFS-e: %s', e)
            return {'success': False, 'error': str(e), 'numero_rps': numero_rps}

    # ------------------------------------------------------------------
    # Protocolo / consulta de lote (fluxo assincrono ABRASF)
    # ------------------------------------------------------------------
    def _consultar_lote_rps_ate_nfse(
        self,
        protocolo: str,
        prestador_cnpj: str,
        prestador_inscricao_municipal: str,
        tentativas: int = 20,
        intervalo_s: float = 3.0,
    ) -> Dict[str, Any]:
        """ConsultarLoteRps ate obter CompNfse ou esgotar tentativas."""
        xml_consulta = construir_xml_consultar_lote_rps(
            protocolo, prestador_cnpj, prestador_inscricao_municipal
        )
        for tent in range(tentativas):
            if tent > 0:
                time.sleep(intervalo_s)
            out, _xml_b = self._post_soap_operacao(
                nome_operacao='ConsultarLoteRps',
                soap_action_uri=SOAP_ACTION_CONSULTAR_LOTE_RPS,
                dados_xml=xml_consulta,
            )
            if out.get('success'):
                return out
            err = out.get('error') or ''
            # E178 = lote aguardando processamento — continuar tentando
            pode_retry = (
                'NFS-e nao encontrada na resposta' in err
                or 'E178' in err
                or 'aguardando processamento' in err.lower()
            )
            if pode_retry and tent < tentativas - 1:
                logger.info(
                    'ISSNet consulta lote protocolo %s tentativa %s/%s — %s',
                    protocolo,
                    tent + 1,
                    tentativas,
                    'aguardando processamento' if 'E178' in err else 'sem NF ainda',
                )
                continue
            return out
        return {'success': False, 'error': 'Tempo esgotado aguardando NFS-e apos envio do lote (60s).'}

    def _post_soap_operacao(
        self,
        nome_operacao: str,
        soap_action_uri: str,
        dados_xml: str,
    ):
        return post_soap_operacao(
            base_url=self.base_url,
            wsdl_url=self.wsdl_url,
            certificado_path=self.certificado_path,
            senha_certificado=self.senha_certificado,
            nome_operacao=nome_operacao,
            soap_action_uri=soap_action_uri,
            dados_xml=dados_xml,
        )

    # ------------------------------------------------------------------
    # Enviar via requests direto (formato exato da lib PHP)
    # ------------------------------------------------------------------
    def _enviar_soap_direto(
        self,
        xml_dados: str,
        prestador_cnpj: str = '',
        prestador_inscricao_municipal: str = '',
    ) -> Dict[str, Any]:
        """RecepcionarLoteRps; se vier apenas Protocolo, consulta o lote ate obter a NFSe."""
        parsed, xml_body = self._post_soap_operacao(
            nome_operacao='RecepcionarLoteRps',
            soap_action_uri=SOAP_ACTION_RECEPCIONAR_LOTE_RPS,
            dados_xml=xml_dados,
        )
        if parsed.get('success'):
            return parsed
        err0 = (parsed.get('error') or '')
        if 'Erro genérico do webservice ISSNet' in err0 or 'sem detail' in err0.lower():
            logger.info(
                'ISSNet: falha generica no RecepcionarLoteRps; fluxo sincrono e feito em emitir_nfse '
                '(raiz EnviarLoteRpsSincronoEnvio). Segue apenas consulta por protocolo se houver.'
            )
        proto = extrair_protocolo_lote(xml_body)
        if proto and prestador_cnpj and prestador_inscricao_municipal:
            logger.info('ISSNet envio retornou protocolo %s; consultando lote...', proto)
            return self._consultar_lote_rps_ate_nfse(
                proto,
                prestador_cnpj,
                prestador_inscricao_municipal,
            )
        return parsed

    # ------------------------------------------------------------------
    # Enviar via zeep (mantido como fallback)
    # ------------------------------------------------------------------
    def _enviar_gerar_nfse(self, xml_assinado: str) -> Dict[str, Any]:
        """
        Chama operacao RecepcionarLoteRps do webservice ISSNet (fallback zeep).
        """
        try:
            client = self._get_soap_client()
            logger.info('XML enviado ao ISSNet (nfseDadosMsg): %s', xml_assinado[:2000])
            with client.settings(raw_response=True):
                response = client.service.RecepcionarLoteRps(
                    nfseCabecMsg=CABEC_MSG,
                    nfseDadosMsg=xml_assinado,
                )
            # response eh um requests.Response
            resp_text = response.text if hasattr(response, 'text') else str(response)
            logger.info('Resposta ISSNet HTTP %s, preview: %s',
                        getattr(response, 'status_code', '?'), resp_text[:500])

            # Extrair conteudo do SOAP Body
            xml_body = self._extrair_body_soap(resp_text)
            return self._parse_resposta_xml(xml_body)
        except Exception as e:
            logger.exception('Erro ao enviar GerarNfse: %s', e)
            return {'success': False, 'error': str(e)}

    def _extrair_body_soap(self, soap_xml: str) -> str:
        return extrair_body_soap(soap_xml)

    def _parse_resposta_xml(self, xml_str: str) -> Dict[str, Any]:
        return parse_resposta_xml(xml_str)

    def _extrair_erros(self, texto: str) -> str:
        return extrair_erros(texto)

    def _parse_resposta_cancelamento(self, xml_str: str) -> Dict[str, Any]:
        return parse_resposta_cancelamento(xml_str)

    def _interpretar_cancelamento(self, parsed: Dict[str, Any], xml_body: str) -> Dict[str, Any]:
        return interpretar_cancelamento(parsed, xml_body)

    # ------------------------------------------------------------------
    # Consultar NFS-e por RPS
    # ------------------------------------------------------------------
    def consultar_url_nfse(self, numero_nf: str, prestador_cnpj: str = '', inscricao_municipal: str = '') -> Dict[str, Any]:
        """
        Chama ConsultarUrlNfse para obter a URL do PDF/portal oficial da NFS-e no ISSNet.
        Retorna {'success': True, 'url': '...'} ou {'success': False, 'error': '...'}.
        """
        try:
            cnpj = somente_digitos(prestador_cnpj or self.usuario or '')
            xml_consulta = construir_xml_consultar_url_nfse(
                numero_nf, cnpj, inscricao_municipal or ''
            )
            # Assinar o XML completo (Signature fica fora do Pedido, dentro do ConsultarUrlNfseEnvio)
            try:
                xml_consulta = self._assinar_xml(xml_consulta)
            except Exception as e:
                logger.warning('Erro ao assinar ConsultarUrlNfse (tentando sem assinatura): %s', e)
            parsed, xml_body = self._post_soap_operacao(
                nome_operacao='ConsultarUrlNfse',
                soap_action_uri='http://nfse.abrasf.org.br/ConsultarUrlNfse',
                dados_xml=xml_consulta,
            )
            # Logar resposta bruta completa para diagnóstico
            logger.info('ConsultarUrlNfse resposta bruta completa: %s', xml_body)
            logger.info('ConsultarUrlNfse parsed: %s', parsed)

            resp_str = xml_body or ''

            from nfse_integration.issnet_response import parse_consultar_url_nfse_resposta

            url_parsed = parse_consultar_url_nfse_resposta(resp_str)
            if url_parsed.get('success') and url_parsed.get('numero_nf'):
                url = str(url_parsed.get('url') or '').strip()
                if not url:
                    for tag in ('UrlVisualizacaoNfse', 'UrlNfse', 'Url', 'url'):
                        url_match = re.search(
                            rf'<{tag}[^>]*>(.*?)</{tag}>', resp_str, re.IGNORECASE | re.DOTALL
                        )
                        if url_match:
                            cand = url_match.group(1).strip()
                            if cand.startswith('http'):
                                url = cand
                                break
                if url:
                    url_parsed['url'] = url
                logger.info('ConsultarUrlNfse links extraídos: %s', url_parsed)
                return url_parsed

            nf_parsed = self._parse_resposta_xml(resp_str)
            if nf_parsed.get('success') and nf_parsed.get('numero_nf'):
                url = ''
                for tag in ('Url', 'url', 'Link', 'link', 'UrlNfse', 'urlNfse'):
                    url_match = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', resp_str, re.IGNORECASE | re.DOTALL)
                    if url_match:
                        cand = url_match.group(1).strip()
                        if cand.startswith('http') and not any(
                            x in cand for x in ['abrasf.org.br', 'xmlsoap.org', 'w3.org', 'schemas.']
                        ):
                            url = cand
                            break
                return {**nf_parsed, 'success': True, 'url': url}

            # Tentar extrair URL da resposta XML — vários formatos possíveis
            for tag in ('Url', 'url', 'Link', 'link', 'UrlNfse', 'urlNfse'):
                url_match = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', resp_str, re.IGNORECASE | re.DOTALL)
                if url_match:
                    url = url_match.group(1).strip()
                    # Ignorar namespaces e URLs de schema
                    if url and url.startswith('http') and not any(x in url for x in ['abrasf.org.br', 'xmlsoap.org', 'w3.org', 'schemas.']):
                        logger.info('ConsultarUrlNfse URL encontrada: %s', url)
                        return {'success': True, 'url': url}

            # Procurar qualquer URL http que não seja o namespace
            for http_match in re.finditer(r'(https?://[^\s<>"&]+)', resp_str):
                url = http_match.group(1)
                if 'abrasf.org.br' not in url and 'xmlsoap.org' not in url and 'w3.org' not in url and 'schemas.' not in url:
                    logger.info('ConsultarUrlNfse URL via fallback: %s', url)
                    return {'success': True, 'url': url}

            if parsed.get('success') is False:
                return {'success': False, 'error': parsed.get('error', ''), 'raw': resp_str[:500]}
            return {'success': False, 'error': f'URL não encontrada na resposta', 'raw': resp_str[:500]}
        except Exception as e:
            logger.warning('Erro ao consultar URL NFS-e ISSNet: %s', e)
            return {'success': False, 'error': str(e)}

    def inferir_cancelada_por_url(self, *, url: str) -> Dict[str, Any]:
        """
        Busca a página do portal/visualização oficial retornada pelo ISSNet e tenta inferir se a nota
        está cancelada (ex.: "CANCELADA", "SEM VALOR LEGAL").

        Isso é um fallback de sincronização quando a consulta por RPS falha (E160/E183).
        """
        try:
            import requests

            u = (url or '').strip()
            if not u.startswith('http'):
                return {'success': False, 'error': 'URL inválida para verificação.'}

            r = requests.get(u, timeout=(6, 18), headers={'User-Agent': 'LWK-Sistemas/CRM'})
            txt = (r.text or '')[:200000]  # limitar
            up = txt.upper()
            cancelada = ('SEM VALOR LEGAL' in up) or ('CANCELAD' in up)
            return {'success': True, 'cancelada': bool(cancelada)}
        except Exception as e:
            logger.warning('Erro ao verificar cancelamento via URL ISSNet: %s', e)
            return {'success': False, 'error': str(e)}

    def _variantes_xml_consulta(self, xml_consulta: str, *, assinar: bool = True) -> list[str]:
        variantes: list[str] = []
        if assinar:
            try:
                variantes.append(self._assinar_xml(xml_consulta))
            except Exception as exc:
                logger.warning('Falha ao assinar consulta ISSNet: %s', exc)
        if xml_consulta not in variantes:
            variantes.append(xml_consulta)
        return variantes

    def _executar_consulta_nfse(
        self,
        *,
        nome_operacao: str,
        soap_action_uri: str,
        dados_xml: str,
        numero_nf_esperado: str | None = None,
    ) -> Dict[str, Any]:
        parsed, xml_body = self._post_soap_operacao(
            nome_operacao=nome_operacao,
            soap_action_uri=soap_action_uri,
            dados_xml=dados_xml,
        )
        resp_str = (xml_body or '').strip()
        if not resp_str:
            return {'success': False, 'error': f'Resposta vazia ao {nome_operacao}.'}
        if re.search(r'<\s*ListaMensagemRetorno\b', resp_str, re.I):
            return {
                'success': False,
                'error': self._extrair_erros(resp_str),
                'raw_xml': resp_str[:8000],
            }
        if numero_nf_esperado:
            nf = parse_resposta_xml_nfse_por_numero(resp_str, numero_nf_esperado)
        else:
            nf = self._parse_resposta_xml(resp_str)
        if nf.get('success'):
            return {**nf, 'cancelada': False, 'raw_xml': resp_str[:8000]}
        if parsed and parsed.get('success') is False:
            return {**parsed, 'raw_xml': resp_str[:8000]}
        return {
            'success': False,
            'error': nf.get('error') or 'NFS-e não encontrada na resposta do ISSNet.',
            'raw_xml': resp_str[:8000],
        }

    def consultar_nfse_servico_prestado(
        self,
        numero_nf: str,
        prestador_cnpj: str = '',
        inscricao_municipal: str = '',
    ) -> Dict[str, Any]:
        """Consulta NFS-e emitida pelo prestador (por número da nota)."""
        try:
            cnpj = somente_digitos(prestador_cnpj or self.usuario or '')
            xml_consulta = construir_xml_consultar_nfse_servico_prestado(
                str(numero_nf), cnpj, inscricao_municipal or ''
            )
            last_err = 'NFS-e não encontrada no ISSNet.'
            for dados in self._variantes_xml_consulta(xml_consulta, assinar=True):
                out = self._executar_consulta_nfse(
                    nome_operacao='ConsultarNfseServicoPrestado',
                    soap_action_uri='http://nfse.abrasf.org.br/ConsultarNfseServicoPrestado',
                    dados_xml=dados,
                    numero_nf_esperado=str(numero_nf),
                )
                if out.get('success') and out.get('numero_nf'):
                    return out
                last_err = str(out.get('error') or last_err)
            return {'success': False, 'error': last_err}
        except Exception as e:
            logger.exception('Erro ao consultar NFS-e por número: %s', e)
            return {'success': False, 'error': str(e)}

    def consultar_nfse_por_faixa(
        self,
        numero_nf: str,
        prestador_cnpj: str = '',
        inscricao_municipal: str = '',
    ) -> Dict[str, Any]:
        """Consulta NFS-e por faixa (inicial=final=numero)."""
        try:
            cnpj = somente_digitos(prestador_cnpj or self.usuario or '')
            xml_consulta = construir_xml_consultar_nfse_por_faixa(
                str(numero_nf), cnpj, inscricao_municipal or ''
            )
            last_err = 'NFS-e não encontrada no ISSNet.'
            for dados in self._variantes_xml_consulta(xml_consulta, assinar=True):
                out = self._executar_consulta_nfse(
                    nome_operacao='ConsultarNfsePorFaixa',
                    soap_action_uri='http://nfse.abrasf.org.br/ConsultarNfsePorFaixa',
                    dados_xml=dados,
                    numero_nf_esperado=str(numero_nf),
                )
                if out.get('success') and out.get('numero_nf'):
                    return out
                last_err = str(out.get('error') or last_err)
            return {'success': False, 'error': last_err}
        except Exception as e:
            logger.exception('Erro ao consultar NFS-e por faixa: %s', e)
            return {'success': False, 'error': str(e)}

    def consultar_nfse(self, numero_nf: str) -> Dict[str, Any]:
        """Consulta NFS-e emitida por RPS (compat: método legado)."""
        try:
            xml_consulta = construir_xml_consultar_nfse_por_rps_legado(
                numero_nf, self.usuario
            )
            client = self._get_soap_client()
            response = client.service.ConsultarNfsePorRps(
                nfseCabecMsg=CABEC_MSG,
                nfseDadosMsg=xml_consulta,
            )
            return {'success': True, 'data': str(response)}
        except Exception as e:
            logger.exception('Erro ao consultar NFS-e: %s', e)
            return {'success': False, 'error': str(e)}

    def consultar_nfse_por_rps(
        self,
        *,
        numero_rps: int,
        serie_rps: str,
        tipo_rps: str = '1',
        prestador_cnpj: str,
        inscricao_municipal: str,
    ) -> Dict[str, Any]:
        """
        Consulta NFS-e por RPS (ABRASF 2.04 / ISSNet).
        Usado para sincronizar status (ex.: cancelada no portal).
        """
        try:
            xml_consulta = construir_xml_consultar_nfse_por_rps(
                numero_rps=numero_rps,
                serie_rps=serie_rps,
                tipo_rps=tipo_rps,
                prestador_cnpj=prestador_cnpj or self.usuario or '',
                inscricao_municipal=inscricao_municipal or '',
            )
            last_err = 'NFS-e não encontrada na resposta do ISSNet.'
            for dados in self._variantes_xml_consulta(xml_consulta, assinar=False):
                try:
                    dados_ass = self._assinar_xml(dados)
                except Exception:
                    dados_ass = None
                for xml_try in [d for d in (dados, dados_ass) if d]:
                    parsed, xml_body = self._post_soap_operacao(
                        nome_operacao='ConsultarNfsePorRps',
                        soap_action_uri='http://nfse.abrasf.org.br/ConsultarNfsePorRps',
                        dados_xml=xml_try,
                    )
                    resp_str = (xml_body or '').strip()
                    if not resp_str:
                        continue
                    if re.search(r'<\s*ListaMensagemRetorno\b', resp_str, re.I):
                        last_err = self._extrair_erros(resp_str)
                        continue
                    cancelada = bool(
                        re.search(
                            r'<\s*(Cancelamento|NfseCancelada|ConfirmacaoCancelamento)\b',
                            resp_str,
                            re.I,
                        )
                        or re.search(r'DataHoraCancelamento', resp_str, re.I)
                    )
                    if cancelada:
                        return {'success': True, 'cancelada': True, 'raw_xml': resp_str[:8000]}
                    nf = self._parse_resposta_xml(resp_str)
                    if nf.get('success'):
                        return {**nf, 'cancelada': False, 'raw_xml': resp_str[:8000]}
                    if parsed and parsed.get('success') is False:
                        last_err = str(parsed.get('error') or last_err)
            return {'success': False, 'error': last_err}
        except Exception as e:
            logger.exception('Erro ao consultar NFS-e por RPS: %s', e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------
    # Cancelar NFS-e
    # ------------------------------------------------------------------
    def cancelar_nfse(self, numero_nf: str, motivo: str, prestador_cnpj: str = '', inscricao_municipal: str = '', codigo_cancelamento: str = '1') -> Dict[str, Any]:
        """Cancela NFS-e emitida via ISSNet."""
        try:
            def _tentar_cancelamento(xml_payload: str, *, label: str):
                xml_assinado = self._assinar_xml(xml_payload)
                parsed_raw, xml_body = self._post_soap_operacao(
                    nome_operacao='CancelarNfse',
                    soap_action_uri='http://nfse.abrasf.org.br/CancelarNfse',
                    dados_xml=xml_assinado,
                )
                parsed = self._interpretar_cancelamento(parsed_raw or {}, xml_body or '')
                if parsed.get('success') is False:
                    logger.warning('ISSNet cancelar_nfse falhou (%s): %s', label, parsed.get('error'))
                elif parsed.get('success'):
                    logger.info('ISSNet cancelar_nfse OK (%s)', label)
                return parsed, xml_body

            xml_cancelar_1 = construir_xml_cancelar_nfse(
                numero_nf,
                prestador_cnpj or self.usuario or '',
                inscricao_municipal or '',
                codigo_cancelamento,
            )
            parsed, xml_body = _tentar_cancelamento(xml_cancelar_1, label='pedido')

            if parsed and parsed.get('success') is False:
                nf_digits = somente_digitos(str(numero_nf))
                inf_id = f'cancel{nf_digits}' if nf_digits else 'cancels01'
                xml_cancelar_2 = construir_xml_cancelar_nfse(
                    numero_nf,
                    prestador_cnpj or self.usuario or '',
                    inscricao_municipal or '',
                    codigo_cancelamento,
                    inf_pedido_id=inf_id,
                )
                parsed, xml_body = _tentar_cancelamento(xml_cancelar_2, label='inf_pedido')

            if parsed.get('success'):
                return parsed

            return self._interpretar_cancelamento(parsed, xml_body or '')
        except Exception as e:
            logger.exception('Erro ao cancelar NFS-e: %s', e)
            return {'success': False, 'error': str(e)}
