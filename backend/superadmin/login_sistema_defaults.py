"""Padrões visuais das telas de login Superadmin e Suporte (paths servidos pelo frontend)."""

LOGIN_SISTEMA_DEFAULTS = {
    'superadmin': {
        'logo': '/login-logos/superadmin.svg',
        'login_background': '/login-backgrounds/superadmin.jpg',
        'cor_primaria': '#9333ea',
        'cor_secundaria': '#7e22ce',
        'titulo': 'Super Admin',
        'subtitulo': 'Gestão global da plataforma LWK',
    },
    'suporte': {
        'logo': '/login-logos/suporte.svg',
        'login_background': '/login-backgrounds/suporte.jpg',
        'cor_primaria': '#2563eb',
        'cor_secundaria': '#1d4ed8',
        'titulo': 'Portal de Suporte',
        'subtitulo': 'Chamados, tickets e atendimento às lojas',
    },
}
