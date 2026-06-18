"""Configuração compartilhada do django-q (fila de tarefas)."""
from __future__ import annotations

from urllib.parse import urlparse


def parse_redis_url(redis_url: str) -> dict:
    """Converte REDIS_URL (redis:// ou rediss://) para dict do django-q."""
    parsed = urlparse(redis_url)
    db = 0
    if parsed.path and parsed.path != '/':
        try:
            db = int(parsed.path.lstrip('/'))
        except ValueError:
            db = 0
    cfg = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 6379,
        'db': db,
    }
    if parsed.password:
        cfg['password'] = parsed.password
    if parsed.scheme == 'rediss':
        cfg['ssl'] = True
    return cfg


def build_q_cluster(*, workers: int = 4, redis_url: str | None = None) -> dict:
    """
    Fila django-q: Redis quando disponível (produção), senão ORM (dev/test).
    """
    cluster = {
        'name': 'LWKSistemas',
        'workers': workers,
        'recycle': 500,
        'timeout': 300,
        'compress': True,
        'save_limit': 250,
        'queue_limit': 500,
        'cpu_affinity': 1,
        'label': 'Django Q',
        'catch_up': True,
        'sync': False,
        'ack_failures': True,
        'max_attempts': 3,
        'retry': 360,
    }
    if redis_url:
        cluster['redis'] = parse_redis_url(redis_url)
    else:
        cluster['redis'] = None
        cluster['orm'] = 'default'
    return cluster
