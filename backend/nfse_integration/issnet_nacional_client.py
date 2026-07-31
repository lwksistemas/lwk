"""Cliente ISSNet padrão Nacional (RTC) — Ribeirão Preto.

Substitui o ABRASF 2.04 a partir de 03/08/2026.
Endpoint: https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx
Métodos: RecepcionarLoteDpsSincrono, CancelarNfse, ConsultarNfseDps, ConsultarUrlNfse.
"""
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from nfse_integration.issnet_cert import carregar_certificado
from nfse_integration.issnet_constants import (
    ISSNET_NACIONAL_URLS,
    SOAP_ACTION_NACIONAL_CANCELAR_NFSE,
    SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS,
    SOAP_ACTION_NACIONAL_CONSULTAR_URL_NFSE,
    SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO,
)
from nfse_integration.issnet_nacional_xml_builder import (
    construir_xml_cancelar_nfse_nacional,
    construir_xml_consultar_nfse_por_dps,
    construir_xml_enviar_lote_dps_sincrono,
    extrair_chave_acesso_nfse_nacional,
    extrair_numero_nfse_nacional,
)
from nfse_integration.issnet_response import extrair_body_soap, extrair_erros
from nfse_integration.issnet_xml_builder import somente_digitos

logger = logging.getLogger(__name__)


