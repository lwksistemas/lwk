"""Cliente principal do provedor NFS-e Nacional (ADN).

Orquestra: construção XML → assinatura → compressão → envio → parse resposta.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from .constants import SEFIN_NFSE_URLS
from .transport import (
    comprimir_e_codificar,
    consultar_dfe_nsu,
    enviar_dps_sefin,
    interpretar_resposta_emissao,
)
from .xml_builder import construir_xml_dps
from .xml_signer import assinar_xml_dps, assinar_xml_dps_bytes

logger = logging.getLogger(__name__)


class NacionalClient:
    """Cliente para emissão de NFS-e via ADN (Ambiente de Dados Nacional).

    Uso:
        client = NacionalClient(
            pfx_path='/path/to/cert.pfx',
            senha_pfx='senha123',
            ambiente='homologacao',
        )
        resultado = client.emitir_nfse(...)
    """

    def __init__(
        self,
        pfx_path: str | None = None,
        pfx_bytes: bytes | None = None,
        senha_pfx: str = "",
        ambiente: str = "producao",
    ):
        """Args:
        pfx_path: Caminho para o certificado .pfx (A1)
        pfx_bytes: Bytes do certificado (alternativa ao path, para BinaryField)
        senha_pfx: Senha do certificado
        ambiente: 'producao' ou 'homologacao'

        """
        self.pfx_path = pfx_path
        self.pfx_bytes = pfx_bytes
        from core.encryption import decrypt_value

        self.senha_pfx = decrypt_value(senha_pfx) or senha_pfx
        self.ambiente = "homologacao" if ambiente == "homologacao" else "producao"

        if not pfx_path and not pfx_bytes:
            raise ValueError("Certificado .pfx obrigatório (pfx_path ou pfx_bytes)")
        if not senha_pfx:
            raise ValueError("Senha do certificado obrigatória")

    def emitir_nfse(
        self,
        # Identificação
        numero_dps: int,
        serie_dps: str = "900",
        codigo_municipio_prestador: str = "",
        # Prestador
        prestador_cnpj: str = "",
        prestador_inscricao_municipal: str = "",
        prestador_razao_social: str = "",
        prestador_nome_fantasia: str = "",
        prestador_endereco: dict[str, str] | None = None,
        prestador_telefone: str = "",
        prestador_email: str = "",
        # Tomador
        tomador_cpf_cnpj: str = "",
        tomador_nome: str = "",
        tomador_endereco: dict[str, str] | None = None,
        tomador_telefone: str = "",
        tomador_email: str = "",
        # Serviço
        codigo_servico: str = "14.01",
        descricao_servico: str = "",
        codigo_cnae: str = "",
        codigo_municipio_incidencia: str = "",
        codigo_tributacao_municipal: str = "",
        codigo_nbs: str = "",
        # Valores
        valor_servicos: Decimal = Decimal("0.00"),
        aliquota_iss: Decimal = Decimal("0.00"),
        valor_deducoes: Decimal = Decimal("0.00"),
        valor_desconto_incondicionado: Decimal = Decimal("0.00"),
        valor_desconto_condicionado: Decimal = Decimal("0.00"),
        # Tributação
        natureza_tributacao: int = 1,
        iss_retido: bool = False,
        optante_simples_nacional: bool = True,
        regime_especial: int = 0,
        incentivador_cultural: bool = False,
        p_tot_trib_sn: Decimal | None = None,
        # Controle
        codigo_numerico: int = 0,
        data_competencia: datetime | None = None,
    ) -> dict[str, Any]:
        """Emite NFS-e via ADN Nacional.

        Fluxo completo:
        1. Constrói XML da DPS
        2. Assina com certificado digital (XMLDSIG RSA-SHA256)
        3. Comprime (GZip) e codifica (Base64)
        4. Envia ao ADN via POST /DFe com mTLS
        5. Retorna resultado com ChaveAcesso e status

        Returns:
            Dict com:
                success: bool
                chave_acesso: str (se sucesso)
                nsu_recepcao: str (se sucesso)
                status_processamento: str
                xml_dps: str (XML assinado)
                alertas: list
                erros: list
                error: str (se falha)

        """
        result = {
            "success": False,
            "chave_acesso": None,
            "nsu_recepcao": None,
            "status_processamento": None,
            "xml_dps": None,
            "resposta_adn_raw": None,
            "alertas": [],
            "erros": [],
            "error": None,
        }

        try:
            # 1. Construir XML
            logger.info("NFS-e Nacional: construindo XML DPS nº %d...", numero_dps)
            xml_dps = construir_xml_dps(
                numero_dps=numero_dps,
                serie_dps=serie_dps,
                codigo_municipio_prestador=codigo_municipio_prestador,
                ambiente=self.ambiente,
                prestador_cnpj=prestador_cnpj,
                prestador_inscricao_municipal=prestador_inscricao_municipal,
                prestador_razao_social=prestador_razao_social,
                prestador_nome_fantasia=prestador_nome_fantasia,
                prestador_endereco=prestador_endereco,
                prestador_telefone=prestador_telefone,
                prestador_email=prestador_email,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                tomador_telefone=tomador_telefone,
                tomador_email=tomador_email,
                codigo_servico=codigo_servico,
                codigo_tributacao_municipal=codigo_tributacao_municipal,
                descricao_servico=descricao_servico,
                codigo_cnae=codigo_cnae,
                codigo_municipio_incidencia=codigo_municipio_incidencia,
                codigo_nbs=codigo_nbs,
                valor_servicos=valor_servicos,
                aliquota_iss=aliquota_iss,
                valor_deducoes=valor_deducoes,
                valor_desconto_incondicionado=valor_desconto_incondicionado,
                valor_desconto_condicionado=valor_desconto_condicionado,
                natureza_tributacao=natureza_tributacao,
                iss_retido=iss_retido,
                optante_simples_nacional=optante_simples_nacional,
                regime_especial=regime_especial,
                incentivador_cultural=incentivador_cultural,
                p_tot_trib_sn=p_tot_trib_sn,
                codigo_numerico=codigo_numerico,
                data_competencia=data_competencia,
            )

            # 2. Assinar XML
            logger.info("NFS-e Nacional: assinando XML...")
            if self.pfx_bytes:
                xml_assinado = assinar_xml_dps_bytes(
                    xml_dps, self.pfx_bytes, self.senha_pfx,
                    prefixo_ds=False, usar_cadeia=False, usar_sha256=True,
                )
            else:
                xml_assinado = assinar_xml_dps(
                    xml_dps, self.pfx_path, self.senha_pfx,
                    prefixo_ds=False, usar_cadeia=False, usar_sha256=True,
                )

            result["xml_dps"] = xml_assinado

            # 3. Comprimir e codificar
            logger.info("NFS-e Nacional: XML assinado (primeiros 300 chars): %s", xml_assinado[:300])
            xml_b64 = comprimir_e_codificar(xml_assinado)

            logger.info("NFS-e Nacional: enviando à Sefin (%s)...", self.ambiente)
            resposta = enviar_dps_sefin(
                dps_xml_b64=xml_b64,
                ambiente=self.ambiente,
                pfx_path=self.pfx_path,
                pfx_bytes=self.pfx_bytes,
                senha_pfx=self.senha_pfx,
            )

            data = resposta.get("data") if isinstance(resposta.get("data"), dict) else {}
            result["resposta_adn_raw"] = str(resposta)[:5000]
            logger.info("NFS-e Nacional: resposta Sefin: %s", str(data)[:2000])
            if not resposta.get("success"):
                lido = interpretar_resposta_emissao(data)
                result["erros"] = lido.get("erros") or self._extrair_erros(data)
                result["error"] = lido.get("error") or resposta.get("error", "Erro desconhecido no envio")
                logger.error("NFS-e Nacional: envio falhou: %s", result["error"])
                return result

            lido = interpretar_resposta_emissao(data)
            result["chave_acesso"] = lido.get("chave_acesso")
            result["nsu_recepcao"] = lido.get("nsu_recepcao")
            result["alertas"] = lido.get("alertas") or []
            result["erros"] = lido.get("erros") or []
            if lido.get("xml_nfse"):
                result["xml_nfse"] = lido["xml_nfse"]
            result["ambiente_resposta"] = data.get("tipoAmbiente") or data.get("TipoAmbiente")
            result["versao_aplicativo"] = data.get("versaoAplicativo") or data.get("VersaoAplicativo")
            result["data_processamento"] = data.get("dataHoraProcessamento") or data.get("DataHoraProcessamento")
            if lido.get("success"):
                result["success"] = True
                logger.info(
                    "NFS-e Nacional EMITIDA: ChaveAcesso=%s",
                    result["chave_acesso"],
                )
            else:
                result["error"] = lido.get("error") or "Sefin Nacional rejeitou a DPS"
                logger.warning("NFS-e Nacional: rejeitada: %s", result["error"])

        except Exception as e:
            logger.exception("NFS-e Nacional: erro inesperado: %s", e)
            result["error"] = str(e)

        return result

    def consultar_nfse(self, nsu: int, cnpj: str) -> dict[str, Any]:
        """Consulta NFS-e por NSU.

        Args:
            nsu: Número Sequencial Único retornado na emissão
            cnpj: CNPJ do contribuinte

        Returns:
            Dict com dados da NFS-e

        """
        return consultar_dfe_nsu(
            nsu=nsu,
            cnpj_consulta=cnpj,
            ambiente=self.ambiente,
            pfx_path=self.pfx_path,
            pfx_bytes=self.pfx_bytes,
            senha_pfx=self.senha_pfx,
        )

    def testar_conexao(self) -> dict[str, Any]:
        """Testa o mTLS no host da Sefin Nacional, onde a DPS é emitida."""
        import requests as req

        url = SEFIN_NFSE_URLS.get(self.ambiente)
        cert_path = None
        key_path = None

        try:
            from .transport import _limpar_temp, _preparar_cert_mtls

            cert_path, key_path = _preparar_cert_mtls(
                self.pfx_path, self.pfx_bytes, self.senha_pfx,
            )

            # Tentar acessar o endpoint (GET sem body retorna 405 ou similar, mas valida TLS)
            response = req.get(
                url,
                cert=(cert_path, key_path),
                timeout=15,
                verify=True,
                headers={"User-Agent": "LWK-Sistemas/1.0 (teste)"},
            )

            # Qualquer resposta HTTP (mesmo 405) indica que o mTLS funcionou
            if response.status_code < 500:
                return {
                    "success": True,
                    "message": f"Conexão mTLS OK (HTTP {response.status_code}). "
                               f"Ambiente: {self.ambiente}. Endpoint: {url}",
                    "status_code": response.status_code,
                }
            return {
                "success": False,
                "detail": f"Servidor retornou HTTP {response.status_code}",
            }

        except req.exceptions.SSLError as e:
            return {
                "success": False,
                "detail": f"Erro SSL/mTLS: certificado pode estar inválido ou expirado. {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "detail": f"Erro ao testar conexão: {e}",
            }
        finally:
            if cert_path or key_path:
                from .transport import _limpar_temp
                _limpar_temp(cert_path, key_path, self.pfx_path)

    @staticmethod
    def _extrair_erros(data) -> list:
        """Extrai lista de erros de uma resposta."""
        if not data:
            return []
        if isinstance(data, dict):
            return data.get("Erros", []) or data.get("errors", []) or []
        return []

    @staticmethod
    def _formatar_erros(erros: list) -> str:
        """Formata lista de erros em string legível."""
        if not erros:
            return ""
        msgs = []
        for e in erros:
            if isinstance(e, dict):
                codigo = e.get("Codigo", "")
                desc = e.get("Descricao", "")
                compl = e.get("Complemento", "")
                msg = f"[{codigo}] {desc}"
                if compl:
                    msg += f" ({compl})"
                msgs.append(msg)
            else:
                msgs.append(str(e))
        return "; ".join(msgs)
