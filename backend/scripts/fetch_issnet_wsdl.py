#!/usr/bin/env python3
"""Baixa o WSDL do ISSNet Nacional usando certificado .pfx (mTLS).

Uso:
    python scripts/fetch_issnet_wsdl.py --pfx /caminho/cert.pfx --senha SENHA [--homologacao]

O WSDL salvo em issnet_nacional.wsdl pode ser usado para inspecionar o schema
correto de cabeçalho, DPS e operações SOAP esperadas pelo endpoint.
"""
import argparse
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nfse_integration.issnet_cert import certificado_mtls_temporario  # noqa: E402

URL_PRODUCAO = "https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx?wsdl"
URL_HOMOLOGACAO = URL_PRODUCAO  # Nacional não tem homologação separada na ISSNet


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixa WSDL ISSNet Nacional via mTLS")
    parser.add_argument("--pfx", required=True, help="Caminho do certificado .pfx/.p12")
    parser.add_argument("--senha", required=True, help="Senha do certificado")
    parser.add_argument("--homologacao", action="store_true", help="Usar endpoint de homologação")
    parser.add_argument("--saida", default="issnet_nacional.wsdl", help="Arquivo de saída")
    args = parser.parse_args()

    url = URL_HOMOLOGACAO if args.homologacao else URL_PRODUCAO
    pfx_path = Path(args.pfx)
    if not pfx_path.is_file():
        print(f"ERRO: certificado não encontrado: {pfx_path}", file=sys.stderr)
        return 1

    print(f"Buscando WSDL em {url} usando {pfx_path} ...")
    try:
        with certificado_mtls_temporario(str(pfx_path), args.senha) as (cert_pem, key_pem):
            resp = requests.get(url, cert=(cert_pem, key_pem), timeout=(10, 60), verify=True)
        print(f"HTTP {resp.status_code} ({len(resp.content)} bytes)")
        if resp.status_code == 200:
            with open(args.saida, "wb") as f:
                f.write(resp.content)
            print(f"Salvo em: {Path(args.saida).resolve()}")
            return 0
        print(resp.text[:2000], file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
