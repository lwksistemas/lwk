"""API de upload/listagem de mídia — LWK Sistemas.

Estrutura em disco:
  /storage/{tenant}/{nome_cpf_paciente}/fotos|pdf/{arquivo}
  /storage/{tenant}/{fotos|docs|...}/{nome_cpf_paciente}/{arquivo}  (legado)
  /storage/{cpf_cnpj}_{nome-empresa}/dicom|docs/{cpf_paciente}/{arquivo}

Endpoints:
  POST   /upload/<tenant>/
  DELETE /upload/<tenant>/<path:filename>            (arquivo; ou pasta vazia)
  DELETE /upload/<tenant>/<path:filename>?recursive=true  (pasta do paciente + conteúdo)
  DELETE /upload/<tenant>/?recursive=true            (loja inteira: /storage/{tenant})
  GET    /list/
  GET    /list/<tenant>/
  GET    /list/<tenant>/<path:folder>/
  GET    /health
"""
import hashlib
import hmac
import os
import re
import shutil
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from flask import Flask, jsonify, request

app = Flask(__name__)
STORAGE_ROOT = Path(os.environ.get("MEDIA_STORAGE_ROOT", "/storage"))
API_TOKEN = os.environ.get("MEDIA_API_TOKEN", "")
# 0 = links antigos sem ?e=&s= continuam válidos (WhatsApp/backup). 1 = exige assinatura.
REQUIRE_SIGNED = os.environ.get("MEDIA_REQUIRE_SIGNED", "0").lower() in ("1", "true", "yes")
SYSTEM_TENANTS = frozenset({"superadmin", "suporte"})
TENANT_RE = re.compile(
    r"^(?:\d{11}|\d{14}|superadmin|suporte|\d{11,14}_[a-z0-9][a-z0-9_-]{0,80})$"
)
ALLOWED_FOLDERS = ("fotos", "docs", "pdf", "avatars", "recibos", "contratos", "dicom")
PASTAS_LOJA = frozenset({"admin", "loja"})
# pasta raiz, tipo/paciente (legado) ou paciente/tipo (fotos|pdf)
FOLDER_PATH_RE = re.compile(
    r"^[a-z0-9][a-z0-9_./-]{0,200}$"
)
MAX_FILES_PER_FOLDER = 500
_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})
_PDF_EXTS = frozenset({".pdf"})
_DICOM_EXTS = frozenset({".dcm", ".dicom"})


def _bearer_token() -> str:
    auth = request.headers.get("Authorization", "")
    return auth.replace("Bearer ", "").strip()


def token_for_tenant(tenant: str) -> str:
    return hmac.new(
        API_TOKEN.encode("utf-8"),
        tenant.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_token(tenant: str | None = None) -> bool:
    """Master libera tudo. Token HMAC da loja só vale para aquele tenant."""
    if not API_TOKEN:
        return False
    token = _bearer_token()
    if not token:
        return False
    if hmac.compare_digest(token, API_TOKEN):
        return True
    if tenant and hmac.compare_digest(token, token_for_tenant(tenant)):
        return True
    return False


def _assinatura_path(path: str, exp: int) -> str:
    msg = f"{path}\n{exp}".encode("utf-8")
    return hmac.new(API_TOKEN.encode("utf-8"), msg, hashlib.sha256).hexdigest()[:32]


def _verify_file_sig(path: str, exp: str, sig: str) -> bool:
    if not API_TOKEN or not path or not exp or not sig:
        return False
    try:
        exp_i = int(exp)
    except (TypeError, ValueError):
        return False
    if exp_i < int(time.time()) or len(sig) != 32:
        return False
    esperado = _assinatura_path(path, exp_i)
    return hmac.compare_digest(esperado, sig)


def folder_structure_ok(folder_path: str) -> bool:
    """Aceita tipo, admin/tipo, paciente/fotos|pdf, legado tipo/paciente ou dicom/cpf."""
    parts = [p for p in (folder_path or "").split("/") if p]
    if not parts or any(".." in p for p in parts):
        return False
    if len(parts) == 1:
        return parts[0] in ALLOWED_FOLDERS
    if len(parts) == 2:
        a, b = parts
        if a in PASTAS_LOJA and b in ALLOWED_FOLDERS:
            return True
        if b in ("fotos", "pdf"):
            return True
        if a in ALLOWED_FOLDERS:
            return True
    return False


def _ext_permitida(folder_path: str, ext: str) -> bool:
    last = (folder_path or "").rstrip("/").split("/")[-1]
    if last in ("fotos", "avatars"):
        return ext in _IMAGE_EXTS
    if last in ("pdf", "docs", "recibos", "contratos"):
        return ext in _PDF_EXTS
    if last == "dicom":
        return ext in _DICOM_EXTS or ext in _IMAGE_EXTS
    return ext in _IMAGE_EXTS | _PDF_EXTS


def normalize_tenant(raw: str) -> str | None:
    value = (raw or "").strip()
    if value in SYSTEM_TENANTS:
        return value
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) in (11, 14) and "_" not in value:
        return digits
    if re.fullmatch(r"\d{11,14}_[a-z0-9][a-z0-9_-]{0,80}", value):
        return value
    return None


