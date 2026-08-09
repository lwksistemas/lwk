"""Auditoria de prontidão para NFS-e Padrão Nacional (DPS/RTC) no Clínica Beleza.

Verifica configurações por loja/tenant:
- ClinicaBelezaNfseConfig com padrao_nacional/issnet_usar_padrao_nacional
- Inscrição municipal (IM)
- Códigos de tributação nacional/municipal
- Código do município nacional
- Certificado A1 configurado
- Provedor NFS-e compatível com nacional

Uso:
    python manage.py audit_dps_nacional [--csv /tmp/auditoria_dps.csv]
    python manage.py audit_dps_nacional --problemas
    python manage.py audit_dps_nacional --schema nome_schema
"""
from __future__ import annotations

import csv
import json
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Auditoria de prontidão para NFS-e Padrão Nacional (DPS/RTC)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            dest="csv",
            default=None,
            help="Caminho para salvar relatório CSV.",
        )
        parser.add_argument(
            "--json",
            dest="json",
            default=None,
            help="Caminho para salvar relatório JSON.",
        )
        parser.add_argument(
            "--schema",
            dest="schema",
            default=None,
            help="Auditar apenas um schema específico.",
        )
        parser.add_argument(
            "--problemas",
            action="store_true",
            default=False,
            help="Mostrar apenas lojas com pendências.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando auditoria DPS/RTC..."))

        if connection.vendor != "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "Este comando é destinado a ambientes PostgreSQL com schemas tenants."
                )
            )
            return

        schemas = [options["schema"]] if options["schema"] else self._get_tenant_schemas()

        resultados: list[dict[str, Any]] = []
        for schema in schemas:
            itens = self.auditar_schema(schema)
            resultados.extend(itens)

        if not resultados:
            self.stdout.write(self.style.WARNING("Nenhum dado de NFS-e encontrado."))
            return

        total = len(resultados)
        prontas = sum(1 for r in resultados if r["pronta_para_nacional"])
        self.stdout.write(f"Total auditado: {total}")
        self.stdout.write(f"Prontas para DPS/RTC: {prontas}")
        self.stdout.write(f"Pendentes: {total - prontas}")

        for r in resultados:
            if options["problemas"] and r["pronta_para_nacional"]:
                continue
            self.imprimir_resultado(r)

        if options["csv"]:
            self.salvar_csv(resultados, options["csv"])
        if options["json"]:
            self.salvar_json(resultados, options["json"])

    def _get_tenant_schemas(self) -> list[str]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN (
                    'public', 'information_schema', 'pg_catalog', 'pg_toast'
                )
                ORDER BY schema_name
                """
            )
            return [row[0] for row in cursor.fetchall()]

    def auditar_schema(self, schema: str) -> list[dict[str, Any]]:
        if not self._table_exists(schema, "clinica_beleza_clinicabelezanfseconfig"):
            return []

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO %s, public", [schema])

        loja = self._buscar_loja_do_schema(schema)
        if not loja:
            return []

        cfg = self._buscar_nfse_config(loja["id"])
        cert = self._buscar_certificado(loja["id"])
        problema = self._avaliar_prontidao(loja, cfg, cert)

        return [{
            "schema": schema,
            "loja_id": loja["id"],
            "loja_nome": loja["nome"],
            "loja_slug": loja["slug"],
            "cpf_cnpj": loja.get("cpf_cnpj", ""),
            "padrao_nacional_habilitado": cfg.get("padrao_nacional", False) if cfg else False,
            "issnet_usar_padrao_nacional": cfg.get("issnet_usar_padrao_nacional", False) if cfg else False,
            "provedor_nf": cfg.get("provedor_nf", "") if cfg else "",
            "im": cfg.get("im", "") if cfg else "",
            "codigo_tributacao_nacional": cfg.get("codigo_tributacao_nacional", "") if cfg else "",
            "codigo_tributacao_municipal": cfg.get("codigo_tributacao_municipal", "") if cfg else "",
            "nacional_codigo_municipio": cfg.get("nacional_codigo_municipio", "") if cfg else "",
            "certificado_configurado": bool(cert),
            "pronta_para_nacional": problema is None,
            "pendencias": problema or "",
        }]

    def _table_exists(self, schema: str, table_name: str) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                LIMIT 1
                """,
                [schema, table_name],
            )
            return cursor.fetchone() is not None

    def _buscar_loja_do_schema(self, schema: str) -> dict[str, Any] | None:
        """Resolve a loja dona do schema (database_name com hífen → underscore)."""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, nome, slug, cpf_cnpj, database_name
                    FROM public.superadmin_loja
                    WHERE is_active = true
                      AND replace(coalesce(database_name, ''), '-', '_') = %s
                    ORDER BY id
                    LIMIT 1
                    """,
                    [schema],
                )
                row = cursor.fetchone()
        except Exception:
            return None
        if not row:
            return None
        return {
            "id": row[0],
            "nome": row[1],
            "slug": row[2],
            "cpf_cnpj": row[3] or "",
            "database_name": row[4] or "",
        }

    def _buscar_lojas(self) -> list[dict[str, Any]]:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, nome, slug, cpf_cnpj
                    FROM public.superadmin_loja
                    WHERE is_active = true
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()
        except Exception:
            return []
        return [
            {"id": row[0], "nome": row[1], "slug": row[2], "cpf_cnpj": row[3] or ""}
            for row in rows
        ]

    def _buscar_nfse_config(self, loja_id: int) -> dict[str, Any] | None:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT padrao_nacional,
                           issnet_usar_padrao_nacional,
                           provedor_nf,
                           im,
                           codigo_tributacao_nacional,
                           codigo_tributacao_municipal,
                           nacional_codigo_municipio
                    FROM clinica_beleza_clinicabelezanfseconfig
                    WHERE loja_id = %s
                    LIMIT 1
                    """,
                    [loja_id],
                )
                row = cursor.fetchone()
        except Exception:
            return None

        if not row:
            return None
        return {
            "padrao_nacional": bool(row[0]),
            "issnet_usar_padrao_nacional": bool(row[1]),
            "provedor_nf": row[2] or "",
            "im": row[3] or "",
            "codigo_tributacao_nacional": row[4] or "",
            "codigo_tributacao_municipal": row[5] or "",
            "nacional_codigo_municipio": row[6] or "",
        }

    def _buscar_certificado(self, loja_id: int) -> dict[str, Any] | None:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = current_schema()
                      AND tablename LIKE '%certificado%'
                    """
                )
                tabelas = [row[0] for row in cursor.fetchall()]
        except Exception:
            return None

        for tabela in tabelas:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        SELECT id FROM {tabela}
                        WHERE loja_id = %s AND ativo = true
                        LIMIT 1
                        """,
                        [loja_id],
                    )
                    if cursor.fetchone():
                        return {"tabela": tabela}
            except Exception:
                continue
        return None

    def _avaliar_prontidao(
        self,
        loja: dict[str, Any],
        cfg: dict[str, Any] | None,
        cert: dict[str, Any] | None,
    ) -> str | None:
        pendentes = []
        if not cfg:
            return "Configuração NFS-e inexistente"

        if not cfg.get("padrao_nacional") and not cfg.get("issnet_usar_padrao_nacional"):
            pendentes.append("Padrão nacional não habilitado")

        provedor = (cfg.get("provedor_nf") or "").lower()
        if "nacional" not in provedor and "issnet" not in provedor:
            pendentes.append(f"Provedor '{cfg.get('provedor_nf')}' não compatível com DPS/RTC")

        if not (cfg.get("im") or "").strip():
            pendentes.append("Inscrição municipal (IM) ausente")

        if not (cfg.get("codigo_tributacao_nacional") or "").strip():
            pendentes.append("Código de tributação nacional ausente")

        if not (cfg.get("codigo_tributacao_municipal") or "").strip():
            pendentes.append("Código de tributação municipal ausente")

        if not (cfg.get("nacional_codigo_municipio") or "").strip():
            pendentes.append("Código município nacional ausente")

        if not cert:
            pendentes.append("Certificado A1 não configurado")

        if not (loja.get("cpf_cnpj") or "").strip():
            pendentes.append("Loja sem CPF/CNPJ")

        return "; ".join(pendentes) if pendentes else None

    def imprimir_resultado(self, r: dict[str, Any]):
        status = self.style.SUCCESS("OK") if r["pronta_para_nacional"] else self.style.ERROR("PENDENTE")
        self.stdout.write(
            f"{status} {r['schema']} | {r['loja_nome']} ({r['cpf_cnpj'] or 'sem CNPJ'})"
        )
        if r["pendencias"]:
            self.stdout.write(f"    -> {r['pendencias']}")

    def salvar_csv(self, resultados: list[dict[str, Any]], path: str):
        if not resultados:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
            writer.writeheader()
            writer.writerows(resultados)
        self.stdout.write(self.style.SUCCESS(f"CSV salvo em {path}"))

    def salvar_json(self, resultados: list[dict[str, Any]], path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"JSON salvo em {path}"))
