"""API de upload/listagem de mídia — LWK Sistemas.

Estrutura em disco:
  /storage/{tenant}/{nome_cpf_paciente}/fotos|pdf/{arquivo}
  /storage/{tenant}/{fotos|docs|...}/{nome_cpf_paciente}/{arquivo}  (legado)
  /storage/{cpf_cnpj}_{nome-empresa}/dicom|docs/{cpf_paciente}/{arquivo}

Endpoints:
  POST   /upload/<tenant>/
  DELETE /upload/<tenant>/<path:filename>
  GET    /list/
  GET    /list/<tenant>/
  GET    /list/<tenant>/<path:folder>/
  GET    /health
"""
import hmac
import os
import re
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
STORAGE_ROOT = Path("/storage")
API_TOKEN = os.environ.get("MEDIA_API_TOKEN", "")
SYSTEM_TENANTS = frozenset({"superadmin", "suporte"})
TENANT_RE = re.compile(
    r"^(?:\d{11}|\d{14}|superadmin|suporte|\d{11,14}_[a-z0-9][a-z0-9_-]{0,80})$"
)
ALLOWED_FOLDERS = ("fotos", "docs", "pdf", "avatars", "recibos", "contratos", "dicom")
# pasta raiz, tipo/paciente (legado) ou paciente/tipo (fotos|pdf)
FOLDER_PATH_RE = re.compile(
    r"^[a-z0-9][a-z0-9_./-]{0,200}$"
)
MAX_FILES_PER_FOLDER = 500


def verify_token():
    if not API_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        return False
    return hmac.compare_digest(token, API_TOKEN)


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
    if not verify_token():
        return jsonify({"error": "Unauthorized"}), 401

    tenant_key = normalize_tenant(tenant)
    if not tenant_key:
        return jsonify({"error": "Tenant inválido (CPF/CNPJ, superadmin ou suporte)"}), 400

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    folder_path = normalize_folder_path(request.form.get("folder", "fotos"))
    if not folder_path:
        folder_path = "fotos"

    dest_dir = STORAGE_ROOT / tenant_key / Path(folder_path)
    if not _safe_under_storage(dest_dir):
        return jsonify({"error": "Pasta inválida"}), 400
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() or ".jpg"
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


@app.route("/upload/<tenant>/<path:filename>", methods=["DELETE"])
def delete(tenant, filename):
    if not verify_token():
        return jsonify({"error": "Unauthorized"}), 401

    tenant_key = normalize_tenant(tenant)
    if not tenant_key:
        return jsonify({"error": "Tenant inválido"}), 400

    filepath = STORAGE_ROOT / tenant_key / filename
    if not _safe_under_storage(filepath):
        return jsonify({"error": "Path inválido"}), 400
    if filepath.exists() and filepath.is_file():
        filepath.unlink()
        return jsonify({"success": True}), 200
    if filepath.exists() and filepath.is_dir():
        removed = _rmdir_vazio(filepath)
        if removed:
            return jsonify({"success": True, "removed": removed}), 200
        return jsonify({"error": "Pasta não está vazia"}), 409
    return jsonify({"error": "Arquivo não encontrado"}), 404


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
    if not verify_token():
        return jsonify({"error": "Unauthorized"}), 401

    tenant_key = normalize_tenant(tenant)
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
    if not verify_token():
        return jsonify({"error": "Unauthorized"}), 401

    tenant_key = normalize_tenant(tenant)
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


@app.route("/health", methods=["GET"])
def health():
    free_gb = os.statvfs("/storage").f_bavail * os.statvfs("/storage").f_frsize / (1024**3)
    tenants = len([d for d in STORAGE_ROOT.iterdir() if d.is_dir()]) if STORAGE_ROOT.exists() else 0
    return jsonify({"status": "ok", "free_gb": round(free_gb, 1), "tenants": tenants})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