def normalize_folder_path(raw: str) -> str | None:
    value = (raw or "").strip().strip("/")
    if not value or ".." in value:
        return None
    if not FOLDER_PATH_RE.fullmatch(value):
        return None
    return value


def _safe_under_storage(path: Path) -> bool:
    try:
        path.resolve().relative_to(STORAGE_ROOT.resolve())
        return True
    except (ValueError, OSError):
        return False


@app.route("/upload/<tenant>/", methods=["POST"])
def upload(tenant):
    tenant_key = normalize_tenant(tenant)
    if not verify_token(tenant_key):
        return jsonify({"error": "Unauthorized"}), 401
    if not tenant_key:
        return jsonify({"error": "Tenant inválido (CPF/CNPJ, superadmin ou suporte)"}), 400

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    folder_path = normalize_folder_path(request.form.get("folder", "fotos"))
    if not folder_path or not folder_structure_ok(folder_path):
        return jsonify({"error": "Pasta inválida"}), 400

    dest_dir = STORAGE_ROOT / tenant_key / Path(folder_path)
    if not _safe_under_storage(dest_dir):
        return jsonify({"error": "Pasta inválida"}), 400
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() or ".jpg"
    if not _ext_permitida(folder_path, ext):
        return jsonify({"error": "Tipo de arquivo não permitido nesta pasta"}), 400
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = dest_dir / filename
    file.save(str(filepath))

    url = f"/files/{tenant_key}/{folder_path}/{filename}"
    return jsonify({
        "success": True,
        "url": url,
        "filename": filename,
        "tenant": tenant_key,
        "folder": folder_path,
        "size": os.path.getsize(str(filepath)),
    }), 201


@app.route("/upload/<tenant>/", methods=["DELETE"])
def delete_tenant_root(tenant):
    """Apaga toda a pasta de um tenant (loja) — exige recursive=true.

    Usado quando a loja é excluída no superadmin: remove /storage/{tenant} inteiro.
    """
    tenant_key = normalize_tenant(tenant)
    if not verify_token(tenant_key):
        return jsonify({"error": "Unauthorized"}), 401
    if not tenant_key:
        return jsonify({"error": "Tenant inválido"}), 400
    recursive = str(request.args.get("recursive", "")).lower() in ("1", "true", "yes")
    if not recursive:
        return jsonify({"error": "Exclusão da raiz do tenant exige recursive=true"}), 400
    base = STORAGE_ROOT / tenant_key
    if not base.exists():
        return jsonify({"success": True, "removed": None, "note": "já não existia"}), 200
    removed = _rmtree_seguro(base, tenant_key)
    if removed is None:
        return jsonify({"error": "Path inválido"}), 400
    return jsonify({"success": True, "removed": removed, "recursive": True}), 200


