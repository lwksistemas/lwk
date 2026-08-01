"""Cliente ISSNet padrão Nacional (RTC) — Ribeirão Preto.

Substitui o ABRASF 2.04 a partir de 03/08/2026.
Endpoint: https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx
Métodos: RecepcionarLoteDpsSincrono, CancelarNfse, ConsultarNfseDps, ConsultarUrlNfse.

Envelope SOAP alinhado ao ACBr (ISSNet APIPrópria):
  - SOAPAction: http://www.sped.fazenda.gov.br/nfse/<Operacao>
  - Body: <nfse:Operacao xmlns:nfse="http://www.sped.fazenda.gov.br/nfse">
  - nfseCabecMsg / nfseDadosMsg como xsd:string (XML escapado)
"""
import logging
import os
import tempfile
import time
from contextlib import suppress
from datetime import datetime
from decimal import Decimal
from typing import Any

import requests as req
from lxml import etree

from nfse_integration.issnet_cert import certificado_mtls_temporario
from nfse_integration.issnet_constants import (
    CABEC_MSG_NACIONAL,
    ISSNET_NACIONAL_URLS,
    NS_NFSE_NACIONAL,
    SOAP_ACTION_NACIONAL_CANCELAR_NFSE,
    SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS,
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
from nfse_integration.issnet_soap import (
    _montar_soap_envelope,
    issnet_corpo_parece_xml,
    issnet_erro_schema_ou_cabecalho,
    issnet_fault_soap_generico,
)
from nfse_integration.issnet_xml_builder import somente_digitos
from nfse_integration.nacional.xml_signer import assinar_xml_enviar_lote_dps

logger = logging.getLogger(__name__)


def _nome_operacao_de_soap_action(soap_action: str) -> str:
    action = (soap_action or "").strip().strip('"')
    return action.rsplit("/", 1)[-1] if "/" in action else action


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

    def _pfx_temp(self) -> str:
        """Garante path .pfx (grava bytes em temp se necessário). Caller remove se criou temp."""
        if self.cert_path and os.path.isfile(self.cert_path):
            return self.cert_path
        if not self.cert_bytes:
            raise ValueError("Certificado digital não disponível.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pfx", prefix="issnet_nac_") as tmp:
            tmp.write(bytes(self.cert_bytes))
            return tmp.name

    def _assinar_xml(self, xml_str: str) -> str:
        """Assina XML Nacional: lote DPS via assinador SPED; cancelamento via ISSNet."""
        from lxml import etree

        from nfse_integration.issnet_xml_signer import assinar_xml_issnet

        created_tmp = not (self.cert_path and os.path.isfile(self.cert_path))
        cert_path = self._pfx_temp()
        try:
            root = etree.fromstring(xml_str.encode("utf-8"))
            root_local = etree.QName(root.tag).localname if root.tag else ""
            if root_local in (
                "EnviarLoteDpsSincronoEnvio",
                "EnviarLoteDpsEnvio",
                "GerarNfseEnvio",
                "DPS",
            ):
                # ISSNet Nacional: assina apenas cada DPS, sem assinatura de lote,
                # sem prefixo ds: e com apenas o certificado folha na X509Data,
                # conforme exemplos oficiais retornados pelo servidor.
                return assinar_xml_enviar_lote_dps(
                    xml_str,
                    cert_path,
                    self.cert_password,
                    assinar_lote=False,
                    prefixo_ds=False,
                    usar_cadeia=False,
                )
            # CancelarNfseEnvio e afins: assinatura Pedido (mesmo padrão ISSNet)
            return assinar_xml_issnet(xml_str, cert_path, self.cert_password)
        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

    def _enviar_soap(self, xml_dados: str, soap_action: str) -> str:
        """POST SOAP 1.1 com mTLS; tenta cabeçalhos e envelopes alternativos."""
        nome_op = _nome_operacao_de_soap_action(soap_action)
        created_tmp = not (self.cert_path and os.path.isfile(self.cert_path))
        cert_path = self._pfx_temp()

        # Combinações (label, cabecalho_xml, target_namespace, modo) em ordem de prioridade
        # para o ISSNet Nacional. Ribeirão Preto (template Unimake) usa SPED 1.01 + aninhado.
        tentativas = [
            # Conforme documentação ISSNet Nacional, o cabeçalho cru sem xmlns
            # e o XML aninhado são o único formato que passa do schema.
            ("SPED sem xmlns 1.01 aninhado", self._cabec_msg_nacional_sem_ns("1.01"), NS_NFSE_NACIONAL, "aninhado"),
            ("SPED sem xmlns 1.01 CDATA", self._cabec_msg_nacional_sem_ns("1.01"), NS_NFSE_NACIONAL, "cdata"),
            ("SPED sem xmlns 1.01 xsd:string", self._cabec_msg_nacional_sem_ns("1.01"), NS_NFSE_NACIONAL, "xsd_string"),
            ("SPED 1.01 aninhado", CABEC_MSG_NACIONAL, NS_NFSE_NACIONAL, "aninhado"),
            ("SPED 1.01 CDATA", CABEC_MSG_NACIONAL, NS_NFSE_NACIONAL, "cdata"),
            ("SPED 1.01 xsd:string", CABEC_MSG_NACIONAL, NS_NFSE_NACIONAL, "xsd_string"),
            ("SPED 1.00 aninhado", self._cabec_msg_nacional_sped("1.00"), NS_NFSE_NACIONAL, "aninhado"),
            ("SPED 1.00 CDATA", self._cabec_msg_nacional_sped("1.00"), NS_NFSE_NACIONAL, "cdata"),
            ("SPED 1.00 xsd:string", self._cabec_msg_nacional_sped("1.00"), NS_NFSE_NACIONAL, "xsd_string"),
            ("ABRASF 2.04 aninhado", self._cabec_msg_nacional_abrasf("2.04"), NS_NFSE_NACIONAL, "aninhado"),
            ("ABRASF 2.04 CDATA", self._cabec_msg_nacional_abrasf("2.04"), NS_NFSE_NACIONAL, "cdata"),
            ("ABRASF 2.04 xsd:string", self._cabec_msg_nacional_abrasf("2.04"), NS_NFSE_NACIONAL, "xsd_string"),
        ]

        try:
            with certificado_mtls_temporario(cert_path, self.cert_password) as (pem_cert, pem_key):
                last_text = ""
                for cabec_label, cabec_txt, target_ns, modo in tentativas:
                    modo_label = {
                        "xsd_string": "xsd:string (ACBr XmlToStr)",
                        "cdata": "CDATA",
                        "aninhado": "XML aninhado",
                    }[modo]
                    label = f"{cabec_label} + {modo_label}"
                    envelope = _montar_soap_envelope(
                        nome_op, xml_dados, cabec_txt=cabec_txt,
                        target_ns=target_ns, modo=modo,
                    )
                    logger.debug("ISSNet Nacional: envelope SOAP (%s):\n%s", label, envelope)
                    headers = {
                        "Content-Type": "text/xml; charset=utf-8",
                        "SOAPAction": f'"{soap_action}"',
                        "Connection": "close",
                        "Accept": "text/xml",
                        "User-Agent": "LWK-Sistemas/ISSNet-Nacional",
                    }
                    logger.info(
                        "ISSNet Nacional SOAP %s (~%d bytes, %s) → %s",
                        nome_op, len(envelope.encode("utf-8")), label, self.url,
                    )
                    try:
                        r = req.post(
                            self.url,
                            data=envelope.encode("utf-8"),
                            headers=headers,
                            cert=(pem_cert, pem_key),
                            timeout=(8, 45),
                            verify=True,
                        )
                    except (req.exceptions.ConnectionError, req.exceptions.ReadTimeout) as e:
                        logger.warning("ISSNet Nacional %s conexão falhou (%s); retry 1x", nome_op, e)
                        time.sleep(1.5)
                        r = req.post(
                            self.url,
                            data=envelope.encode("utf-8"),
                            headers=headers,
                            cert=(pem_cert, pem_key),
                            timeout=(8, 45),
                            verify=True,
                        )

                    last_text = r.text or ""
                    logger.info(
                        "ISSNet Nacional %s HTTP %s (%d bytes) via %s",
                        nome_op, r.status_code, len(last_text), label,
                    )

                    ns_fault = (
                        "with namespace name" in last_text
                        and "was not found" in last_text
                    )
                    schema_fault = issnet_erro_schema_ou_cabecalho(last_text)

                    if r.status_code >= 400 or "Fault" in last_text:
                        logger.error(
                            "ISSNet Nacional %s erro (%s): %s",
                            nome_op, label, last_text[:2000],
                        )

                    if schema_fault:
                        logger.error(
                            "ISSNet Nacional %s erro de schema/cabeçalho (%s): envelope=%s | resposta=%s",
                            nome_op, label, envelope[:4000], last_text[:4000],
                        )

                    if issnet_corpo_parece_xml(last_text) and not (
                        issnet_fault_soap_generico(last_text) or ns_fault or schema_fault
                    ):
                        # Resposta válida sem erros reconhecidos -> retorna
                        return last_text

                    # Se não for erro de schema/cabeçalho, não adianta insistir com outros formatos
                    if not (ns_fault or schema_fault):
                        return last_text

                return last_text
        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

    @staticmethod
    def _cabec_msg_nacional_abrasf(versao: str) -> str:
        return (
            f'<cabecalho xmlns="http://www.abrasf.org.br/nfse.xsd" versao="{versao}">'
            '<versaoDados>1.01</versaoDados>'
            '</cabecalho>'
        )

    @staticmethod
    def _cabec_msg_nacional_sped(versao: str) -> str:
        return (
            f'<cabecalho xmlns="http://www.sped.fazenda.gov.br/nfse" versao="{versao}">'
            '<versaoDados>1.01</versaoDados>'
            '</cabecalho>'
        )

    @staticmethod
    def _cabec_msg_nacional_sem_ns(versao: str) -> str:
        return (
            f'<cabecalho versao="{versao}">'
            '<versaoDados>1.01</versaoDados>'
            '</cabecalho>'
        )

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

            logger.info("ISSNet Nacional: assinando XML DPS nº %d...", numero_dps)
            xml_assinado = self._assinar_xml(xml_envio)
            result["xml_dps"] = xml_assinado
            logger.debug("ISSNet Nacional: XML DPS assinado completo:\n%s", xml_assinado)

            try:
                root_signed = etree.fromstring(xml_assinado.encode("utf-8"))
                ns_sig = "http://www.w3.org/2000/09/xmldsig#"
                sig_count = len(root_signed.findall(f".//{{{ns_sig}}}Signature"))
                cert_count = len(root_signed.findall(f".//{{{ns_sig}}}X509Certificate"))
                logger.info(
                    "ISSNet Nacional: XML assinado - %d assinatura(s), %d certificado(s) X509",
                    sig_count, cert_count,
                )
            except Exception as e:
                logger.debug("Não foi possível contar assinaturas/certificados: %s", e)

            logger.info(
                "ISSNet Nacional: enviando DPS nº %d ao webservice (%s)...",
                numero_dps, self.ambiente,
            )
            resposta_soap = self._enviar_soap(
                xml_assinado,
                SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO,
            )
            result["xml_resposta"] = resposta_soap

            body = extrair_body_soap(resposta_soap)
            erros = extrair_erros(body)

            if erros:
                result["erro"] = erros
                logger.warning("ISSNet Nacional: erro na emissão DPS %d: %s", numero_dps, erros)
                return result

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
                if "Fault" in (resposta_soap or ""):
                    preview = " ".join((resposta_soap or "").split())
                    result["erro"] = f"SOAP Fault do ISSNet Nacional: {preview[:500]}"
                else:
                    result["erro"] = "NFS-e não encontrada na resposta. Verifique no portal."
                logger.warning("ISSNet Nacional: resposta sem número NFS-e: %s", (body or "")[:500])

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
        result: dict[str, Any] = {
            "success": False, "numero_nfse": None, "chave_acesso": None, "erro": None,
        }

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
        """Testa conexão com o webservice Nacional (certificado + endpoint)."""
        try:
            xml_consulta = construir_xml_consultar_nfse_por_dps(
                numero_dps=99999,
                serie_dps="1",
                prestador_cnpj=self.prestador_cnpj,
                prestador_inscricao_municipal=self.prestador_im,
                codigo_municipio=self.codigo_municipio,
                ambiente=2 if self.ambiente == "homologacao" else 1,
            )
            resposta = self._enviar_soap(xml_consulta, SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS)

            if resposta and ("Fault" not in resposta or "DPS" in resposta.lower() or "MensagemRetorno" in resposta):
                return {
                    "success": True,
                    "message": f"Conexão OK com ISSNet Nacional ({self.ambiente}). Endpoint: {self.url}",
                }
            return {
                "success": False,
                "detail": f"Resposta inesperada: {(resposta or '')[:200]}",
            }
        except Exception as e:
            return {
                "success": False,
                "detail": f"Erro ao conectar: {e}",
            }
