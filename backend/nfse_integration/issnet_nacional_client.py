"""Cliente ISSNet padrão Nacional (RTC) — Ribeirão Preto.

Substitui o ABRASF 2.04 a partir de 03/08/2026.
Endpoint: https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx
Métodos: RecepcionarLoteDpsSincrono, CancelarNfse, ConsultarNfseDps, ConsultarUrlNfse.

Envelope SOAP alinhado ao ACBr (ISSNet APIPrópria):
  - SOAPAction: http://www.sped.fazenda.gov.br/nfse/<Operacao>
  - Body: <nfse:Operacao xmlns:nfse="http://www.sped.fazenda.gov.br/nfse">
  - nfseCabecMsg / nfseDadosMsg como xsd:string (XML escapado)
"""
import hashlib
import logging
import os
import re
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
    CABEC_MSG,
    CABEC_MSG_NACIONAL,
    ISSNET_NACIONAL_URLS,
    NS_NFSE_NACIONAL,
    SOAP_ACTION_NACIONAL_CANCELAR_NFSE,
    SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS,
    SOAP_ACTION_NACIONAL_GERAR_NFSE,
    SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO,
)
from nfse_integration.issnet_nacional_xml_builder import (
    construir_xml_cancelar_nfse_nacional,
    construir_xml_consultar_nfse_por_dps,
    construir_xml_enviar_lote_dps_sincrono,
    construir_xml_gerar_nfse_envio,
    extrair_chave_acesso_nfse_nacional,
    extrair_numero_nfse_nacional,
)
from nfse_integration.issnet_response import extrair_body_soap, extrair_erros
from nfse_integration.issnet_soap import (
    _montar_soap_envelope,
    issnet_corpo_parece_xml,
    issnet_erro_assinatura,
    issnet_erro_schema_ou_cabecalho,
    issnet_fault_soap_generico,
    montar_soap_envelope_sem_ns_raiz,
)
from nfse_integration.issnet_xml_builder import somente_digitos
from nfse_integration.nacional.xml_signer import (
    assinar_lote_dps_em_elemento,
    assinar_xml_enviar_lote_dps,
)

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

    def _assinar_dps_signxml(self, dps_xml_str: str) -> str:
        """Assina DPS isolada usando signxml (RSA-SHA1, C14N inclusiva, inline).

        signxml gera a Signature sem espaços/newlines extras, o que evita
        problemas de formatação que o xmlsec introduz e que podem invalidar
        a assinatura no servidor ISSNet.
        """
        from contextlib import suppress
        from lxml import etree
        from signxml import XMLSigner, methods
        from cryptography.hazmat.primitives.serialization import (
            Encoding, NoEncryption, PrivateFormat, pkcs12,
        )

        created_tmp = not (self.cert_path and os.path.isfile(self.cert_path))
        cert_path = self._pfx_temp()

        try:
            # Carregar certificado
            with open(cert_path, "rb") as f:
                pfx_data = f.read()
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_data, self.cert_password.encode(),
            )

            key_pem = private_key.private_bytes(
                Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption(),
            )
            cert_pem = certificate.public_bytes(Encoding.PEM)

            # Parse DPS
            dps_root = etree.fromstring(dps_xml_str.encode("utf-8"))
            ns = "http://www.sped.fazenda.gov.br/nfse"
            inf_dps = dps_root.find(f"{{{ns}}}infDPS")
            if inf_dps is None:
                raise ValueError("infDPS não encontrado na DPS")

            inf_id = inf_dps.get("Id")
            if not inf_id:
                raise ValueError("Atributo Id ausente em infDPS")

            # Assinar com signxml
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha1",
                digest_algorithm="sha1",
                c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
            )

            signed_root = signer.sign(
                dps_root,
                key=key_pem,
                cert=cert_pem,
                reference_uri=f"#{inf_id}",
                id_attribute="Id",
            )

            # Serializar sem <?xml?> e sem formatação
            resultado = etree.tostring(
                signed_root, encoding="unicode", xml_declaration=False,
            )

            logger.info(
                "ISSNet Nacional: DPS assinada com signxml (RSA-SHA1, Reference=#%s, %d bytes)",
                inf_id, len(resultado),
            )
            return resultado

        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

    def _assinar_dupla(self, lote_xml: str) -> str:
        """Dupla assinatura conforme suporte NotaControl (07/08/2026).

        Fluxo obrigatório:
        1) Extrair cada DPS do lote como documento isolado (com xmlns próprio)
        2) Assinar cada DPS isoladamente (RSA-SHA1, C14N inclusiva)
        3) Remontar o EnviarLoteDpsSincronoEnvio com as DPS já assinadas
           (via concatenação de string para preservar o XML byte-a-byte)
        4) Assinar o LoteDps (segunda assinatura)
        5) Retornar o XML final sem nenhuma formatação adicional

        IMPORTANTE: O lxml remove xmlns redundante quando pai e filho compartilham
        o mesmo namespace. Por isso o passo 3 usa string concatenation para a DPS,
        e o passo 4 re-parseia o resultado final para assinar o lote via xmlsec.
        Após a assinatura do lote, serializa uma única vez sem formatação.
        """
        from contextlib import suppress
        from lxml import etree
        from nfse_integration.nacional.xml_signer import (
            _carregar_chave_xmlsec,
            _completar_cadeia_certificados,
            _assinar_elemento_por_id,
            assinar_xml_enviar_lote_dps,
        )

        created_tmp = not (self.cert_path and os.path.isfile(self.cert_path))
        cert_path = self._pfx_temp()

        try:
            ns = "http://www.sped.fazenda.gov.br/nfse"

            # Parse o lote para extrair dados e DPS
            root = etree.fromstring(lote_xml.encode("utf-8"))
            dps_nodes = root.findall(f".//{{{ns}}}DPS")
            if not dps_nodes:
                raise ValueError("Nenhum DPS encontrado no lote para assinatura.")

            # Extrair dados do lote
            lote_el = root.find(f"{{{ns}}}LoteDps")
            if lote_el is None:
                raise ValueError("LoteDps não encontrado no XML.")

            numero_lote = lote_el.findtext(f"{{{ns}}}NumeroLote") or "1"
            lote_id = lote_el.get("Id") or f"Lote{numero_lote}"
            lote_versao = lote_el.get("versao") or "1.00"

            prest_el = lote_el.find(f"{{{ns}}}Prestador")
            prest_cnpj = ""
            prest_im = ""
            if prest_el is not None:
                prest_cnpj = prest_el.findtext(f"{{{ns}}}CNPJ") or ""
                prest_im = prest_el.findtext(f"{{{ns}}}IM") or ""

            qtd_dps = str(len(dps_nodes))

            # ---- PASSO 1+2: Assinar cada DPS isoladamente ----
            dps_assinados_str = []
            for dps in dps_nodes:
                # Serializar DPS como root (garante xmlns no elemento)
                dps_isolado_str = etree.tostring(
                    dps, encoding="unicode", xml_declaration=False,
                )
                # Assinar a DPS isolada (apenas DPS, sem lote)
                dps_assinado_str = assinar_xml_enviar_lote_dps(
                    dps_isolado_str,
                    cert_path,
                    self.cert_password,
                    assinar_lote=False,
                    prefixo_ds=False,
                    usar_cadeia=False,
                    usar_sha256=False,
                )
                # Remove <?xml ...?> se presente
                dps_assinado_str = re.sub(
                    r'^\s*<\?xml[^?]*\?>\s*', '', dps_assinado_str, count=1,
                )
                dps_assinados_str.append(dps_assinado_str)
                logger.info(
                    "ISSNet Nacional: DPS assinada isoladamente (len=%d bytes)",
                    len(dps_assinado_str),
                )

            # ---- PASSO 3: Remontar lote via string (preserva xmlns na DPS) ----
            # Montamos o lote XML por concatenação para não perder o xmlns
            # que o lxml removeria se usássemos append de elementos.
            prest_im_tag = f"<IM>{prest_im}</IM>" if prest_im else ""
            dps_concat = "".join(dps_assinados_str)

            lote_xml_com_dps_assinadas = (
                f'<EnviarLoteDpsSincronoEnvio xmlns="{ns}">'
                f'<LoteDps versao="{lote_versao}" Id="{lote_id}">'
                f'<NumeroLote>{numero_lote}</NumeroLote>'
                f'<Prestador><CNPJ>{prest_cnpj}</CNPJ>{prest_im_tag}</Prestador>'
                f'<QuantidadeDps>{qtd_dps}</QuantidadeDps>'
                f'<ListaDps>{dps_concat}</ListaDps>'
                f'</LoteDps>'
                f'</EnviarLoteDpsSincronoEnvio>'
            )

            # ---- PASSO 4: Assinar o LoteDps (segunda assinatura) ----
            # Re-parseia para assinar via xmlsec (necessário para calcular digest)
            # NOTA: o lxml vai normalizar namespaces aqui, mas o DigestValue do
            # lote é calculado SOBRE o LoteDps (não sobre cada DPS individual).
            # A assinatura de cada DPS já foi feita sobre o documento isolado
            # (com xmlns presente) — o que importa é que o CONTEÚDO da DPS
            # (infDPS) não mude. A remoção do xmlns redundante da tag <DPS>
            # não afeta a assinatura da DPS porque a Reference aponta para
            # infDPS (não para DPS) e o transform enveloped-signature + C14N
            # canoniza a partir do infDPS.
            final_root = etree.fromstring(lote_xml_com_dps_assinadas.encode("utf-8"))
            final_lote = final_root.find(f"{{{ns}}}LoteDps")

            if final_lote is None:
                raise ValueError("LoteDps não encontrado após remontagem.")

            # Garantir Id no LoteDps
            if not final_lote.get("Id"):
                final_lote.set("Id", lote_id)

            key, cert_obj, extra_certs = _carregar_chave_xmlsec(cert_path, self.cert_password)
            chain = _completar_cadeia_certificados(cert_obj, extra_certs)

            _assinar_elemento_por_id(
                final_root, final_lote, key, lote_id, cert_obj, chain,
                prefixo_ds=False, usar_cadeia=False, usar_sha256=False,
            )

            # ---- PASSO 5: Serializar sem formatação ----
            resultado = etree.tostring(
                final_root, encoding="unicode", xml_declaration=False,
            )
            logger.info(
                "ISSNet Nacional: dupla assinatura concluída (lote=%s, %d DPS, %d bytes)",
                lote_id, len(dps_assinados_str), len(resultado),
            )
            return resultado

        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

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
            ):
                # Lote/GerarNfseEnvio: assina cada DPS dentro.
                # Suporte NotaControl (03/08/2026) confirmou: assinatura deve ser
                # RSA-SHA1 com canonização inclusiva (funcionava assim nos dias
                # 01-02/08; a troca para SHA-256 quebrou a validação - E0714).
                # RecepcionarLoteDpsSincrono também exige assinatura do lote
                # (EM003 "A assinatura do Lote é obrigatória" se ausente).
                return assinar_xml_enviar_lote_dps(
                    xml_str,
                    cert_path,
                    self.cert_password,
                    assinar_lote=True,
                    prefixo_ds=False,
                    usar_cadeia=False,
                    usar_sha256=False,
                )
            if root_local == "DPS":
                # DPS isolado: assinar diretamente (RSA-SHA1, conforme suporte)
                return assinar_xml_enviar_lote_dps(
                    xml_str,
                    cert_path,
                    self.cert_password,
                    assinar_lote=False,
                    prefixo_ds=False,
                    usar_cadeia=False,
                    usar_sha256=False,
                )
            # CancelarNfseEnvio e afins: assinatura Pedido (mesmo padrão ISSNet)
            return assinar_xml_issnet(xml_str, cert_path, self.cert_password)
        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

    def _enviar_soap(self, xml_dados: str, soap_action: str) -> str:
        """POST SOAP 1.1 com mTLS.

        Envia os dados como XML literal (aninhado) dentro de nfseDadosMsg.
        O envelope NÃO declara xmlns:nfse para evitar que a canonização C14N
        inclusiva capture namespaces extras. Os dados já contêm xmlns="..."
        declarado localmente (no EnviarLoteDpsSincronoEnvio), que é suficiente.

        O elemento da operação e nfseCabecMsg/nfseDadosMsg são declarados
        diretamente com o namespace (sem prefixo herdado do envelope).
        """
        nome_op = _nome_operacao_de_soap_action(soap_action)
        created_tmp = not (self.cert_path and os.path.isfile(self.cert_path))
        cert_path = self._pfx_temp()

        cabec_txt = self._cabec_msg_nacional_sem_ns("1.00", "1.00")

        try:
            with certificado_mtls_temporario(cert_path, self.cert_password) as (pem_cert, pem_key):
                from nfse_integration.issnet_soap import strip_xml_declaration

                dados_limpo = strip_xml_declaration(xml_dados or "")
                cabec_limpo = strip_xml_declaration(cabec_txt or "")

                # Envelope SOAP minimalista:
                # - Apenas xmlns:soapenv no root (sem xmlns:nfse!)
                # - O elemento da operação declara xmlns localmente
                # - nfseCabecMsg e nfseDadosMsg com conteúdo literal
                # Assim os dados ficam num contexto onde apenas xmlns:soapenv
                # está no escopo (não afeta C14N de elementos com namespace nfse).
                ns = NS_NFSE_NACIONAL
                envelope = (
                    '<?xml version="1.0" encoding="utf-8"?>'
                    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
                    '<soapenv:Header/>'
                    '<soapenv:Body>'
                    f'<{nome_op} xmlns="{ns}">'
                    f'<nfseCabecMsg>{cabec_limpo}</nfseCabecMsg>'
                    f'<nfseDadosMsg>{dados_limpo}</nfseDadosMsg>'
                    f'</{nome_op}>'
                    '</soapenv:Body>'
                    '</soapenv:Envelope>'
                )

                logger.info(
                    "ISSNet Nacional: envelope SOAP (aninhado sem xmlns:nfse no root, truncado 3000):\n%s",
                    envelope[:3000],
                )

                envelope_bytes = envelope.encode("utf-8")
                logger.info(
                    "ISSNet Nacional: envelope SHA-1 = %s (%d bytes)",
                    hashlib.sha1(envelope_bytes).hexdigest(), len(envelope_bytes),
                )

                headers = {
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": f'"{soap_action}"',
                    "Connection": "close",
                    "Accept": "text/xml",
                    "User-Agent": "LWK-Sistemas/ISSNet-Nacional",
                }
                logger.info(
                    "ISSNet Nacional SOAP %s (~%d bytes) → %s",
                    nome_op, len(envelope_bytes), self.url,
                )
                try:
                    r = req.post(
                        self.url,
                        data=envelope_bytes,
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
                        data=envelope_bytes,
                        headers=headers,
                        cert=(pem_cert, pem_key),
                        timeout=(8, 45),
                        verify=True,
                    )

                last_text = r.text or ""
                logger.info(
                    "ISSNet Nacional %s HTTP %s (%d bytes)",
                    nome_op, r.status_code, len(last_text),
                )

                if r.status_code >= 400 or "Fault" in last_text:
                    logger.error(
                        "ISSNet Nacional %s erro: %s",
                        nome_op, last_text[:2000],
                    )

                if issnet_erro_assinatura(last_text):
                    logger.error(
                        "ISSNet Nacional %s erro de assinatura: %s",
                        nome_op, last_text[:2000],
                    )

                return last_text
        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

    def _enviar_lote_dps_assinando_no_envelope(
        self, lote_xml_nao_assinado: str, soap_action: str,
    ) -> str:
        """Monta o envelope SOAP com o LoteDps SEM assinatura, faz o parse
        como UM ÚNICO documento e só então assina DPS/LoteDps já dentro
        desse contexto final.

        Orientação do suporte NotaControl (03/08/2026): "remova o xmlns [da
        DPS isolada] e assine [já no contexto final]" — a assinatura
        calculada sobre o documento isolado não sobrevive à inserção em um
        envelope que introduz namespaces ambiente (soapenv:, nfse:) porque a
        canonização C14N inclusiva captura TODOS os namespaces em escopo,
        usados ou não, no momento da verificação pelo servidor.
        """
        nome_op = _nome_operacao_de_soap_action(soap_action)
        created_tmp = not (self.cert_path and os.path.isfile(self.cert_path))
        cert_path = self._pfx_temp()

        cabec_txt = self._cabec_msg_nacional_sem_ns("1.00", "1.00")
        envelope_nao_assinado = montar_soap_envelope_sem_ns_raiz(
            nome_op, lote_xml_nao_assinado,
            cabec_txt=cabec_txt,
            target_ns=NS_NFSE_NACIONAL,
        )

        try:
            envelope_tree = etree.fromstring(envelope_nao_assinado.encode("utf-8"))
            ns = NS_NFSE_NACIONAL
            envio_root = envelope_tree.find(f".//{{{ns}}}EnviarLoteDpsSincronoEnvio")
            if envio_root is None:
                envio_root = envelope_tree.find(f".//{{{ns}}}EnviarLoteDpsEnvio")
            if envio_root is None:
                raise ValueError("EnviarLoteDpsSincronoEnvio não encontrado no envelope montado.")

            assinar_lote_dps_em_elemento(
                envio_root,
                cert_path,
                self.cert_password,
                assinar_lote=True,
                prefixo_ds=False,
                usar_cadeia=False,
                usar_sha256_xmlsec=False,
            )

            envelope_final = etree.tostring(
                envelope_tree, encoding="utf-8", xml_declaration=True,
            ).decode("utf-8")
        finally:
            if created_tmp and os.path.isfile(cert_path):
                with suppress(OSError):
                    os.unlink(cert_path)

        logger.info(
            "ISSNet Nacional: envelope SOAP (assinado no contexto final) (truncado):\n%s",
            envelope_final[:8000],
        )

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{soap_action}"',
            "Connection": "close",
            "Accept": "text/xml",
            "User-Agent": "LWK-Sistemas/ISSNet-Nacional",
        }
        cert_path2 = self._pfx_temp()
        created_tmp2 = not (self.cert_path and os.path.isfile(self.cert_path))
        try:
            with certificado_mtls_temporario(cert_path2, self.cert_password) as (pem_cert, pem_key):  # noqa: E501
                envelope_bytes = envelope_final.encode("utf-8")
                logger.info(
                    "ISSNet Nacional SOAP %s (~%d bytes, assinado-no-envelope) → %s",
                    nome_op, len(envelope_bytes), self.url,
                )
                try:
                    r = req.post(
                        self.url,
                        data=envelope_bytes,
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
                        data=envelope_bytes,
                        headers=headers,
                        cert=(pem_cert, pem_key),
                        timeout=(8, 45),
                        verify=True,
                    )
                texto = r.text or ""
                logger.info(
                    "ISSNet Nacional %s HTTP %s (%d bytes, assinado-no-envelope)",
                    nome_op, r.status_code, len(texto),
                )
                if r.status_code >= 400 or "Fault" in texto:
                    logger.error(
                        "ISSNet Nacional %s erro (assinado-no-envelope): %s",
                        nome_op, texto[:2000],
                    )
                return texto
        finally:
            if created_tmp2 and os.path.isfile(cert_path2):
                with suppress(OSError):
                    os.unlink(cert_path2)

    @staticmethod
    def _cabec_msg_nacional_sped(versao: str, versao_dados: str = "1.00") -> str:
        ns = NS_NFSE_NACIONAL
        cab = etree.Element(f"{{{ns}}}cabecalho", nsmap={None: ns})
        cab.set("versao", versao)
        vd = etree.SubElement(cab, f"{{{ns}}}versaoDados")
        vd.text = versao_dados
        return etree.tostring(cab, encoding="unicode", xml_declaration=False)

    @staticmethod
    def _cabec_msg_nacional_sem_ns(versao: str, versao_dados: str = "1.00") -> str:
        # Cabeçalho conforme print enviado pelo suporte NotaControl (03/08/2026):
        # <cabecalho versao="1.01" xmlns="...">  — atributo versao ANTES do xmlns.
        ns = "http://www.sped.fazenda.gov.br/nfse"
        return (
            f'<cabecalho versao="{versao}" xmlns="{ns}">'
            f'<versaoDados>{versao_dados}</versaoDados>'
            f'</cabecalho>'
        )

    @staticmethod
    def _cabec_msg_nacional_abrasf(versao: str, versao_dados: str = "1.00") -> str:
        ns = "http://www.abrasf.org.br/nfse.xsd"
        cab = etree.Element(f"{{{ns}}}cabecalho", nsmap={None: ns})
        cab.set("versao", versao)
        vd = etree.SubElement(cab, f"{{{ns}}}versaoDados")
        vd.text = versao_dados
        return etree.tostring(cab, encoding="unicode", xml_declaration=False)

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
        p_tot_trib_sn: Decimal | None = None,
        indicador_operacao: str = "",
        cst_ibscbs: str = "000",
        cclass_trib_ibscbs: str = "000001",
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

            # O padrão nacional DPS não possui operação "GerarNfse" (isso é
            # nomenclatura legada ABRASF). A emissão síncrona de um lote
            # (mesmo que com uma única DPS) é feita via "EnviarLoteDpsSincrono",
            # conforme Manual de Integração Webservice (Sistema Nacional NFS-e).
            lote_xml = construir_xml_enviar_lote_dps_sincrono(
                numero_lote=numero_dps,
                prestador_cnpj=self.prestador_cnpj,
                prestador_inscricao_municipal=self.prestador_im,
                prestador_telefone=prestador_telefone,
                prestador_email=prestador_email,
                numero_dps=numero_dps,
                serie_dps=serie_dps,
                data_emissao=data_emissao,
                data_competencia=data_competencia,
                codigo_municipio_emissor=self.codigo_municipio,
                ambiente=ambiente_int,
                optante_simples_nacional=self.optante_simples,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                tomador_telefone=tomador_telefone,
                tomador_email=tomador_email,
                codigo_municipio_prestacao=codigo_municipio_prestacao or self.codigo_municipio,
                municipio_prestacao_nome=(tomador_endereco or {}).get("cidade", ""),
                codigo_tributacao_nacional=codigo_tributacao_nacional,
                codigo_tributacao_municipal=codigo_tributacao_municipal,
                descricao_servico=descricao_servico,
                codigo_nbs=codigo_nbs,
                valor_servicos=valor_servicos,
                aliquota_iss=aliquota_iss,
                p_tot_trib_sn=p_tot_trib_sn,
                indicador_operacao=indicador_operacao,
                cst_ibscbs=cst_ibscbs,
                cclass_trib_ibscbs=cclass_trib_ibscbs,
            )

            # Emissão via GerarNfse (DPS única assinada isoladamente).
            # Usando signxml para gerar Signature inline (sem espaços/newlines
            # que o xmlsec adiciona e que podem quebrar a validação no ISSNet).
            logger.info(
                "ISSNet Nacional: assinando DPS nº %d isoladamente com signxml para GerarNfse...",
                numero_dps,
            )

            # Extrair a DPS do lote (que foi montado como EnviarLoteDpsSincrono)
            from lxml import etree as _etree
            _ns = "http://www.sped.fazenda.gov.br/nfse"
            _root = _etree.fromstring(lote_xml.encode("utf-8"))
            _dps_el = _root.find(f".//{{{_ns}}}DPS")
            if _dps_el is None:
                raise ValueError("DPS não encontrada no XML do lote.")

            # Serializar DPS isolada (com xmlns)
            dps_isolada_str = _etree.tostring(_dps_el, encoding="unicode", xml_declaration=False)

            # Assinar com signxml (RSA-SHA1 + C14N inclusiva, inline)
            xml_dps_assinada = self._assinar_dps_signxml(dps_isolada_str)

            # Montar GerarNfseEnvio com a DPS assinada
            xml_gerar_nfse = (
                f'<GerarNfseEnvio xmlns="{_ns}">'
                f'{xml_dps_assinada}'
                f'</GerarNfseEnvio>'
            )

            resposta_soap = self._enviar_soap(
                xml_gerar_nfse,
                SOAP_ACTION_NACIONAL_GERAR_NFSE,
            )
            result["xml_dps"] = lote_xml
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