@app.route("/upload/<tenant>/<path:filename>", methods=["DELETE"])
def delete(tenant, filename):
    tenant_key = normalize_tenant(tenant)
    if not verify_token(tenant_key):
        return jsonify({"error": "Unauthorized"}), 401
    if not tenant_key:
        return jsonify({"error": "Tenant inválido"}), 400

    filepath = STORAGE_ROOT / tenant_key / filename
    if not _safe_under_storage(filepath):
        return jsonify({"error": "Path inválido"}), 400
    if filepath.exists() and filepath.is_file():
        filepath.unlink()
        return jsonify({"success": True}), 200
    if filepath.exists() and filepath.is_dir():
        recursive = str(request.args.get("recursive", "")).lower() in ("1", "true", "yes")
        if recursive:
            removed = _rmtree_seguro(filepath, tenant_key)
            if removed is None:
                return jsonify({"error": "Path inválido para exclusão recursiva"}), 400
            return jsonify({"success": True, "removed": removed, "recursive": True}), 200
        removed = _rmdir_vazio(filepath)
        if removed:
            return jsonify({"success": True, "removed": removed}), 200
        return jsonify({"error": "Pasta não está vazia"}), 409
    return jsonify({"error": "Arquivo não encontrado"}), 404


def _rmtree_seguro(path: Path, tenant_key: str) -> str | None:
    """Remove pasta e todo o conteúdo (recursivo). Retorna caminho relativo removido
    ou None se o alvo for inseguro.

    Salvaguardas: só dentro de /storage; nunca a raiz /storage; nunca a raiz do
    próprio tenant... exceto quando o alvo É a pasta raiz do tenant (usado para
    excluir toda a mídia de uma loja) — nesse caso exige que o path resolvido seja
    exatamente /storage/{tenant_key}.
    """
    if not _safe_under_storage(path) or not path.is_dir():
        return None
    resolved = path.resolve()
    storage = STORAGE_ROOT.resolve()
    if resolved == storage:
        return None  # nunca apagar a raiz /storage
    # o alvo tem que estar sob /storage/{tenant_key}
    tenant_root = (STORAGE_ROOT / tenant_key).resolve()
    if resolved != tenant_root and tenant_root not in resolved.parents:
        return None
    rel = str(resolved.relative_to(storage))
    try:
        shutil.rmtree(resolved)
    except OSError:
        return None
    return rel


def _rmdir_vazio(path: Path) -> list[str]:
    """Remove pasta só se não tiver arquivo. Apaga subpastas vazias de dentro para fora."""
    if not path.is_dir() or not _safe_under_storage(path):
        return []
    removed: list[str] = []
    for child in sorted(path.iterdir(), key=lambda p: len(str(p)), reverse=True):
        if child.is_dir():
            removed.extend(_rmdir_vazio(child))
        elif child.is_file():
            return []
    try:
        path.rmdir()
        removed.append(str(path.relative_to(STORAGE_ROOT)))
    except OSError:
        return removed
    return removed


@app.route("/list/", methods=["GET"])
def list_tenants():
    if not verify_token():
        return jsonify({"error": "Unauthorized"}), 401

    tenants = []
    if STORAGE_ROOT.exists():
        for d in sorted(STORAGE_ROOT.iterdir(), key=lambda p: p.name):
            if not d.is_dir() or d.name == "backups":
                continue
            if not TENANT_RE.match(d.name):
                continue
            folders = sorted(
                x.name for x in d.iterdir()
                if x.is_dir() and not x.name.startswith(".")
            )
            tenants.append({
                "tenant": d.name,
                "folders": folders,
                "folder_count": len(folders),
            })
    return jsonify({"tenants": tenants, "total": len(tenants)})


