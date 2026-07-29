"""Importa pacientes a partir do Excel Relatorio de Clientes (sistema antigo).

Formato esperado (Harmonis / similares):
  linha 1 = titulo
  linha 2 = cabecalhos (ID, Nome, CPF, ...)
  linha 3+ = dados

Uso:
  python manage.py importar_pacientes_relatorio_xlsx \\
    --slug clinicaharmonis --arquivo /tmp/clientes.xlsx --dry-run

  python manage.py importar_pacientes_relatorio_xlsx \\
    --slug clinicaharmonis --arquivo /tmp/clientes.xlsx
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.db_config import ensure_loja_database_config
from core.phone_utils import formatar_telefone_brasileiro, limpar_telefone
from core.validators import formatar_cpf
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

HEADER_ALIASES = {
    "id": "id_antigo",
    "nome": "nome",
    "cpf": "cpf",
    "data de nascimento": "data_nascimento",
    "origem": "origem",
    "endereço": "endereco",
    "endereco": "endereco",
    "bairro": "bairro",
    "uf - cidade": "uf_cidade",
    "telefone": "telefone",
    "celular": "celular",
    "celular 2": "celular2",
    "e-mail": "email",
    "email": "email",
    "cep": "cep",
    "ticket médio por venda": "ticket_medio",
    "ticket medio por venda": "ticket_medio",
    "data de cadastro": "data_cadastro",
    "data últ. compra": "data_ult_compra",
    "data ult. compra": "data_ult_compra",
    "valor últ. compra": "valor_ult_compra",
    "valor ult. compra": "valor_ult_compra",
}


def _col_row(ref: str) -> tuple[int, int]:
    m = re.match(r"([A-Z]+)(\d+)", ref or "")
    if not m:
        return 0, 0
    col, row = m.group(1), int(m.group(2))
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n - 1, row - 1


def _cell_val(c, shared_strings: list[str]) -> str | None:
    t = c.attrib.get("t")
    if t == "inlineStr":
        return "".join(x.text or "" for x in c.findall(".//m:t", NS))
    if t == "s":
        v = c.find("m:v", NS)
        if v is not None and v.text is not None:
            try:
                return shared_strings[int(v.text)]
            except (ValueError, IndexError):
                return v.text
    v = c.find("m:v", NS)
    return v.text if v is not None else None


def ler_linhas_xlsx(path: Path) -> list[list[str | None]]:
    """Le a primeira planilha do XLSX via stdlib (sem openpyxl)."""
    with zipfile.ZipFile(path) as zf:
        ss: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                ss.append("".join(t.text or "" for t in si.findall(".//m:t", NS)))

        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        sheets = wb.findall("m:sheets/m:sheet", NS)
        if not sheets:
            raise CommandError("XLSX sem abas.")
        rid = sheets[0].attrib.get(f"{REL_NS}id")
        rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels_root:
            if rel.attrib.get("Id") == rid:
                target = rel.attrib.get("Target")
                break
        if not target:
            raise CommandError("Nao foi possivel localizar a planilha no XLSX.")
        sheet_path = target if target.startswith("xl/") else f"xl/{target.lstrip('/')}"
        sheet = ET.fromstring(zf.read(sheet_path))

    grid: dict[tuple[int, int], str | None] = {}
    max_r = max_c = 0
    for c in sheet.findall(".//m:c", NS):
        ref = c.attrib.get("r")
        if not ref:
            continue
        ci, ri = _col_row(ref)
        max_r = max(max_r, ri)
        max_c = max(max_c, ci)
        grid[(ri, ci)] = _cell_val(c, ss)

    rows: list[list[str | None]] = []
    for ri in range(max_r + 1):
        rows.append([grid.get((ri, ci)) for ci in range(max_c + 1)])
    return rows


def _norm_header(h: str | None) -> str:
    return re.sub(r"\s+", " ", (h or "").strip().lower())


def mapear_registros(rows: list[list[str | None]]) -> list[dict]:
    """Detecta linha de cabecalho e devolve dicts tipados."""
    header_idx = None
    mapping: dict[int, str] = {}
    for i, row in enumerate(rows[:5]):
        labels = [_norm_header(c) for c in row]
        if "nome" in labels and ("cpf" in labels or "celular" in labels or "telefone" in labels):
            header_idx = i
            for ci, lab in enumerate(labels):
                key = HEADER_ALIASES.get(lab)
                if key:
                    mapping[ci] = key
            break
    if header_idx is None or "nome" not in mapping.values():
        raise CommandError(
            "Cabecalho nao reconhecido. Esperado relatorio com coluna Nome "
            "(ex.: Relatorio de Clientes)."
        )

    out: list[dict] = []
    for row in rows[header_idx + 1 :]:
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        rec: dict[str, str] = {}
        for ci, key in mapping.items():
            raw = row[ci] if ci < len(row) else None
            rec[key] = str(raw).strip() if raw is not None else ""
        if rec.get("nome"):
            out.append(rec)
    return out


def parse_data_br(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue
    return None


def split_uf_cidade(value: str) -> tuple[str, str]:
    value = (value or "").strip()
    if not value or value in ("-", " - ", "--"):
        return "", ""
    if " - " in value:
        uf, cidade = value.split(" - ", 1)
        uf = uf.strip().upper()[:2]
        return (uf if len(uf) == 2 and uf.isalpha() else ""), cidade.strip()
    return "", value


def escolher_telefone(rec: dict) -> str:
    for key in ("celular", "telefone", "celular2"):
        dig = limpar_telefone(rec.get(key) or "")
        if len(dig) >= 10:
            return formatar_telefone_brasileiro(dig)[:20]
    dig = limpar_telefone(rec.get("celular") or rec.get("telefone") or rec.get("celular2") or "")
    return dig[:20] if dig else ""


def normalizar_cpf(value: str) -> str | None:
    dig = re.sub(r"\D", "", value or "")
    if len(dig) != 11:
        return None
    if dig == dig[0] * 11:
        return None
    return formatar_cpf(dig)


def montar_observacoes(rec: dict) -> str:
    parts = []
    if rec.get("id_antigo"):
        parts.append(f"ID antigo: {rec['id_antigo']}")
    if rec.get("origem") and rec["origem"] not in ("--", "-", "-Array-"):
        parts.append(f"Origem: {rec['origem']}")
    if rec.get("cep"):
        parts.append(f"CEP: {rec['cep']}")
    if rec.get("bairro"):
        parts.append(f"Bairro: {rec['bairro']}")
    if rec.get("data_cadastro"):
        parts.append(f"Cadastro antigo: {rec['data_cadastro']}")
    if rec.get("data_ult_compra"):
        parts.append(f"Ult. compra: {rec['data_ult_compra']}")
    if rec.get("valor_ult_compra") and rec["valor_ult_compra"] not in ("0,00", "0.00", "0"):
        parts.append(f"Valor ult. compra: {rec['valor_ult_compra']}")
    if rec.get("ticket_medio") and rec["ticket_medio"] not in ("0,00", "0.00", "0"):
        parts.append(f"Ticket medio: {rec['ticket_medio']}")
    return " | ".join(parts)


def chave_dedup(nome: str, telefone: str, cpf: str | None) -> str:
    if cpf:
        return f"cpf:{re.sub(r'\D', '', cpf)}"
    dig = limpar_telefone(telefone)
    return f"nome:{nome.upper().strip()}|tel:{dig}"


class Command(BaseCommand):
    help = "Importa pacientes do Excel Relatorio de Clientes (sistema antigo) para a clinica."

    def add_arguments(self, parser):
        parser.add_argument("--slug", required=True, help="Slug ou atalho da loja")
        parser.add_argument("--arquivo", required=True, help="Caminho do .xlsx")
        parser.add_argument("--dry-run", action="store_true", help="So simula, nao grava")
        parser.add_argument(
            "--incluir-diversos",
            action="store_true",
            help="Importa tambem 'Clientes Diversos'",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Atualiza paciente existente (preenche campos vazios)",
        )

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or "").strip()
        loja = Loja.objects.using("default").filter(slug__iexact=ident).first()
        if not loja:
            loja = Loja.objects.using("default").filter(atalho__iexact=ident).first()
        if not loja:
            raise CommandError(f'Loja nao encontrada para "{ident}".')
        return loja

    def handle(self, *args, **options):
        from clinica_beleza.models import Patient

        path = Path(options["arquivo"]).expanduser()
        if not path.is_file():
            raise CommandError(f"Arquivo nao encontrado: {path}")

        loja = self._resolver_loja(options["slug"])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f"Loja {loja.slug}: schema ainda nao criado.")

        db = loja.database_name
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError("Falha ao configurar DB da loja.")
        set_current_tenant_db(db)
        set_current_loja_id(loja.id)

        rows = ler_linhas_xlsx(path)
        registros = mapear_registros(rows)
        self.stdout.write(f"Loja {loja.slug} (id={loja.id}, db={db})")
        self.stdout.write(f"Registros no Excel (com nome): {len(registros)}")

        skip_diversos = not options["incluir_diversos"]
        dry = options["dry_run"]
        do_update = options["update"]

        criados = atualizados = pulados = erros = 0
        vistos: set[str] = set()
        amostra_erros: list[str] = []

        existentes_cpf = {
            re.sub(r"\D", "", p.cpf or ""): p
            for p in Patient.objects.filter(loja_id=loja.id, is_active=True)
            .exclude(cpf__isnull=True)
            .exclude(cpf="")
            if re.sub(r"\D", "", p.cpf or "")
        }
        existentes_nome_tel = {
            f"{(p.nome or '').upper().strip()}|{limpar_telefone(p.telefone)}": p
            for p in Patient.objects.filter(loja_id=loja.id, is_active=True)
        }

        def achar_existente(nome: str, telefone: str, cpf: str | None):
            if cpf:
                dig = re.sub(r"\D", "", cpf)
                if dig in existentes_cpf:
                    return existentes_cpf[dig]
            key = f"{nome.upper().strip()}|{limpar_telefone(telefone)}"
            return existentes_nome_tel.get(key)

        batch: list = []

        for rec in registros:
            nome = (rec.get("nome") or "").strip()
            if not nome:
                pulados += 1
                continue
            if skip_diversos and nome.lower().startswith("clientes diversos"):
                pulados += 1
                continue

            telefone = escolher_telefone(rec)
            cpf = normalizar_cpf(rec.get("cpf") or "")
            email_raw = (rec.get("email") or "").strip()
            email = email_raw if "@" in email_raw else None
            nasc = parse_data_br(rec.get("data_nascimento") or "")
            uf, cidade = split_uf_cidade(rec.get("uf_cidade") or "")
            endereco_parts = [rec.get("endereco") or "", rec.get("bairro") or ""]
            endereco = ", ".join(p for p in endereco_parts if p and p not in (",", "-")).strip(" ,")
            obs = montar_observacoes(rec)

            k = chave_dedup(nome, telefone, cpf)
            if k in vistos:
                pulados += 1
                continue
            vistos.add(k)

            existente = achar_existente(nome, telefone, cpf)
            try:
                if existente:
                    if not do_update:
                        pulados += 1
                        continue
                    changed = False
                    if not existente.telefone and telefone:
                        existente.telefone = telefone
                        changed = True
                    if not existente.cpf and cpf:
                        existente.cpf = cpf
                        changed = True
                    if not existente.email and email:
                        existente.email = email
                        changed = True
                    if not existente.data_nascimento and nasc:
                        existente.data_nascimento = nasc
                        changed = True
                    if not existente.endereco and endereco:
                        existente.endereco = endereco
                        changed = True
                    if not existente.cidade and cidade:
                        existente.cidade = cidade.upper()
                        changed = True
                    if not existente.estado and uf:
                        existente.estado = uf
                        changed = True
                    if obs and (not existente.observacoes or "ID antigo:" not in (existente.observacoes or "")):
                        existente.observacoes = (
                            f"{existente.observacoes} | {obs}".strip(" |")
                            if existente.observacoes
                            else obs
                        )
                        changed = True
                    if changed and not dry:
                        existente.save()
                    if changed:
                        atualizados += 1
                    else:
                        pulados += 1
                    continue

                patient = Patient(
                    loja_id=loja.id,
                    nome=nome.upper(),
                    telefone=telefone or "",
                    cpf=cpf,
                    email=email,
                    data_nascimento=nasc,
                    endereco=endereco or "",
                    cidade=(cidade or "").upper(),
                    estado=uf or "",
                    observacoes=obs or "",
                    is_active=True,
                    allow_whatsapp=True,
                )
                if dry:
                    criados += 1
                else:
                    batch.append(patient)
                    criados += 1
                    if len(batch) >= 200:
                        with transaction.atomic():
                            Patient.objects.bulk_create(batch)
                        for p in batch:
                            if p.cpf:
                                existentes_cpf[re.sub(r"\D", "", p.cpf)] = p
                            existentes_nome_tel[
                                f"{(p.nome or '').upper().strip()}|{limpar_telefone(p.telefone)}"
                            ] = p
                        batch = []
            except Exception as exc:  # noqa: BLE001
                erros += 1
                if len(amostra_erros) < 15:
                    amostra_erros.append(f"{nome}: {exc}")

        if not dry and batch:
            with transaction.atomic():
                Patient.objects.bulk_create(batch)

        modo = "DRY-RUN" if dry else "APLICADO"
        self.stdout.write(
            self.style.SUCCESS(
                f"[{modo}] criados={criados} atualizados={atualizados} "
                f"pulados={pulados} erros={erros}"
            )
        )
        total_agora = Patient.objects.filter(loja_id=loja.id, is_active=True).count()
        self.stdout.write(f"Pacientes ativos na loja agora: {total_agora}")
        for e in amostra_erros:
            self.stderr.write(self.style.WARNING(e))
