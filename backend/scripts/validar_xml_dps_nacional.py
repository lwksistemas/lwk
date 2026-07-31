"""Validação local do XML DPS/RTC enviado ao ISSNet padrão Nacional.

Não faz chamada ao webservice — apenas constrói o XML exatamente como o backend
faria e valida estrutura/namespace. Use para depurar rejeições de schema antes
de emitir em produção.
"""
import argparse
import logging
import sys
from decimal import Decimal
from pathlib import Path

# Adiciona backend ao path sem depender do manage.py
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from lxml import etree

from nfse_integration.issnet_nacional_xml_builder import construir_xml_enviar_lote_dps_sincrono
from nfse_integration.issnet_soap import (
    montar_soap_envelope_nacional_aninhado,
    montar_soap_envelope_nacional_cdata,
    montar_soap_envelope_nacional_xsd_string,
)
from nfse_integration.nacional.xml_signer import assinar_xml_enviar_lote_dps

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

NS_NFSE = "http://www.sped.fazenda.gov.br/nfse"
XSD_URL = "https://raw.githubusercontent.com/MirrorProjetoACBr/ACBr/master/Exemplos/ACBrDFe/Schemas/NFSe/PadraoNacional/1.01/schema_v101-ISSNet.xsd"
XSD_SIG_URL = "https://raw.githubusercontent.com/MirrorProjetoACBr/ACBr/master/Exemplos/ACBrDFe/Schemas/NFSe/PadraoNacional/1.01/xmldsig-core-schema.xsd"


def _check_required_tags(root: etree.Element) -> list[str]:
    """Verifica presença das tags obrigatórias do DPS/RTC."""
    required = [
        "infDPS",
        "prest",
        "toma",
        "serv",
        "valores",
        "DPS",
    ]
    missing = []
    for tag in required:
        found = root.find(f".//{{{NS_NFSE}}}{tag}")
        if found is None:
            missing.append(tag)
    return missing


def _check_namespace(root: etree.Element) -> str:
    """Retorna namespace do root ou aviso."""
    ns = etree.QName(root.tag).namespace
    return ns or "AVISO: root sem namespace"


def build_dps_xml(args) -> str:
    """Chama o builder real do backend com os parâmetros fornecidos."""
    tomador_endereco = {
        "logradouro": args.tomador_logradouro,
        "numero": args.tomador_numero,
        "bairro": args.tomador_bairro,
        "cidade": args.tomador_cidade,
        "uf": args.tomador_uf,
        "cep": args.tomador_cep,
        "codigo_municipio": args.tomador_codigo_municipio,
    }
    return construir_xml_enviar_lote_dps_sincrono(
        numero_lote=args.numero,
        prestador_cnpj=args.prestador_cnpj,
        prestador_inscricao_municipal=args.prestador_im,
        numero_dps=args.numero,
        serie_dps=args.serie,
        data_emissao=args.data_emissao,
        data_competencia=args.data_competencia,
        codigo_municipio_emissor=args.codigo_municipio_emissor,
        ambiente=args.ambiente,
        prestador_telefone=args.prestador_telefone,
        prestador_email=args.prestador_email,
        optante_simples_nacional=args.optante_simples,
        tomador_cpf_cnpj=args.tomador_cnpj,
        tomador_nome=args.tomador_nome,
        tomador_endereco=tomador_endereco,
        tomador_telefone=args.tomador_telefone,
        tomador_email=args.tomador_email,
        codigo_municipio_prestacao=args.tomador_codigo_municipio,
        codigo_tributacao_nacional=args.codigo_tributacao_nacional,
        codigo_tributacao_municipal=args.codigo_tributacao_municipal,
        descricao_servico=args.descricao,
        codigo_nbs=args.codigo_nbs,
        valor_servicos=Decimal(str(args.valor)),
        aliquota_iss=Decimal(str(args.aliquota)),
        indicador_operacao=args.indicador_operacao,
        ind_final_ibscbs=args.ind_final_ibscbs,
        ind_dest_ibscbs=args.ind_dest_ibscbs,
        cst_ibscbs=args.cst_ibscbs,
        cclass_trib_ibscbs=args.cclass_trib_ibscbs,
    )