@app.route("/list/<tenant>/", methods=["GET"])
def list_folders(tenant):
    tenant_key = normalize_tenant(tenant)
    if not verify_token(tenant_key):
        return jsonify({"error": "Unauthorized"}), 401
    if not tenant_key:
        return jsonify({"error": "Tenant inválido"}), 400

    base = STORAGE_ROOT / tenant_key
    if not _safe_under_storage(base) or not base.is_dir():
        return jsonify({"tenant": tenant_key, "folders": []})

    folders = []
    for d in sorted(base.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or d.name.startswith("."):
            continue
        try:
            file_count = sum(1 for f in d.iterdir() if f.is_file())
            sub_count = sum(1 for f in d.iterdir() if f.is_dir())
        except OSError:
            file_count = 0
            sub_count = 0
        folders.append({
            "folder": d.name,
            "file_count": file_count,
            "subfolder_count": sub_count,
        })
    return jsonify({"tenant": tenant_key, "folders": folders})


@app.route("/list/<tenant>/<path:folder>/", methods=["GET"])
def list_files(tenant, folder):
    tenant_key = normalize_tenant(tenant)
    if not verify_token(tenant_key):
        return jsonify({"error": "Unauthorized"}), 401
    if not tenant_key:
        return jsonify({"error": "Tenant inválido"}), 400

    folder_path = normalize_folder_path(folder)
    if not folder_path:
        return jsonify({"error": "Pasta inválida"}), 400

    dest = STORAGE_ROOT / tenant_key / Path(folder_path)
    if not _safe_under_storage(dest) or not dest.is_dir():
        return jsonify({
            "tenant": tenant_key,
            "folder": folder_path,
            "files": [],
            "subfolders": [],
            "truncated": False,
        })

    files = []
    subfolders = []
    truncated = False
    try:
        children = list(dest.iterdir())
    except OSError:
        children = []

    dirs = sorted((c for c in children if c.is_dir()), key=lambda p: p.name)
    for d in dirs:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,100}", d.name):
            continue
        try:
            count = sum(1 for f in d.iterdir() if f.is_file())
        except OSError:
            count = 0
        subfolders.append({
            "name": d.name,
            "path": f"{folder_path}/{d.name}",
            "file_count": count,
        })

    file_entries = sorted(
        (c for c in children if c.is_file()),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    for f in file_entries:
        if len(files) >= MAX_FILES_PER_FOLDER:
            truncated = True
            break
        try:
            st = f.stat()
        except OSError:
            continue
        files.append({
            "filename": f.name,
            "size": st.st_size,
            "mtime": int(st.st_mtime),
            "url": f"/files/{tenant_key}/{folder_path}/{f.name}",
        })

    return jsonify({
        "tenant": tenant_key,
        "folder": folder_path,
        "files": files,
        "subfolders": subfolders,
        "truncated": truncated,
    })


@app.route("/auth-file", methods=["GET"])
def auth_file():
    """Usado pelo nginx auth_request em GET /files/.

    Sem assinatura: 200 se MEDIA_REQUIRE_SIGNED=0 (links antigos), 401 se =1.
    Com ?e=&s=: 200 só se HMAC e prazo forem válidos.
    """
    uri = request.headers.get("X-Original-URI") or ""
    if not uri:
        return "", 403
    parsed = urlparse(uri)
    path = parsed.path or ""
    if not path.startswith("/files/"):
        return "", 403
    qs = parse_qs(parsed.query)
    exp = (qs.get("e") or [""])[0]
    sig = (qs.get("s") or [""])[0]
    if not exp and not sig:
        return ("", 200) if not REQUIRE_SIGNED else ("", 401)
    if _verify_file_sig(path, exp, sig):
        return "", 200
    return "", 401


@app.route("/health", methods=["GET"])
def health():
    free_gb = os.statvfs("/storage").f_bavail * os.statvfs("/storage").f_frsize / (1024**3)
    tenants = len([d for d in STORAGE_ROOT.iterdir() if d.is_dir()]) if STORAGE_ROOT.exists() else 0
    return jsonify({"status": "ok", "free_gb": round(free_gb, 1), "tenants": tenants})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