class ISSNetNacionalClient:
    """Cliente para emissão NFS-e via ISSNet padrão Nacional (DPS).

    Uso:
        client = ISSNetNacionalClient(
            cert_path='/path/to/cert.pfx',
            cert_password='senha',
            ambiente='producao',
            prestador_cnpj='41449198000172',
            prestador_inscricao_municipal='20130440',
        )
        resultado = client.emitir_nfse(...)
    """

    def __init__(
        self,
        *,
        cert_path: str | None = None,
        cert_bytes: bytes | None = None,
        cert_password: str = "",
        ambiente: str = "producao",
        prestador_cnpj: str = "",
        prestador_inscricao_municipal: str = "",
        codigo_municipio: str = "3543402",
        optante_simples_nacional: bool = True,
    ):
        self.cert_path = cert_path
        self.cert_bytes = cert_bytes
        self.cert_password = cert_password
        self.ambiente = "homologacao" if ambiente == "homologacao" else "producao"
        self.prestador_cnpj = somente_digitos(prestador_cnpj)
        self.prestador_im = (prestador_inscricao_municipal or "").strip()
        self.codigo_municipio = codigo_municipio
        self.optante_simples = optante_simples_nacional
        self.url = ISSNET_NACIONAL_URLS.get(self.ambiente, ISSNET_NACIONAL_URLS["producao"])

    def _assinar_xml(self, xml_str: str) -> str:
        """Assina XML com certificado digital (salva cert em arquivo temp)."""
        import os
        import tempfile
        from contextlib import suppress

        from nfse_integration.issnet_xml_signer import assinar_xml_issnet

        cert_data = self.cert_bytes
        if not cert_data and self.cert_path:
            from nfse_integration.issnet_cert import carregar_certificado
            # cert_path é path direto
            return assinar_xml_issnet(xml_str, self.cert_path, self.cert_password)

        if not cert_data:
            raise ValueError("Certificado digital não disponível para assinatura.")

        # Salvar bytes em arquivo temporário
        cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pfx", prefix="issnet_nac_")
        try:
            cert_tmp.write(bytes(cert_data))
            cert_tmp.close()
            return assinar_xml_issnet(xml_str, cert_tmp.name, self.cert_password)
        finally:
            if os.path.isfile(cert_tmp.name):
                with suppress(OSError):
                    os.unlink(cert_tmp.name)

    def _enviar_soap(self, xml_dados: str, soap_action: str) -> str:
        """Envia requisição SOAP ao webservice Nacional com envelope específico."""
        import os
        import tempfile
        from contextlib import suppress
        from xml.sax.saxutils import escape as xml_escape

        import requests as req

        from nfse_integration.issnet_cert import certificado_mtls_temporario
        from nfse_integration.issnet_soap import strip_xml_declaration

        cert_data = self.cert_bytes
        if not cert_data:
            raise ValueError("Certificado digital não disponível.")

        # Salvar cert em temp para mTLS
        cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pfx", prefix="issnet_soap_")
        cert_tmp.write(bytes(cert_data))
        cert_tmp.close()
        cert_path = cert_tmp.name

        try:
            with certificado_mtls_temporario(cert_path, self.cert_password) as (pem_cert, pem_key):
                # Montar envelope SOAP para padrão Nacional
                dados = strip_xml_declaration(xml_dados or "")
                cabec_nac = (
                    '<cabecalho versao="1.01" xmlns="http://www.sped.fazenda.gov.br/nfse">'
                    '<versaoDados>1.01</versaoDados>'
                    '</cabecalho>'
                )
                nome_op = soap_action.rsplit("/", 1)[-1] if "/" in soap_action else soap_action

                envelope = (
                    '<?xml version="1.0" encoding="utf-8"?>'
                    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
                    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                    'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                    'xmlns:nfse="http://nfse.abrasf.org.br">'
                    '<soap:Header/>'
                    '<soap:Body>'
                    f'<nfse:{nome_op}>'
                    f'<nfseCabecMsg><![CDATA[{cabec_nac}]]></nfseCabecMsg>'
                    f'<nfseDadosMsg><![CDATA[{dados}]]></nfseDadosMsg>'
                    f'</nfse:{nome_op}>'
                    '</soap:Body>'
                    '</soap:Envelope>'
                )

                headers = {
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": soap_action,
                    "User-Agent": "LWK-Sistemas/NacionalNFSe",
                }

                logger.info("ISSNet Nacional SOAP %s (%d bytes) enviando...", nome_op, len(envelope.encode()))
                r = req.post(
                    self.url,
                    data=envelope.encode("utf-8"),
                    headers=headers,
                    cert=(pem_cert, pem_key),
                    timeout=(8, 25),
                    verify=True,
                )
                logger.info("ISSNet Nacional resposta HTTP %d (%d bytes)", r.status_code, len(r.text))
                if r.status_code >= 400:
                    logger.error("ISSNet Nacional resposta erro: %s", r.text[:2000])
                return r.text

        finally:
            if os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

    def emitir_nfse(
        self,
        *,
        numero_lote: int,
        numero_dps: int,
        serie_dps: str = "1",
        tomador_cpf_cnpj: str = "",
        tomador_nome: str = "",
        tomador_endereco: dict[str, str] | None = None,
        tomador_telefone: str = "",
        tomador_email: str = "",
        codigo_tributacao_nacional: str = "140100",
        codigo_tributacao_municipal: str | None = None,
        descricao_servico: str = "Serviço prestado",
        codigo_nbs: str = "",
        valor_servicos: Decimal = Decimal("0.00"),
        aliquota_iss: Decimal = Decimal("2.50"),
        data_emissao: datetime | None = None,
        data_competencia: datetime | None = None,
        codigo_municipio_prestacao: str = "",
        prestador_telefone: str = "",
        prestador_email: str = "",
    ) -> dict[str, Any]:
        """Emite NFS-e via ISSNet Nacional (padrão DPS).

        Returns:
            Dict com: success, numero_nfse, chave_acesso, xml_dps, erro, xml_resposta
        """
        result: dict[str, Any] = {
            "success": False,
            "numero_nfse": None,
            "chave_acesso": None,
            "codigo_verificacao": None,
            "xml_dps": None,
            "xml_resposta": None,
            "erro": None,
        }

        try:
            ambiente_int = 1 if self.ambiente == "producao" else 2

            # 1. Construir XML
            xml_envio = construir_xml_enviar_lote_dps_sincrono(
                numero_lote=numero_lote,
                prestador_cnpj=self.prestador_cnpj,
                prestador_inscricao_municipal=self.prestador_im,
                numero_dps=numero_dps,
                serie_dps=serie_dps,
                data_emissao=data_emissao,
                data_competencia=data_competencia,
                codigo_municipio_emissor=self.codigo_municipio,
                ambiente=ambiente_int,
                prestador_telefone=prestador_telefone,
                prestador_email=prestador_email,
                optante_simples_nacional=self.optante_simples,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                tomador_telefone=tomador_telefone,
                tomador_email=tomador_email,
                codigo_municipio_prestacao=codigo_municipio_prestacao or self.codigo_municipio,
                codigo_tributacao_nacional=codigo_tributacao_nacional,
                codigo_tributacao_municipal=codigo_tributacao_municipal,
                descricao_servico=descricao_servico,
                codigo_nbs=codigo_nbs,
                valor_servicos=valor_servicos,
                aliquota_iss=aliquota_iss,
            )

            # 2. Assinar XML
            logger.info("ISSNet Nacional: assinando XML DPS nº %d...", numero_dps)
            xml_assinado = self._assinar_xml(xml_envio)
            result["xml_dps"] = xml_assinado

            # 3. Enviar via SOAP
            logger.info("ISSNet Nacional: enviando DPS nº %d ao webservice (%s)...", numero_dps, self.ambiente)
            resposta_soap = self._enviar_soap(
                xml_assinado,
                SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO,
            )
            result["xml_resposta"] = resposta_soap

            # 4. Processar resposta
            body = extrair_body_soap(resposta_soap)
            erros = extrair_erros(body)

            if erros:
                result["erro"] = erros
                logger.warning("ISSNet Nacional: erro na emissão DPS %d: %s", numero_dps, erros)
                return result

            # Extrair dados da NFS-e gerada
            numero_nfse = extrair_numero_nfse_nacional(body)
            chave_acesso = extrair_chave_acesso_nfse_nacional(body)

            if numero_nfse:
                result["success"] = True
                result["numero_nfse"] = numero_nfse
                result["chave_acesso"] = chave_acesso
                result["codigo_verificacao"] = chave_acesso
                logger.info(
                    "ISSNet Nacional: NFS-e EMITIDA! nº %s, chave=%s",
                    numero_nfse, chave_acesso,
                )
            else:
                # Sem número mas sem erro explícito — pode ser processamento pendente
                result["erro"] = "NFS-e não encontrada na resposta. Verifique no portal."
                logger.warning("ISSNet Nacional: resposta sem número NFS-e: %s", body[:500])

        except Exception as e:
            logger.exception("ISSNet Nacional: erro inesperado na emissão DPS %d: %s", numero_dps, e)
            result["erro"] = str(e)

        return result

    def cancelar_nfse(
        self,
        numero_nfse: str,
        motivo: str = "",
        codigo_cancelamento: str = "1",
        chave_acesso: str = "",
    ) -> dict[str, Any]:
        """Cancela NFS-e via ISSNet Nacional."""
        result: dict[str, Any] = {"success": False, "erro": None, "xml_resposta": None}

        try:
            ambiente_int = 1 if self.ambiente == "producao" else 2

            xml_cancelamento = construir_xml_cancelar_nfse_nacional(
                numero_nfse=numero_nfse,
                codigo_cancelamento=codigo_cancelamento,
                motivo_cancelamento=motivo,
                prestador_cnpj=self.prestador_cnpj,
                prestador_inscricao_municipal=self.prestador_im,
                codigo_municipio=self.codigo_municipio,
                chave_acesso=chave_acesso,
                ambiente=ambiente_int,
            )

            xml_assinado = self._assinar_xml(xml_cancelamento)
            resposta = self._enviar_soap(xml_assinado, SOAP_ACTION_NACIONAL_CANCELAR_NFSE)
            result["xml_resposta"] = resposta

            body = extrair_body_soap(resposta)
            erros = extrair_erros(body)

            if erros:
                result["erro"] = erros
            else:
                result["success"] = True
                logger.info("ISSNet Nacional: NFS-e %s cancelada com sucesso.", numero_nfse)

        except Exception as e:
            logger.exception("ISSNet Nacional: erro ao cancelar NFS-e %s: %s", numero_nfse, e)
            result["erro"] = str(e)

        return result

    def consultar_nfse_por_dps(
        self,
        numero_dps: int,
        serie_dps: str = "1",
    ) -> dict[str, Any]:
        """Consulta NFS-e por DPS via ISSNet Nacional."""
        result: dict[str, Any] = {"success": False, "numero_nfse": None, "chave_acesso": None, "erro": None}

        try:
            ambiente_int = 1 if self.ambiente == "producao" else 2

            xml_consulta = construir_xml_consultar_nfse_por_dps(
                numero_dps=numero_dps,
                serie_dps=serie_dps,
                prestador_cnpj=self.prestador_cnpj,
                prestador_inscricao_municipal=self.prestador_im,
                codigo_municipio=self.codigo_municipio,
                ambiente=ambiente_int,
            )

            resposta = self._enviar_soap(xml_consulta, SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS)
            body = extrair_body_soap(resposta)
            erros = extrair_erros(body)

            if erros:
                result["erro"] = erros
            else:
                result["success"] = True
                result["numero_nfse"] = extrair_numero_nfse_nacional(body)
                result["chave_acesso"] = extrair_chave_acesso_nfse_nacional(body)

        except Exception as e:
            logger.exception("ISSNet Nacional: erro na consulta DPS %d: %s", numero_dps, e)
            result["erro"] = str(e)

        return result

    def testar_conexao(self) -> dict[str, Any]:
        """Testa conexão com o webservice Nacional (valida certificado + endpoint)."""
        try:
            xml_consulta = construir_xml_consultar_nfse_por_dps(
                numero_dps=99999,
                serie_dps="1",
                prestador_cnpj=self.prestador_cnpj,
                prestador_inscricao_municipal=self.prestador_im,
                codigo_municipio=self.codigo_municipio,
                ambiente=2,  # homologação para teste
            )
            resposta = self._enviar_soap(xml_consulta, SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS)

            if resposta and ("Fault" not in resposta or "DPS" in resposta.lower()):
                return {
                    "success": True,
                    "message": f"Conexão OK com ISSNet Nacional ({self.ambiente}). Endpoint: {self.url}",
                }
            return {
                "success": False,
                "detail": f"Resposta inesperada: {resposta[:200]}",
            }
        except Exception as e:
            return {
                "success": False,
                "detail": f"Erro ao conectar: {e}",
            }
