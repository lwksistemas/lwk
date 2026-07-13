"""
Remove mídias diretamente na pasta raiz lwksistemas/ (legado).

Não apaga subpastas (superadmin, suporte, lojas, etc.).

Uso:
    python manage.py limpar_cloudinary_raiz              # lista o que seria apagado
    python manage.py limpar_cloudinary_raiz --confirm    # exclui de fato
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from core.cloudinary_folders import ROOT


def _is_root_asset(public_id: str) -> bool:
    """True se o asset está em lwksistemas/arquivo (sem subpasta)."""
    prefix = f'{ROOT}/'
    if not public_id.startswith(prefix):
        return False
    rest = public_id[len(prefix):]
    return bool(rest) and '/' not in rest


def _configure_cloudinary():
    import cloudinary

    from superadmin.cloudinary_models import CloudinaryConfig

    cfg = CloudinaryConfig.get_config()
    if not cfg.enabled or not cfg.cloud_name or not cfg.api_key or not cfg.api_secret:
        raise RuntimeError(
            'Cloudinary não configurado (habilite em Superadmin → Homepage → Cloudinary).'
        )
    cloudinary.config(
        cloud_name=cfg.cloud_name,
        api_key=cfg.api_key,
        api_secret=cfg.api_secret,
        secure=True,
    )
    return cfg.cloud_name


def _list_root_assets():
    import cloudinary.api

    assets: list[dict] = []
    next_cursor = None
    while True:
        kwargs = {
            'type': 'upload',
            'prefix': f'{ROOT}/',
            'max_results': 500,
        }
        if next_cursor:
            kwargs['next_cursor'] = next_cursor
        result = cloudinary.api.resources(**kwargs)
        for item in result.get('resources', []):
            pid = (item.get('public_id') or '').strip()
            if _is_root_asset(pid):
                assets.append(item)
        next_cursor = result.get('next_cursor')
        if not next_cursor:
            break
    return assets


class Command(BaseCommand):
    help = 'Exclui mídias legadas na pasta raiz lwksistemas/ (sem subpastas).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Executa a exclusão (sem isso, apenas lista).',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']

        try:
            cloud_name = _configure_cloudinary()
        except RuntimeError as exc:
            self.stdout.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(f'Cloud: {cloud_name}')
        self.stdout.write(f'Buscando assets em {ROOT}/ (somente raiz, sem subpastas)...')

        try:
            assets = _list_root_assets()
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Erro ao listar Cloudinary: {exc}'))
            return

        if not assets:
            self.stdout.write(self.style.SUCCESS('Nenhum asset na pasta raiz.'))
            return

        self.stdout.write(f'Encontrados {len(assets)} asset(s) na raiz:')
        for item in assets[:20]:
            self.stdout.write(f"  - {item.get('public_id')} ({item.get('format')}, {item.get('bytes', 0)} bytes)")
        if len(assets) > 20:
            self.stdout.write(f'  ... e mais {len(assets) - 20}')

        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    'Modo simulação. Use --confirm para excluir.'
                )
            )
            return

        import cloudinary.api

        public_ids = [a['public_id'] for a in assets if a.get('public_id')]
        deleted = 0
        errors = 0
        batch_size = 100
        for i in range(0, len(public_ids), batch_size):
            batch = public_ids[i:i + batch_size]
            try:
                result = cloudinary.api.delete_resources(batch, resource_type='image')
                for pid, status in (result.get('deleted') or {}).items():
                    if status == 'deleted' or status == 'not found':
                        deleted += 1
                    else:
                        errors += 1
                        self.stdout.write(self.style.WARNING(f'  Falha: {pid} → {status}'))
            except Exception as exc:
                errors += len(batch)
                self.stdout.write(self.style.ERROR(f'Erro no lote: {exc}'))

        self.stdout.write(
            self.style.SUCCESS(f'Concluído: {deleted} excluído(s), {errors} erro(s).')
        )
