"""Exporta / importa SuperadminNFSeConfig entre ambientes (ex.: produção → beta).

Uso:
  # Na produção (Railway SSH ou local com DB prod)
  python manage.py nfse_config_sync export --output /tmp/nfse_config.json

  # No beta/staging
  python manage.py nfse_config_sync import --input /tmp/nfse_config.json

  # Importar sem sobrescrever contadores de RPS/DPS (recomendado se beta emite notas reais em paralelo)
  python manage.py nfse_config_sync import --input /tmp/nfse_config.json --keep-counters

O JSON contém senhas em texto claro — trate como secreto e apague após importar.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.encryption import decrypt_value, encrypt_value


def _serialize_config(config) -> dict:
    def dec(field: str) -> str:
        raw = getattr(config, field, "") or ""
        if not raw:
            return ""
        try:
            return decrypt_value(raw) or raw
        except Exception:
            return raw

    data = {
        "provedor_nfse": config.provedor_nfse,
        "emitir_automaticamente": config.emitir_automaticamente,
        "prestador_cnpj": config.prestador_cnpj or "",
        "prestador_razao_social": config.prestador_razao_social or "",
        "prestador_inscricao_municipal": config.prestador_inscricao_municipal or "",
        "prestador_email": config.prestador_email or "",
        "regime_especial_tributacao": config.regime_especial_tributacao or "",
        "codigo_servico_municipal": config.codigo_servico_municipal or "",
        "item_lista_servico": getattr(config, "item_lista_servico", "") or "",
        "codigo_tributacao_municipio": getattr(config, "codigo_tributacao_municipio", "") or "",
        "descricao_servico_padrao": config.descricao_servico_padrao or "",
        "aliquota_iss": str(config.aliquota_iss),
        "codigo_cnae": config.codigo_cnae or "",
        "optante_simples_nacional": config.optante_simples_nacional,
        "incentivador_cultural": config.incentivador_cultural,
        "issnet_usuario": dec("issnet_usuario"),
        "issnet_senha": dec("issnet_senha"),
        "issnet_senha_certificado": dec("issnet_senha_certificado"),
        "issnet_certificado_nome": config.issnet_certificado_nome or "",
        "issnet_certificado_b64": (
            base64.b64encode(bytes(config.issnet_certificado)).decode("ascii")
            if config.issnet_certificado
            else ""
        ),
        "serie_rps": config.serie_rps or "E",
        "ultimo_rps": config.ultimo_rps,
        "nacional_certificado_nome": config.nacional_certificado_nome or "",
        "nacional_senha_certificado": dec("nacional_senha_certificado"),
        "nacional_certificado_b64": (
            base64.b64encode(bytes(config.nacional_certificado)).decode("ascii")
            if config.nacional_certificado
            else ""
        ),
        "nacional_ambiente": config.nacional_ambiente or "homologacao",
        "nacional_codigo_municipio": config.nacional_codigo_municipio or "",
        "nacional_serie_dps": config.nacional_serie_dps or "1",
        "nacional_ultimo_dps": config.nacional_ultimo_dps,
    }
    return data


def _apply_config(config, data: dict, *, keep_counters: bool) -> None:
    scalar_fields = [
        "provedor_nfse", "emitir_automaticamente", "prestador_cnpj", "prestador_razao_social",
        "prestador_inscricao_municipal", "prestador_email", "regime_especial_tributacao",
        "codigo_servico_municipal", "item_lista_servico", "codigo_tributacao_municipio",
        "descricao_servico_padrao", "codigo_cnae", "optante_simples_nacional",
        "incentivador_cultural", "issnet_certificado_nome", "serie_rps",
        "nacional_certificado_nome", "nacional_ambiente", "nacional_codigo_municipio",
        "nacional_serie_dps",
    ]
    for field in scalar_fields:
        if field in data:
            setattr(config, field, data[field])

    if "aliquota_iss" in data:
        config.aliquota_iss = data["aliquota_iss"]

    if not keep_counters:
        if "ultimo_rps" in data:
            config.ultimo_rps = data["ultimo_rps"]
        if "nacional_ultimo_dps" in data:
            config.nacional_ultimo_dps = data["nacional_ultimo_dps"]

    for plain_field, enc_field in (
        ("issnet_usuario", "issnet_usuario"),
        ("issnet_senha", "issnet_senha"),
        ("issnet_senha_certificado", "issnet_senha_certificado"),
        ("nacional_senha_certificado", "nacional_senha_certificado"),
    ):
        value = (data.get(plain_field) or "").strip()
        if value:
            setattr(config, enc_field, encrypt_value(value))

    cert_b64 = (data.get("issnet_certificado_b64") or "").strip()
    if cert_b64:
        config.issnet_certificado = base64.b64decode(cert_b64)

    nac_b64 = (data.get("nacional_certificado_b64") or "").strip()
    if nac_b64:
        config.nacional_certificado = base64.b64decode(nac_b64)

    config.save()


class Command(BaseCommand):
    help = "Exporta ou importa configuração NFS-e superadmin entre ambientes"

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="action", required=True)

        export_p = sub.add_parser("export", help="Exporta config para JSON")
        export_p.add_argument("--output", "-o", required=True, help="Arquivo JSON de saída")

        import_p = sub.add_parser("import", help="Importa config de JSON")
        import_p.add_argument("--input", "-i", required=True, help="Arquivo JSON de entrada")
        import_p.add_argument(
            "--keep-counters",
            action="store_true",
            help="Não sobrescreve ultimo_rps / nacional_ultimo_dps no destino",
        )

    def handle(self, *args, **options):
        action = options["action"]
        if action == "export":
            self._export(options["output"])
        elif action == "import":
            self._import(options["input"], keep_counters=options["keep_counters"])

    def _export(self, output_path: str) -> None:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig

        config = SuperadminNFSeConfig.get_config()
        payload = _serialize_config(config)
        path = Path(output_path)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Config NFS-e exportada: {path}"))
        self.stdout.write(self.style.WARNING("⚠️  Arquivo contém senhas — apague após importar no destino."))

    def _import(self, input_path: str, *, keep_counters: bool) -> None:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig

        path = Path(input_path)
        if not path.is_file():
            raise CommandError(f"Arquivo não encontrado: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        config = SuperadminNFSeConfig.get_config()
        _apply_config(config, data, keep_counters=keep_counters)
        self.stdout.write(self.style.SUCCESS("Config NFS-e importada com sucesso."))
        if keep_counters:
            self.stdout.write("Contadores RPS/DPS do ambiente destino foram preservados.")
        self.stdout.write(
            f"  provedor={config.provedor_nfse} | tributação={config.codigo_tributacao_municipio} "
            f"| item={config.item_lista_servico} | ultimo_rps={config.ultimo_rps}",
        )
