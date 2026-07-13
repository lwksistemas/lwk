"""Organiza a árvore de pastas no Cloudinary sob lwksistemas.

Estrutura alvo:
  lwksistemas/producao/superadmin/{homepage,login}
  lwksistemas/producao/suporte/login
  lwksistemas/producao/{cpf_cnpj}/login
  lwksistemas/beta/... (igual)

Uso:
  python manage.py organizar_pastas_cloudinary           # simula
  python manage.py organizar_pastas_cloudinary --confirm # aplica
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from core.cloudinary_folders import ROOT, ensure_cloudinary_folders


def _configure_sdk() -> bool:
    from core.cloudinary_upload_preset import _configure_cloudinary_sdk

    return _configure_cloudinary_sdk()


def _subfolder_paths(parent: str) -> list[str]:
    import cloudinary.api

    try:
        result = cloudinary.api.subfolders(parent)
    except Exception:
        return []
    paths: list[str] = []
    for item in result.get("folders", []):
        if item.get("path"):
            paths.append(item["path"])
        elif item.get("name"):
            paths.append(f'{parent}/{item["name"]}')
    return paths


def _delete_folder_tree(path: str) -> None:
    import cloudinary.api

    for child in _subfolder_paths(path):
        _delete_folder_tree(child)
    try:
        cloudinary.api.delete_folder(path)
    except Exception as exc:
        raise RuntimeError(f"{path}: {exc}") from exc


def _target_skeleton() -> list[str]:
    skeleton = []
    for env in ("producao", "beta"):
        skeleton.extend([
            f"{ROOT}/{env}",
            f"{ROOT}/{env}/superadmin",
            f"{ROOT}/{env}/superadmin/homepage",
            f"{ROOT}/{env}/superadmin/login",
            f"{ROOT}/{env}/suporte",
            f"{ROOT}/{env}/suporte/login",
        ])
    return skeleton


def _legacy_roots_under_lwksistemas() -> list[str]:
    """Pastas na raiz de lwksistemas que não são producao/beta."""
    allowed = {"producao", "beta"}
    legacy = []
    for name in _subfolder_paths(ROOT):
        leaf = name.split("/")[-1]
        if leaf not in allowed:
            legacy.append(name)
    return legacy


def _legacy_inside_producao() -> list[str]:
    allowed = {"superadmin", "suporte"}
    legacy = []
    for name in _subfolder_paths(f"{ROOT}/producao"):
        leaf = name.split("/")[-1]
        if leaf not in allowed:
            legacy.append(name)
    return legacy


class Command(BaseCommand):
    help = "Cria pastas producao/beta e remove pastas legadas vazias em lwksistemas."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Executa alterações.")

    def handle(self, *args, **options):
        confirm = options["confirm"]
        if not _configure_sdk():
            self.stdout.write(self.style.ERROR("Cloudinary não configurado."))
            return

        skeleton = _target_skeleton()
        legacy = _legacy_roots_under_lwksistemas() + _legacy_inside_producao()

        self.stdout.write("Pastas alvo a criar:")
        for p in skeleton:
            self.stdout.write(f"  + {p}")

        self.stdout.write("Pastas legadas a remover (devem estar vazias):")
        if legacy:
            for p in legacy:
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("  (nenhuma)")

        if not confirm:
            self.stdout.write(self.style.WARNING("Simulação. Use --confirm para aplicar."))
            return

        ensure_cloudinary_folders(skeleton)
        self.stdout.write(self.style.SUCCESS("Estrutura alvo criada/verificada."))

        errors = 0
        for path in sorted(legacy, key=len, reverse=True):
            try:
                _delete_folder_tree(path)
                self.stdout.write(self.style.SUCCESS(f"Removida: {path}"))
            except Exception as exc:
                errors += 1
                self.stdout.write(self.style.ERROR(f"Falha {path}: {exc}"))

        if errors:
            self.stdout.write(self.style.WARNING(f"{errors} pasta(s) não removida(s) (podem ter arquivos)."))
        else:
            self.stdout.write(self.style.SUCCESS("Limpeza concluída."))

        self.stdout.write("Raiz lwksistemas agora:")
        for p in _subfolder_paths(ROOT):
            self.stdout.write(f"  {p}")