def _download_schema(dest_dir: Path) -> Path:
    """Baixa o XSD principal e a dependência xmldsig para validação local."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    main_xsd = dest_dir / "schema_v101-ISSNet.xsd"
    sig_xsd = dest_dir / "xmldsig-core-schema.xsd"

    for url, path in [(XSD_URL, main_xsd), (XSD_SIG_URL, sig_xsd)]:
        if not path.exists():
            logger.info("Baixando %s ...", url)
            import urllib.request

            urllib.request.urlretrieve(url, str(path))
    return main_xsd


def validate_xsd(xml_str: str, xsd_path: Path | None) -> bool:
    """Valida o XML DPS contra um XSD local (se informado ou baixado automaticamente)."""
    if not xsd_path:
        xsd_path = _download_schema(Path(__file__).resolve().parent / "xsd")
    if not xsd_path.exists():
        logger.warning("⚠️ XSD não encontrado em %s", xsd_path)
        return False
    try:
        with open(xsd_path, "rb") as f:
            xsd_doc = etree.parse(f)
        schema = etree.XMLSchema(xsd_doc)
        xml_doc = etree.fromstring(xml_str.encode("utf-8"))
        schema.assertValid(xml_doc)
        logger.info("✅ XML validado contra XSD: %s", xsd_path)
        return True
    except etree.DocumentInvalid as e:
        logger.error("❌ Falha na validação XSD: %s", e)
    except Exception as e:
        logger.error("❌ Erro ao validar XSD: %s", e)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida XML DPS/RTC ISSNet Nacional")
    parser.add_argument("--prestador-cnpj", default="24758458000172")
    parser.add_argument("--prestador-im", default="")
    parser.add_argument("--numero", type=int, default=163)
    parser.add_argument("--serie", default="1")
    parser.add_argument("--data-emissao", default="2026-07-31T16:51:43")
    parser.add_argument("--data-competencia", default="2026-07-31")
    parser.add_argument("--codigo-municipio-emissor", default="3543402")
    parser.add_argument("--prestador-telefone", default="")
    parser.add_argument("--prestador-email", default="")
    parser.add_argument("--ambiente", type=int, default=1, choices=[1, 2])
    parser.add_argument("--tomador-cnpj", default="24758458000172")
    parser.add_argument("--tomador-nome", default="LWK SISTEMAS LTDA")
    parser.add_argument("--tomador-logradouro", default="Rua Exemplo")
    parser.add_argument("--tomador-numero", default="123")
    parser.add_argument("--tomador-bairro", default="Centro")
    parser.add_argument("--tomador-cidade", default="Ribeirão Preto")
    parser.add_argument("--tomador-uf", default="SP")
    parser.add_argument("--tomador-cep", default="14000000")
    parser.add_argument("--tomador-codigo-municipio", default="3543402")
    parser.add_argument("--tomador-telefone", default="")
    parser.add_argument("--tomador-email", default="")
    parser.add_argument("--codigo-tributacao-nacional", default="140100")
    parser.add_argument("--codigo-tributacao-municipal", default="")
    parser.add_argument("--descricao", default="Serviço prestado")
    parser.add_argument("--codigo-nbs", default="")
    parser.add_argument("--valor", default="10.00")
    parser.add_argument("--aliquota", default="0.00")
    parser.add_argument("--optante-simples", action="store_true", default=True)
    parser.add_argument("--indicador-operacao", default="050101", help="Código indicador da operação IBSCBS")
    parser.add_argument("--ind-final-ibscbs", default="0", choices=["0", "1"], help="Operação uso/consumo pessoal")
    parser.add_argument("--ind-dest-ibscbs", default="0", choices=["0", "1"], help="Destinatário = tomador")
    parser.add_argument("--cst-ibscbs", default="000", help="CST IBS/CBS")
    parser.add_argument("--cclass-trib-ibscbs", default="000001", help="Classificação tributária IBS/CBS")
    parser.add_argument("--xsd", type=Path, help="Caminho para o XSD local do DPS (opcional)")
    parser.add_argument("--pfx", type=Path, help="PFX do prestador para testar assinatura local")
    parser.add_argument("--senha-pfx", default="", help="Senha do PFX para teste de assinatura")
    parser.add_argument("--mostrar-xml", action="store_true", help="Imprime o XML DPS e envelopes SOAP")
    parser.add_argument("--salvar", type=Path, help="Salva XML DPS no caminho informado")
    args = parser.parse_args()

    from datetime import datetime

    try:
        args.data_emissao = datetime.fromisoformat(args.data_emissao)
        args.data_competencia = datetime.fromisoformat(args.data_competencia)
    except ValueError:
        logger.error("Formato de data inválido. Use ISO 8601, ex: 2026-07-31T16:51:43")
        return 1

    logger.info("Construindo XML DPS Nacional com parâmetros fornecidos...")
    xml_dps = build_dps_xml(args)

    # Parse e validações estruturais
    try:
        root = etree.fromstring(xml_dps.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        logger.error("❌ XML gerado é sintaticamente inválido: %s", e)
        return 1

    ns = _check_namespace(root)
    logger.info("Namespace do root: %s", ns)
    if ns != NS_NFSE:
        logger.error("❌ Namespace inesperado. Esperado %s", NS_NFSE)
        return 1

    missing = _check_required_tags(root)
    if missing:
        logger.error("❌ Tags obrigatórias ausentes: %s", ", ".join(missing))
        return 1

    logger.info("✅ Estrutura mínima do DPS/RTC OK")

    # Envelopes SOAP que seriam enviados
    envelopes = {
        "xsd_string": montar_soap_envelope_nacional_xsd_string("RecepcionarLoteDpsSincrono", xml_dps),
        "cdata": montar_soap_envelope_nacional_cdata("RecepcionarLoteDpsSincrono", xml_dps),
        "aninhado": montar_soap_envelope_nacional_aninhado("RecepcionarLoteDpsSincrono", xml_dps),
    }
    for label, env in envelopes.items():
        try:
            etree.fromstring(env.encode("utf-8"))
            logger.info("✅ Envelope SOAP '%s' parseável (%d bytes)", label, len(env.encode("utf-8")))
        except etree.XMLSyntaxError as e:
            logger.error("❌ Envelope SOAP '%s' inválido: %s", label, e)
            return 1

    # XSD opcional
    if args.xsd:
        validate_xsd(xml_dps, args.xsd)
    else:
        logger.info("ℹ️ XSD não informado — validação estrutural apenas. Baixe o XSD em %s", XSD_URL)

    if args.pfx:
        if not args.pfx.exists():
            logger.error("❌ PFX não encontrado: %s", args.pfx)
            return 1
        try:
            signed_xml = assinar_xml_enviar_lote_dps(xml_dps, str(args.pfx), args.senha_pfx)
            logger.info("✅ XML assinado localmente com sucesso")
            root_signed = etree.fromstring(signed_xml.encode("utf-8"))
            ns_sig = "http://www.w3.org/2000/09/xmldsig#"
            sig_count = len(root_signed.findall(f".//{{{ns_sig}}}Signature"))
            cert_count = len(root_signed.findall(f".//{{{ns_sig}}}X509Certificate"))
            logger.info("ℹ️ Assinaturas no XML: %d | Certificados X509: %d", sig_count, cert_count)
            import xmlsec

            root_signed = etree.fromstring(signed_xml.encode("utf-8"))
            for idx, sig_node in enumerate(root_signed.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")):
                ctx = xmlsec.SignatureContext()
                try:
                    ctx.verify(sig_node)
                    logger.info("✅ Assinatura %d validada localmente", idx + 1)
                except Exception as e:
                    logger.error("❌ Assinatura %d FALHOU na validação local: %s", idx + 1, e)
        except Exception as e:
            logger.error("❌ Falha ao assinar/verificar localmente: %s", e)
            return 1

    if args.mostrar_xml:
        print("\n--- XML DPS ---\n")
        print(xml_dps)
        for label, env in envelopes.items():
            print(f"\n--- SOAP {label} ---\n")
            print(env)

    if args.salvar:
        args.salvar.write_text(xml_dps, encoding="utf-8")
        logger.info("XML DPS salvo em: %s", args.salvar)

    return 0


if __name__ == "__main__":
    sys.exit(main())
