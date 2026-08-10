"""API de upload/listagem de mídia — LWK Sistemas.

Endpoints:
  POST   /upload/<tenant>/ — Upload (multipart)
  DELETE /upload/<tenant>/<path:filename> — Deletar
  GET    /list/ — Lista tenants (CPF/CNPJ/superadmin/suporte)
  GET    /list/<tenant>/ — Lista pastas do tenant
  GET    /list/<tenant>/<folder>/ — Lista arquivos
  GET    /health

Deploy: /opt/media-api no host media (201.23.87.251).
Token via env MEDIA_API_TOKEN (systemd).
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
TENANT_RE = re.compile(r"^(?:\d{11}|\d{14}|superadmin|suporte)$")
ALLOWED_FOLDERS = ("fotos", "docs", "avatars", "recibos", "contratos")
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
    if len(digits) in (11, 14):
        return digits
    return None


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

    subfolder = request.form.get("folder", "fotos")
    if subfolder not in ALLOWED_FOLDERS:
        subfolder = "fotos"

    dest_dir = STORAGE_ROOT / tenant_key / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = dest_dir / filename
    file.save(str(filepath))

    url = f"/files/{tenant_key}/{subfolder}/{filename}"
    return jsonify({
        "success": True,
        "url": url,
        "filename": filename,
        "tenant": tenant_key,
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
    return jsonify({"error": "Arquivo não encontrado"}), 404


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
                if x.is_dir() and x.name in ALLOWED_FOLDERS
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
        if not d.is_dir() or d.name not in ALLOWED_FOLDERS:
            continue
        try:
            file_count = sum(1 for f in d.iterdir() if f.is_file())
        except OSError:
            file_count = 0
        folders.append({
            "folder": d.name,
            "file_count": file_count,
        })
    return jsonify({"tenant": tenant_key, "folders": folders})


@app.route("/list/<tenant>/<folder>/", methods=["GET"])
def list_files(tenant, folder):
    if not verify_token():
        return jsonify({"error": "Unauthorized"}), 401

    tenant_key = normalize_tenant(tenant)
    if not tenant_key:
        return jsonify({"error": "Tenant inválido"}), 400
    if folder not in ALLOWED_FOLDERS:
        return jsonify({"error": "Pasta inválida"}), 400

    dest = STORAGE_ROOT / tenant_key / folder
    if not _safe_under_storage(dest) or not dest.is_dir():
        return jsonify({
            "tenant": tenant_key,
            "folder": folder,
            "files": [],
            "truncated": False,
        })

    files = []
    truncated = False
    try:
        entries = sorted(
            (f for f in dest.iterdir() if f.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        entries = []

    for f in entries:
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
            "url": f"/files/{tenant_key}/{folder}/{f.name}",
        })

    return jsonify({
        "tenant": tenant_key,
        "folder": folder,
        "files": files,
        "truncated": truncated,
    })


@app.route("/health", methods=["GET"])
def health():
    free_gb = os.statvfs("/storage").f_bavail * os.statvfs("/storage").f_frsize / (1024**3)
    tenants = len([d for d in STORAGE_ROOT.iterdir() if d.is_dir()]) if STORAGE_ROOT.exists() else 0
    return jsonify({"status": "ok", "free_gb": round(free_gb, 1), "tenants": tenants})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
