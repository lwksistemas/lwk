"""Inicialização opcional do Sentry (produção). Sem SENTRY_DSN = no-op."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def init_sentry() -> bool:
    """
    Configura Sentry quando SENTRY_DSN está definido.
    Retorna True se o SDK foi inicializado.
    """
    dsn = (os.environ.get('SENTRY_DSN') or '').strip()
    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning('SENTRY_DSN definido mas sentry-sdk não instalado — ignorando')
        return False

    environment = (
        os.environ.get('SENTRY_ENVIRONMENT')
        or os.environ.get('RAILWAY_ENVIRONMENT')
        or 'production'
    )
    traces_sample_rate = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.05'))
    profiles_sample_rate = float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0'))

    logging_integration = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[DjangoIntegration(), logging_integration],
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        send_default_pii=False,
        attach_stacktrace=True,
        release=os.environ.get('LWK_BUILD') or os.environ.get('SENTRY_RELEASE') or None,
    )
    logger.info('Sentry inicializado (env=%s)', environment)
    return True
