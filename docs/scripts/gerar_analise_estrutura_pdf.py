#!/usr/bin/env python3
"""
Gera PDF com a análise da estrutura atual do LWK Sistemas.
Uso: python3 docs/scripts/gerar_analise_estrutura_pdf.py
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib import colors
from datetime import date
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'analise-estrutura-lwk-sistemas.pdf')

# Cores do tema
DARK_BG = HexColor('#1a1f2e')
ACCENT = HexColor('#3b82f6')
GREEN = HexColor('#22c55e')
YELLOW = HexColor('#eab308')
RED = HexColor('#ef4444')
GRAY = HexColor('#6b7280')
LIGHT_BG = HexColor('#f8fafc')


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=28, leading=34, textColor=ACCENT,
        spaceAfter=10, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle', parent=styles['Normal'],
        fontSize=14, leading=18, textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', parent=styles['Heading1'],
        fontSize=16, leading=20, textColor=DARK_BG,
        spaceBefore=20, spaceAfter=10,
        borderWidth=0, borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        'SubSection', parent=styles['Heading2'],
        fontSize=13, leading=16, textColor=ACCENT,
        spaceBefore=14, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=14, textColor=black,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'CodeBlock', parent=styles['Normal'],
        fontName='Courier', fontSize=8.5, leading=11,
        textColor=HexColor('#1e293b'), backColor=LIGHT_BG,
        leftIndent=10, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'BulletItem', parent=styles['Normal'],
        fontSize=10, leading=14, leftIndent=20, bulletIndent=10,
        spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        'StatusOK', parent=styles['Normal'],
        fontSize=10, textColor=GREEN
    ))
    styles.add(ParagraphStyle(
        'StatusWarn', parent=styles['Normal'],
        fontSize=10, textColor=YELLOW
    ))
    styles.add(ParagraphStyle(
        'StatusFail', parent=styles['Normal'],
        fontSize=10, textColor=RED
    ))
    return styles


def make_status_table(data, col_widths=None):
    """Cria tabela formatada com cabeçalho azul."""
    if not col_widths:
        col_widths = [5 * cm, 10 * cm, 3 * cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEADING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def build_pdf():
    styles = build_styles()
    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title='Análise da Estrutura — LWK Sistemas',
        author='LWK Sistemas'
    )
    story = []

    # === CAPA ===
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph('LWK Sistemas', styles['CoverTitle']))
    story.append(Paragraph('Análise da Estrutura Atual', styles['CoverSubtitle']))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f'Gerado em {date.today().strftime("%d/%m/%Y")}', styles['CoverSubtitle']))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        'Documento técnico com visão completa da arquitetura,<br/>'
        'modularização, segurança e próximos passos.',
        styles['CoverSubtitle']
    ))
    story.append(PageBreak())

    # === 1. VISÃO GERAL ===
    story.append(Paragraph('1. Visão Geral da Arquitetura', styles['SectionTitle']))
    story.append(Paragraph(
        'SaaS multi-tenant com Django 5 / DRF no backend (Railway) e Next.js 14 / App Router '
        'no frontend (Vercel). PostgreSQL com schemas isolados por loja, Redis como cache e '
        'broker da fila django-q.',
        styles['Body']
    ))
    story.append(Spacer(1, 4 * mm))

    infra_data = [
        ['Serviço', 'Papel', 'Status'],
        ['lwks-backend', 'API HTTP (Gunicorn 4w × 2t) — enfileira tasks', '✅ Online'],
        ['lwks-worker', 'qcluster django-q — executa fila assíncrona', '✅ Online'],
        ['lwks-cron', 'Cron síncrono (lembretes, backups)', '✅ Online'],
        ['PostgreSQL', 'Banco principal (schemas por loja)', '✅ Online'],
        ['Redis', 'Cache + broker django-q (volume persistente)', '✅ Online'],
        ['Postgres-PITR', 'Point-In-Time Recovery (45.9 MB)', '✅ Ativo'],
        ['evolution-api', 'WhatsApp (Evolution API)', '✅ Online'],
    ]
    story.append(make_status_table(infra_data, [4 * cm, 9 * cm, 3 * cm]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph('Produção:', styles['SubSection']))
    story.append(Paragraph('• API: api.lwksistemas.com.br', styles['BulletItem']))
    story.append(Paragraph('• Frontend: lwksistemas.com.br', styles['BulletItem']))
    story.append(Paragraph('• Beta: beta.lwksistemas.com.br → branch staging', styles['BulletItem']))

    # === 2. APPS DJANGO ===
    story.append(PageBreak())
    story.append(Paragraph('2. Backend — Apps Django (17 apps)', styles['SectionTitle']))

    apps_data = [
        ['App', 'Função'],
        ['superadmin', 'Painel central: lojas, billing, backups, NFS-e, segurança, MFA'],
        ['tenants', 'Middleware multi-tenant, resolução de slug/schema'],
        ['core', 'Mixins (LojaIsolation), task_queue, encryption, throttling'],
        ['suporte', 'Chamados/tickets (schema isolado "suporte")'],
        ['clinica_beleza', 'Clínica da beleza (integração Memed prescrição digital)'],
        ['clinica_estetica', 'Clínica estética'],
        ['cabeleireiro', 'Salão/barbearia'],
        ['hotel', 'Hotel/pousada'],
        ['restaurante', 'Restaurante'],
        ['crm_vendas', 'CRM Vendas (leads, pipeline, Google Calendar)'],
        ['ecommerce', 'E-commerce'],
        ['asaas_integration', 'Gateway Asaas (cobranças, webhooks, NFS-e)'],
        ['nfse_integration', 'NFS-e (ISSNet, API Nacional)'],
        ['whatsapp', 'WhatsApp Cloud API + Evolution API'],
        ['notificacoes / push', 'Notificações in-app + push VAPID'],
        ['rules', 'Motor de regras automáticas'],
        ['homepage', 'Homepage configurável por loja'],
    ]
    story.append(make_status_table(apps_data, [4 * cm, 13 * cm]))

    # === 3. MODULARIZAÇÃO ===
    story.append(PageBreak())
    story.append(Paragraph('3. Modularização (Fase 4 — Concluída)', styles['SectionTitle']))
    story.append(Paragraph(
        'Monolitos do backend foram divididos em pacotes modulares com imports preservados:',
        styles['Body']
    ))

    mod_data = [
        ['Módulo Original', 'Pacote Atual', 'Arquivos'],
        ['superadmin/models.py', 'superadmin/models/', '14 módulos'],
        ['financeiro_views.py', 'superadmin/financeiro_views/', '7 módulos'],
        ['sync_service.py', 'superadmin/sync_service/', '3 (Asaas, MP, NFS-e)'],
        ['backup_service.py', 'superadmin/backup_service/', '5 módulos'],
        ['serializers.py', 'superadmin/serializers/', '7 módulos'],
        ['signals.py', 'superadmin/signals/', '6 módulos'],
        ['views/loja.py', 'superadmin/views/loja/', 'subpacote'],
        ['services (novo)', 'superadmin/services/', '12 services'],
    ]
    story.append(make_status_table(mod_data, [4.5 * cm, 5.5 * cm, 4 * cm]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph('Frontend:', styles['SubSection']))
    story.append(Paragraph('• ModalsAll.tsx (83 KB) → 11 modais lazy em restaurante/modals/', styles['BulletItem']))
    story.append(Paragraph('• CalendarioAgendamentos.tsx (1702 linhas) → 6 módulos', styles['BulletItem']))
    story.append(Paragraph('• Hooks DRY: useLojaInfoPublica, LojaBackupStandardContent, useCrmDocumentoActions', styles['BulletItem']))

    # === 4. MULTI-TENANT ===
    story.append(PageBreak())
    story.append(Paragraph('4. Sistema Multi-Tenant — 3 Camadas', styles['SectionTitle']))

    story.append(Paragraph('<b>Camada 1 — Middleware (TenantMiddleware)</b>', styles['Body']))
    story.append(Paragraph('Detecta loja via header X-Tenant-Slug / X-Loja-ID, configura thread-local.', styles['BulletItem']))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph('<b>Camada 2 — DB Router (MultiTenantRouter)</b>', styles['Body']))
    story.append(Paragraph('Roteia queries para schema correto: public, suporte, ou loja_&lt;slug&gt;.', styles['BulletItem']))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph('<b>Camada 3 — Manager (LojaIsolationManager)</b>', styles['Body']))
    story.append(Paragraph(
        'Filtra automaticamente por loja_id em todas as queries — defesa em profundidade '
        'mesmo com schemas isolados.',
        styles['BulletItem']
    ))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph('Apps isolados por tenant:', styles['SubSection']))
    tenant_apps = (
        'cabeleireiro, clinica_beleza, clinica_estetica, crm_vendas, ecommerce, '
        'hotel, nfse_integration, products, restaurante, servicos, stores, whatsapp'
    )
    story.append(Paragraph(tenant_apps, styles['CodeBlock']))

    # === 5. FILA ASSÍNCRONA ===
    story.append(Paragraph('5. Fila Assíncrona (django-q + Redis)', styles['SectionTitle']))

    queue_data = [
        ['Configuração', 'Valor'],
        ['Broker', 'Redis (produção) / ORM (dev)'],
        ['Workers', '4 (configurável via DJANGO_Q_WORKERS)'],
        ['Timeout', '300s por task'],
        ['Max attempts', '3 (retry em 360s)'],
        ['Queue limit', '500'],
        ['Health: degraded', '≥ 50 tasks acumuladas'],
        ['Health: unhealthy', '≥ 200 tasks acumuladas'],
    ]
    story.append(make_status_table(queue_data, [5 * cm, 11 * cm]))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph('Tasks enfileiradas:', styles['SubSection']))
    story.append(Paragraph('• WhatsApp (lembretes, notificações)', styles['BulletItem']))
    story.append(Paragraph('• E-mail via Resend', styles['BulletItem']))
    story.append(Paragraph('• NFS-e (emissão fiscal)', styles['BulletItem']))
    story.append(Paragraph('• Webhooks Asaas (global + loja CRM)', styles['BulletItem']))
    story.append(Paragraph('• Mercado Pago', styles['BulletItem']))
    story.append(Paragraph('• PDF proposta/contrato (geração + envio — HTTP 202)', styles['BulletItem']))

    # === 6. SEGURANÇA ===
    story.append(PageBreak())
    story.append(Paragraph('6. Segurança Implementada', styles['SectionTitle']))

    sec_data = [
        ['Mecanismo', 'Detalhe'],
        ['JWT', 'Access 30min + Refresh 2h + blacklist + rotação'],
        ['MFA', 'TOTP para superadmin (com backup codes criptografados)'],
        ['Throttling', '100/h anon, 10000/h user, rates específicos (login, reset)'],
        ['CORS', 'Origins explícitos, nunca allow_all, preflight cache 24h'],
        ['SecurityIsolationMiddleware', 'Validação tenant JWT → loja permitida → contexto'],
        ['Criptografia', 'FIELD_ENCRYPTION_KEY para campos sensíveis (TOTP, ISSNet)'],
        ['HistóricoAcesso', 'Middleware registra todos os acessos'],
        ['Senha provisória', 'Troca obrigatória no primeiro login (profissionais)'],
        ['CI Security', 'Bandit (análise estática) via GitHub Actions'],
        ['Session control', 'X-Session-Id para bloqueio de sessão simultânea'],
    ]
    story.append(make_status_table(sec_data, [5 * cm, 11.5 * cm]))

    # === 7. DEPLOY ===
    story.append(Paragraph('7. Deploy e Release', styles['SectionTitle']))
    story.append(Paragraph('<b>releaseCommand (ordem correta):</b>', styles['Body']))
    story.append(Paragraph(
        'migrate → migrate suporte → migrate_all_lojas → ensure_all → setup_initial_data → collectstatic',
        styles['CodeBlock']
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        'Dockerfile unificado com LWK_PROCESS_ROLE (web/worker/cron) — mesma imagem, '
        'processos diferentes. BUILD_ID para invalidar cache de camada.',
        styles['Body']
    ))

    # === 8. HEALTH CHECK ===
    story.append(Paragraph('8. Health Check', styles['SectionTitle']))
    story.append(Paragraph(
        'Endpoint público GET /api/superadmin/health/ verifica:',
        styles['Body']
    ))
    story.append(Paragraph('• Conectividade banco (SELECT 1) + contagem de lojas', styles['BulletItem']))
    story.append(Paragraph('• Migrations pendentes críticas', styles['BulletItem']))
    story.append(Paragraph('• Redis/Cache status', styles['BulletItem']))
    story.append(Paragraph('• Fila: tasks enfileiradas, workers vivos, falhas 24h', styles['BulletItem']))
    story.append(Paragraph('• Evolution API (WhatsApp) disponível', styles['BulletItem']))
    story.append(Paragraph('• Email provider + Build version', styles['BulletItem']))

    # === 9. FRONTEND ===
    story.append(PageBreak())
    story.append(Paragraph('9. Frontend — Next.js 14', styles['SectionTitle']))

    fe_data = [
        ['Pasta', 'Conteúdo'],
        ['app/', 'Pages (App Router) — rotas dinâmicas por tipo de loja'],
        ['components/', 'UI compartilhados (Shadcn/Tailwind)'],
        ['hooks/', 'Custom hooks (useLojaInfoPublica, useCrmDocumentoActions, etc.)'],
        ['services/', 'Camada de API (fetch + auth headers)'],
        ['store/', 'State management'],
        ['contexts/', 'React Contexts (auth, theme, loja)'],
        ['types/', 'TypeScript types'],
        ['middleware.ts', 'Auth + routing middleware'],
    ]
    story.append(make_status_table(fe_data, [4 * cm, 12.5 * cm]))

    # === 10. CONFORMIDADE COM RECOMENDAÇÕES ===
    story.append(Paragraph('10. Conformidade com Recomendações de Arquitetura', styles['SectionTitle']))

    conf_data = [
        ['Recomendação', 'Status'],
        ['PostgreSQL schemas por loja', '✅ Implementado (3 camadas)'],
        ['Next.js + Django desacoplados', '✅ Vercel + Railway'],
        ['Worker assíncrono', '✅ django-q + Redis (4 workers)'],
        ['Staging separado', '✅ beta.lwksistemas.com.br'],
        ['migrate_all_lojas principal / ensure_all fallback', '✅ Implementado'],
        ['Workers para WhatsApp, Resend, NFS-e, Asaas, MP, PDFs', '✅ Todos enfileirados'],
        ['Refatoração de monolitos', '✅ Concluída (Fase 4)'],
        ['Observabilidade (Sentry, OTEL, Prometheus)', '❌ Não implementado'],
        ['Feature flags por loja', '❌ Não implementado'],
        ['Auditoria centralizada (audit_logs)', '⚠️ Parcial (model existe)'],
        ['Versionamento API (/api/v1)', '❌ Sem prefixo de versão'],
        ['Testes automatizados', '⚠️ Parcial (6 test files)'],
        ['Documentação OpenAPI', '⚠️ drf-spectacular configurado'],
    ]
    story.append(make_status_table(conf_data, [9 * cm, 7.5 * cm]))

    # === 11. PRÓXIMOS PASSOS ===
    story.append(PageBreak())
    story.append(Paragraph('11. Próximos Passos Prioritários', styles['SectionTitle']))

    next_data = [
        ['#', 'Item', 'Esforço', 'Impacto'],
        ['1', 'Sentry + OpenTelemetry', 'Médio', 'Alto'],
        ['2', 'Feature flags por loja', 'Médio', 'Alto'],
        ['3', 'Audit_logs cobertura completa', 'Baixo-Médio', 'Alto'],
        ['4', 'Versionamento API (v1)', 'Baixo', 'Médio'],
        ['5', 'Testes automatizados (coverage)', 'Alto', 'Alto'],
        ['6', 'Documentação OpenAPI completa', 'Médio', 'Médio'],
    ]
    story.append(make_status_table(next_data, [1 * cm, 7 * cm, 3.5 * cm, 3.5 * cm]))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph(
        '<i>Nota: A arquitetura recebeu avaliação 9,7/10. O foco deve ser em melhorias '
        'incrementais (observabilidade, testes, auditoria) sem mudanças estruturais.</i>',
        styles['Body']
    ))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        f'Documento gerado automaticamente em {date.today().strftime("%d/%m/%Y")}.<br/>'
        'Fonte: código-fonte do repositório LWK Sistemas (branch main).',
        styles['Body']
    ))

    doc.build(story)
    print(f'✅ PDF gerado: {OUTPUT_PATH}')


if __name__ == '__main__':
    build_pdf()
